"""Config flow for DWD Weather AI."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import callback

from .const import (
    CONF_SCAN_INTERVAL_MINUTES,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    MAX_SCAN_INTERVAL_MINUTES,
    MIN_SCAN_INTERVAL_MINUTES,
)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_LATITUDE): vol.Coerce(float),
        vol.Required(CONF_LONGITUDE): vol.Coerce(float),
        vol.Optional(
            CONF_SCAN_INTERVAL_MINUTES,
            default=DEFAULT_SCAN_INTERVAL_MINUTES,
        ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL_MINUTES, max=MAX_SCAN_INTERVAL_MINUTES)),
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_SCAN_INTERVAL_MINUTES,
            default=DEFAULT_SCAN_INTERVAL_MINUTES,
        ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL_MINUTES, max=MAX_SCAN_INTERVAL_MINUTES)),
    }
)


class DwdWeatherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DWD Weather AI."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            unique_id = f"{user_input[CONF_LATITUDE]:.4f},{user_input[CONF_LONGITUDE]:.4f}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow."""
        return DwdWeatherOptionsFlow(config_entry)


class DwdWeatherOptionsFlow(config_entries.OptionsFlow):
    """Handle options for DWD Weather AI."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL_MINUTES,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL_MINUTES,
                            self.config_entry.data.get(
                                CONF_SCAN_INTERVAL_MINUTES,
                                DEFAULT_SCAN_INTERVAL_MINUTES,
                            ),
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL_MINUTES, max=MAX_SCAN_INTERVAL_MINUTES),
                    )
                }
            ),
        )
