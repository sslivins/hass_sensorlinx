"""Platform for binary sensor integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SensorLinxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="permanent_heat_demand",
        name="Permanent Heat Demand",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    BinarySensorEntityDescription(
        key="permanent_cool_demand", 
        name="Permanent Cool Demand",
        device_class=BinarySensorDeviceClass.COLD,
    ),
    BinarySensorEntityDescription(
        key="warm_weather_shutdown",
        name="Warm Weather Shutdown",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="cold_weather_shutdown",
        name="Cold Weather Shutdown", 
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    coordinator: SensorLinxDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    _LOGGER.debug("Setting up binary sensor platform")
    _LOGGER.debug("Coordinator data: %s", coordinator.data)
    
    if coordinator.data and "devices" in coordinator.data:
        devices = coordinator.data["devices"]
        _LOGGER.debug("Found %d devices in coordinator data", len(devices))
        
        for device_id, device in devices.items():
            _LOGGER.debug("Processing device %s: %s", device_id, device)
            device_parameters = device.get("parameters", {})
            _LOGGER.debug("Device %s parameters: %s", device_id, device_parameters)
            
            for description in BINARY_SENSOR_DESCRIPTIONS:
                if description.key in device_parameters:
                    _LOGGER.debug("Creating binary sensor %s for device %s", description.key, device_id)
                    entities.append(
                        SensorLinxBinarySensor(
                            coordinator,
                            description,
                            device_id,
                            device,
                        )
                    )
                else:
                    _LOGGER.debug("Device %s does not have parameter %s", device_id, description.key)
    else:
        _LOGGER.debug("No coordinator data or devices found")
    
    _LOGGER.debug("Adding %d binary sensor entities", len(entities))
    async_add_entities(entities)


class SensorLinxBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Implementation of a SensorLinx binary sensor."""

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        description: BinarySensorEntityDescription,
        device_id: str,
        device: dict[str, Any],
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._device_id = device_id
        self._device = device
        
        self._attr_unique_id = f"{device_id}_{description.key}"
        self._attr_name = f"{device.get('name', device_id)} {description.name}"
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
            
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
            
        parameters = device.get("parameters", {})
        value = parameters.get(self.entity_description.key)
        
        if value is None:
            return None
        
        # Handle different parameter types
        if self.entity_description.key in ["permanent_heat_demand", "permanent_cool_demand"]:
            # These are boolean values from the API
            return bool(value)
        elif self.entity_description.key in ["warm_weather_shutdown", "cold_weather_shutdown"]:
            # These are temperature values - consider "on" if not disabled (32°F means disabled)
            return value != 32 if isinstance(value, (int, float)) else False
        
        # Default handling
        if isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return value > 0
        elif isinstance(value, str):
            return value.lower() in ("true", "on", "1", "yes", "active")
        
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        )
