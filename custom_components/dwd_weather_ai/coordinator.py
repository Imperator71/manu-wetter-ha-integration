"""Data coordinator for DWD Weather AI."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
import logging
from statistics import mean
from typing import Any

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import BrightSkyClient
from .const import DOMAIN, FORECAST_DAYS, HISTORY_DAYS

_LOGGER = logging.getLogger(__name__)

CONDITION_MAP = {
    "clear": "sunny",
    "dry": "sunny",
    "partly_cloudy": "partlycloudy",
    "cloudy": "cloudy",
    "fog": "fog",
    "rain": "rainy",
    "sleet": "snowy-rainy",
    "snow": "snowy",
    "hail": "hail",
    "thunderstorm": "lightning-rainy",
}


class DwdWeatherCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for weather data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: BrightSkyClient,
        config_entry: ConfigEntry,
        scan_interval_minutes: int,
    ) -> None:
        self.client = client
        self.config_entry = config_entry
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval_minutes),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and normalize weather payloads."""
        try:
            raw = await self.client.async_fetch_all(HISTORY_DAYS, FORECAST_DAYS)
        except (ClientError, TimeoutError, ValueError) as err:
            raise UpdateFailed(f"Error communicating with Bright Sky API: {err}") from err

        return _normalize_payload(raw)


def _parse_datetime(value: str) -> datetime:
    """Parse timestamp into local-aware datetime."""
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=dt_util.UTC)
    return dt.astimezone(dt_util.DEFAULT_TIME_ZONE)


def _map_condition(condition: str | None, icon: str | None) -> str | None:
    """Map Bright Sky condition/icon to HA condition."""
    if condition in CONDITION_MAP:
        return CONDITION_MAP[condition]

    if icon:
        if "rain" in icon:
            return "rainy"
        if "snow" in icon:
            return "snowy"
        if "cloud" in icon:
            return "cloudy"
        if "fog" in icon:
            return "fog"

    return None


def _normalize_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert API data to structures used by entities."""
    weather_rows = raw.get("timeline", {}).get("weather", [])
    current_row = raw.get("current", {}).get("weather", {})
    sources = raw.get("current", {}).get("sources", [])

    now_local = dt_util.now()
    history_precip: dict[str, float] = defaultdict(float)
    hourly_forecast: list[dict[str, Any]] = []
    daily_bucket: dict[str, dict[str, Any]] = {}

    for row in weather_rows:
        timestamp = row.get("timestamp")
        if not timestamp:
            continue

        dt_local = _parse_datetime(timestamp)
        day_key = dt_local.date().isoformat()
        precipitation = float(row.get("precipitation", 0.0) or 0.0)

        if dt_local.date() < now_local.date():
            history_precip[day_key] += precipitation

        if dt_local >= now_local:
            hourly_forecast.append(
                {
                    "datetime": dt_local.isoformat(),
                    "temperature": row.get("temperature"),
                    "templow": None,
                    "condition": _map_condition(row.get("condition"), row.get("icon")),
                    "precipitation": row.get("precipitation"),
                    "precipitation_probability": row.get("precipitation_probability"),
                    "wind_speed": row.get("wind_speed"),
                }
            )

        bucket = daily_bucket.setdefault(
            day_key,
            {
                "temperatures": [],
                "precipitation": 0.0,
                "precip_probability": [],
                "wind": [],
                "condition": None,
            },
        )

        temp = row.get("temperature")
        if temp is not None:
            bucket["temperatures"].append(float(temp))

        bucket["precipitation"] += precipitation

        precip_probability = row.get("precipitation_probability")
        if precip_probability is not None:
            bucket["precip_probability"].append(float(precip_probability))

        wind = row.get("wind_speed")
        if wind is not None:
            bucket["wind"].append(float(wind))

        if bucket["condition"] is None:
            bucket["condition"] = _map_condition(row.get("condition"), row.get("icon"))

    daily_forecast: list[dict[str, Any]] = []
    for day, bucket in sorted(daily_bucket.items()):
        dt_day = datetime.fromisoformat(day)
        if dt_day.date() < now_local.date() or dt_day.date() > (now_local + timedelta(days=FORECAST_DAYS)).date():
            continue

        temps = bucket["temperatures"]
        if not temps:
            continue

        daily_forecast.append(
            {
                "datetime": day,
                "temperature": max(temps),
                "templow": min(temps),
                "condition": bucket["condition"],
                "precipitation": round(bucket["precipitation"], 2),
                "precipitation_probability": round(max(bucket["precip_probability"], default=0.0), 1),
                "wind_speed": round(mean(bucket["wind"]) if bucket["wind"] else 0.0, 1),
            }
        )

    history_days_sorted = sorted(history_precip.items(), key=lambda item: item[0], reverse=True)
    today = now_local.date().isoformat()

    return {
        "current": {
            "temperature": current_row.get("temperature"),
            "pressure": current_row.get("pressure_msl"),
            "humidity": current_row.get("relative_humidity"),
            "wind_speed": current_row.get("wind_speed"),
            "wind_bearing": current_row.get("wind_direction"),
            "visibility": current_row.get("visibility"),
            "condition": _map_condition(current_row.get("condition"), current_row.get("icon")),
            "cloud_coverage": current_row.get("cloud_cover"),
            "precipitation": current_row.get("precipitation_10"),
            "timestamp": current_row.get("timestamp"),
        },
        "hourly_forecast": hourly_forecast[:72],
        "daily_forecast": daily_forecast,
        "history_daily_precip": history_days_sorted,
        "sources": sources,
        "today": today,
    }
