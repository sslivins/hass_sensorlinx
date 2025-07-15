"""Config flow for SensorLinx integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from pysensorlinx import Sensorlinx

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, ERROR_AUTH_FAILED, ERROR_CANNOT_CONNECT, ERROR_UNKNOWN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SensorLinx."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = ERROR_CANNOT_CONNECT
        except InvalidAuth:
            errors["base"] = ERROR_AUTH_FAILED
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = ERROR_UNKNOWN
        else:
            await self.async_set_unique_id(info["title"])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


async def validate_input(hass, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    sensorlinx = Sensorlinx()
    
    try:
        # Test authentication
        await sensorlinx.login(data[CONF_USERNAME], data[CONF_PASSWORD])
        
        # Get user profile to confirm connection
        profile = await sensorlinx.get_profile()
        
        if not profile:
            raise InvalidAuth
            
        # Return info that you want to store in the config entry.
        return {"title": f"SensorLinx ({data[CONF_USERNAME]})"}
        
    except Exception as exc:
        _LOGGER.error("Failed to connect to SensorLinx: %s", exc)
        raise CannotConnect from exc
    finally:
        await sensorlinx.close()
