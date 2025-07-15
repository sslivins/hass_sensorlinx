"""Platform for sensor integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SensorLinxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    # Temperature sensors - these will be dynamically created based on available temperature sensors
    SensorEntityDescription(
        key="temperature_hot_tank",
        name="Hot Tank Temperature",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="temperature_cold_tank", 
        name="Cold Tank Temperature",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="temperature_outdoor",
        name="Outdoor Temperature", 
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="target_temperature_hot_tank",
        name="Hot Tank Target Temperature",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="target_temperature_cold_tank",
        name="Cold Tank Target Temperature", 
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="hot_tank_min_temp",
        name="Hot Tank Minimum Temperature",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="hot_tank_max_temp", 
        name="Hot Tank Maximum Temperature",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="cold_tank_min_temp",
        name="Cold Tank Minimum Temperature",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="cold_tank_max_temp",
        name="Cold Tank Maximum Temperature", 
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="firmware_version",
        name="Firmware Version",
        device_class=SensorDeviceClass.ENUM,
    ),
    SensorEntityDescription(
        key="device_type",
        name="Device Type",
        device_class=SensorDeviceClass.ENUM,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: SensorLinxDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    _LOGGER.debug("Setting up sensor platform")
    _LOGGER.debug("Coordinator data: %s", coordinator.data)
    
    if coordinator.data and "devices" in coordinator.data:
        devices = coordinator.data["devices"]
        _LOGGER.debug("Found %d devices in coordinator data", len(devices))
        
        for device_id, device in devices.items():
            _LOGGER.debug("Processing device %s: %s", device_id, device)
            device_parameters = device.get("parameters", {})
            _LOGGER.debug("Device %s parameters: %s", device_id, device_parameters)
            
            for description in SENSOR_DESCRIPTIONS:
                if description.key in device_parameters:
                    _LOGGER.debug("Creating sensor %s for device %s", description.key, device_id)
                    entities.append(
                        SensorLinxSensor(
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
    
    _LOGGER.debug("Adding %d sensor entities", len(entities))
    async_add_entities(entities)


class SensorLinxSensor(CoordinatorEntity, SensorEntity):
    """Implementation of a SensorLinx sensor."""

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        description: SensorEntityDescription,
        device_id: str,
        device: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
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
    def native_value(self) -> str | int | float | None:
        """Return the native value of the sensor."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
            
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
            
        parameters = device.get("parameters", {})
        return parameters.get(self.entity_description.key)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        )
