"""DWD Weather AI integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BrightSkyClient
from .const import (
    CONF_SCAN_INTERVAL_MINUTES,
    COORDINATOR_TIMEOUT_SECONDS,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import DwdWeatherCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DWD Weather AI from a config entry."""
    scan_minutes = entry.options.get(CONF_SCAN_INTERVAL_MINUTES)
    if scan_minutes is None:
        scan_minutes = entry.data.get(
            CONF_SCAN_INTERVAL_MINUTES,
            DEFAULT_SCAN_INTERVAL_MINUTES,
        )

    client = BrightSkyClient(
        session=async_get_clientsession(hass),
        latitude=entry.data["latitude"],
        longitude=entry.data["longitude"],
        timeout=COORDINATOR_TIMEOUT_SECONDS,
    )

    coordinator = DwdWeatherCoordinator(
        hass=hass,
        client=client,
        config_entry=entry,
        scan_interval_minutes=scan_minutes,
    )

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry.runtime_data = None
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
