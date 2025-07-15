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
    SensorEntityDescription(
        key="temperature",
        name="Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="humidity",
        name="Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="pressure",
        name="Pressure",
        native_unit_of_measurement=UnitOfPressure.HPA,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="energy",
        name="Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="power",
        name="Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
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
    
    if coordinator.data and "devices" in coordinator.data:
        for device_id, device in coordinator.data["devices"].items():
            for description in SENSOR_DESCRIPTIONS:
                if description.key in device.get("parameters", {}):
                    entities.append(
                        SensorLinxSensor(
                            coordinator,
                            description,
                            device_id,
                            device,
                        )
                    )
    
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
