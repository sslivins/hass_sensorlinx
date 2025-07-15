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
        key="online",
        name="Online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    BinarySensorEntityDescription(
        key="alarm",
        name="Alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="maintenance",
        name="Maintenance Mode",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="heating",
        name="Heating",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    BinarySensorEntityDescription(
        key="cooling",
        name="Cooling",
        device_class=BinarySensorDeviceClass.COLD,
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
    
    if coordinator.data and "devices" in coordinator.data:
        for device_id, device in coordinator.data["devices"].items():
            for description in BINARY_SENSOR_DESCRIPTIONS:
                if description.key in device.get("parameters", {}):
                    entities.append(
                        SensorLinxBinarySensor(
                            coordinator,
                            description,
                            device_id,
                            device,
                        )
                    )
    
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
            "model": device.get("type", "Unknown"),
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
