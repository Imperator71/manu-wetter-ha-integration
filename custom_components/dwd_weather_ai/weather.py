"""Weather platform for DWD Weather AI."""

from __future__ import annotations

from typing import Any

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME
from .coordinator import DwdWeatherCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up weather entity from config entry."""
    coordinator: DwdWeatherCoordinator = entry.runtime_data
    async_add_entities([DwdWeatherEntity(coordinator, entry)])


class DwdWeatherEntity(CoordinatorEntity[DwdWeatherCoordinator], WeatherEntity):
    """Representation of DWD weather data."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_visibility_unit = UnitOfLength.KILOMETERS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_attribution = "Weather data provided by Bright Sky (DWD and partner stations)"

    def __init__(self, coordinator: DwdWeatherCoordinator, entry: ConfigEntry) -> None:
        """Initialize weather entity."""
        super().__init__(coordinator)
        name = entry.data.get("name", DEFAULT_NAME)
        self._attr_unique_id = f"{entry.entry_id}_weather"
        self._attr_translation_key = "weather"
        self._attr_device_info = {
            "identifiers": {(entry.domain, entry.entry_id)},
            "name": name,
            "manufacturer": "Bright Sky / DWD",
            "model": "Area Weather",
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def condition(self) -> str | None:
        return self.coordinator.data["current"].get("condition")

    @property
    def native_temperature(self) -> float | None:
        return self.coordinator.data["current"].get("temperature")

    @property
    def humidity(self) -> int | None:
        humidity = self.coordinator.data["current"].get("humidity")
        return int(humidity) if humidity is not None else None

    @property
    def native_pressure(self) -> float | None:
        return self.coordinator.data["current"].get("pressure")

    @property
    def native_wind_speed(self) -> float | None:
        return self.coordinator.data["current"].get("wind_speed")

    @property
    def wind_bearing(self) -> int | None:
        bearing = self.coordinator.data["current"].get("wind_bearing")
        return int(bearing) if bearing is not None else None

    @property
    def native_visibility(self) -> float | None:
        visibility_m = self.coordinator.data["current"].get("visibility")
        if visibility_m is None:
            return None
        return round(float(visibility_m) / 1000, 1)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose extra weather attributes useful for AI conversations."""
        history = self.coordinator.data.get("history_daily_precip", [])
        return {
            "cloud_coverage": self.coordinator.data["current"].get("cloud_coverage"),
            "current_precipitation_10min": self.coordinator.data["current"].get("precipitation"),
            "data_sources": [source.get("dwd_station_id") for source in self.coordinator.data.get("sources", [])],
            "historical_daily_precip_mm": {day: round(amount, 2) for day, amount in history},
        }

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return daily forecast."""
        return self.coordinator.data.get("daily_forecast")

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return hourly forecast."""
        return self.coordinator.data.get("hourly_forecast")
