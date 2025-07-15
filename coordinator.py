"""DataUpdateCoordinator for SensorLinx."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from pysensorlinx import Sensorlinx

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SensorLinxDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the SensorLinx API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.sensorlinx = Sensorlinx()
        self.entry = entry
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            # Login
            await self.sensorlinx.login(
                self.entry.data[CONF_USERNAME],
                self.entry.data[CONF_PASSWORD]
            )
            
            # Get user profile
            profile = await self.sensorlinx.get_user_profile()
            if not profile:
                raise ConfigEntryAuthFailed("Failed to get user profile")
            
            # Get buildings
            buildings = await self.sensorlinx.get_buildings()
            if not buildings:
                buildings = []
            
            # Get devices for each building
            devices = {}
            for building in buildings:
                try:
                    building_devices = await self.sensorlinx.get_devices(building.get("id"))
                    if building_devices:
                        for device in building_devices:
                            try:
                                # Get device parameters
                                device_params = await self.sensorlinx.get_device_parameters(device.get("id"))
                                if device_params:
                                    device["parameters"] = device_params
                                devices[device.get("id")] = device
                            except Exception as device_exc:
                                _LOGGER.warning("Failed to get parameters for device %s: %s", device.get("id"), device_exc)
                                # Still add device without parameters
                                device["parameters"] = {}
                                devices[device.get("id")] = device
                except Exception as building_exc:
                    _LOGGER.warning("Failed to get devices for building %s: %s", building.get("id"), building_exc)
            
            return {
                "profile": profile,
                "buildings": buildings,
                "devices": devices,
            }
            
        except ConfigEntryAuthFailed:
            raise
        except Exception as exc:
            _LOGGER.error("Error communicating with SensorLinx API: %s", exc)
            raise UpdateFailed(f"Error communicating with API: {exc}") from exc

    async def async_shutdown(self) -> None:
        """Close the SensorLinx connection."""
        if self.sensorlinx:
            await self.sensorlinx.close()
