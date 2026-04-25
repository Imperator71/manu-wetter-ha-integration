"""Sensor platform for DWD Weather AI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPrecipitationDepth
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .coordinator import DwdWeatherCoordinator


@dataclass(frozen=True, kw_only=True)
class DwdSensorDescription(SensorEntityDescription):
    """DWD sensor description."""

    value_fn: Callable[[dict], float | str | None]


SENSORS: tuple[DwdSensorDescription, ...] = (
    DwdSensorDescription(
        key="rain_yesterday",
        translation_key="rain_yesterday",
        name="Rain Yesterday",
        device_class=SensorDeviceClass.PRECIPITATION,
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        value_fn=lambda data: _rain_for_days_ago(data, 1),
    ),
    DwdSensorDescription(
        key="rain_2_days_ago",
        translation_key="rain_2_days_ago",
        name="Rain 2 Days Ago",
        device_class=SensorDeviceClass.PRECIPITATION,
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        value_fn=lambda data: _rain_for_days_ago(data, 2),
    ),
    DwdSensorDescription(
        key="rain_next_day",
        translation_key="rain_next_day",
        name="Expected Rain Tomorrow",
        device_class=SensorDeviceClass.PRECIPITATION,
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        value_fn=lambda data: _forecast_rain_for_days_ahead(data, 1),
    ),
    DwdSensorDescription(
        key="rain_next_7_days",
        translation_key="rain_next_7_days",
        name="Expected Rain Next 7 Days",
        device_class=SensorDeviceClass.PRECIPITATION,
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        value_fn=lambda data: _forecast_rain_next_days(data, 7),
    ),
    DwdSensorDescription(
        key="weather_trend_7_days",
        translation_key="weather_trend_7_days",
        name="Weather Trend Next 7 Days",
        icon="mdi:chart-line",
        value_fn=lambda data: _trend_text(data),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities from config entry."""
    coordinator: DwdWeatherCoordinator = entry.runtime_data
    async_add_entities([DwdRainSensor(coordinator, entry, description) for description in SENSORS])


class DwdRainSensor(CoordinatorEntity[DwdWeatherCoordinator], SensorEntity):
    """Representation of weather insight sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: DwdWeatherCoordinator,
        entry: ConfigEntry,
        description: DwdSensorDescription,
    ) -> None:
        """Initialize sensor entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(entry.domain, entry.entry_id)},
            "name": entry.data.get("name", "DWD Weather"),
            "manufacturer": "Bright Sky / DWD",
            "model": "Area Weather",
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def native_value(self):
        value = self.entity_description.value_fn(self.coordinator.data)
        if isinstance(value, float):
            return round(value, 2)
        return value

    @property
    def extra_state_attributes(self) -> dict:
        history = self.coordinator.data.get("history_daily_precip", [])
        return {
            "history_daily_precip_mm": {day: round(amount, 2) for day, amount in history},
            "daily_forecast": self.coordinator.data.get("daily_forecast", []),
            "last_update": dt_util.now().isoformat(),
        }


def _rain_for_days_ago(data: dict, days_ago: int) -> float | None:
    target = (dt_util.now().date() - timedelta(days=days_ago)).isoformat()
    for day, amount in data.get("history_daily_precip", []):
        if day == target:
            return float(amount)
    return None


def _forecast_rain_for_days_ahead(data: dict, days_ahead: int) -> float | None:
    target = (dt_util.now().date() + timedelta(days=days_ahead)).isoformat()
    for row in data.get("daily_forecast", []):
        if row.get("datetime") == target:
            return float(row.get("precipitation", 0.0) or 0.0)
    return None


def _forecast_rain_next_days(data: dict, days: int) -> float:
    today = dt_util.now().date()
    end = today + timedelta(days=days)
    total = 0.0

    for row in data.get("daily_forecast", []):
        value = row.get("datetime")
        if not value:
            continue
        date_value = dt_util.parse_date(value)
        if date_value is None:
            continue
        if today < date_value <= end:
            total += float(row.get("precipitation", 0.0) or 0.0)

    return total


def _trend_text(data: dict) -> str:
    """Very simple weather trend text for AI-friendly summaries."""
    today = dt_util.now().date()
    next_week = today + timedelta(days=7)
    entries = [
        row
        for row in data.get("daily_forecast", [])
        if (d := dt_util.parse_date(row.get("datetime", ""))) and today < d <= next_week
    ]

    if not entries:
        return "no_forecast_data"

    first_half = entries[: len(entries) // 2 or 1]
    second_half = entries[len(entries) // 2 or 1 :]

    first_avg = sum(row.get("temperature", 0) for row in first_half) / max(len(first_half), 1)
    second_avg = sum(row.get("temperature", 0) for row in second_half) / max(len(second_half), 1)
    rain_total = sum(float(row.get("precipitation", 0) or 0) for row in entries)

    if second_avg - first_avg >= 1.5 and rain_total < 15:
        return "improving"
    if first_avg - second_avg >= 1.5 or rain_total > 35:
        return "deteriorating"
    return "stable"
