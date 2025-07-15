"""Platform for switch integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SensorLinxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SWITCH_DESCRIPTIONS: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key="permanent_heat_demand",
        name="Permanent Heat Demand",
        icon="mdi:fire",
    ),
    SwitchEntityDescription(
        key="permanent_cool_demand", 
        name="Permanent Cool Demand",
        icon="mdi:snowflake",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    coordinator: SensorLinxDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    _LOGGER.debug("Setting up switch platform")
    _LOGGER.debug("Coordinator data: %s", coordinator.data)
    
    if coordinator.data and "devices" in coordinator.data:
        devices = coordinator.data["devices"]
        _LOGGER.debug("Found %d devices in coordinator data", len(devices))
        
        for device_id, device in devices.items():
            _LOGGER.debug("Processing device %s: %s", device_id, device)
            device_parameters = device.get("parameters", {})
            _LOGGER.debug("Device %s parameters: %s", device_id, device_parameters)
            
            for description in SWITCH_DESCRIPTIONS:
                # Always create switches for these controls, even if not currently in parameters
                _LOGGER.debug("Creating switch %s for device %s", description.key, device_id)
                entities.append(
                    SensorLinxSwitch(
                        coordinator,
                        description,
                        device_id,
                        device,
                    )
                )
    else:
        _LOGGER.debug("No coordinator data or devices found")
    
    _LOGGER.debug("Adding %d switch entities", len(entities))
    async_add_entities(entities)


class SensorLinxSwitch(CoordinatorEntity, SwitchEntity):
    """Implementation of a SensorLinx switch."""

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        description: SwitchEntityDescription,
        device_id: str,
        device: dict[str, Any],
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.entity_description = description
        self._device_id = device_id
        self._device = device
        
        self._attr_unique_id = f"{device_id}_{description.key}"
        self._attr_name = f"{device.get('name', device_id)} {description.name}"
        
        # Device info - use extracted parameters from coordinator
        parameters = device.get("parameters", {})
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": parameters.get("device_type", device.get("deviceType", "Unknown")),
            "sw_version": parameters.get("firmware_version", device.get("firmware_version")),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
            
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
            
        parameters = device.get("parameters", {})
        value = parameters.get(self.entity_description.key)
        
        if value is None:
            return False  # Default to off if no value
        
        # These are boolean values from the API
        return bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._async_set_demand(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._async_set_demand(False)

    async def _async_set_demand(self, state: bool) -> None:
        """Set the demand state."""
        try:
            # Get building info from coordinator data
            if not self.coordinator.data or "devices" not in self.coordinator.data:
                _LOGGER.error("No coordinator data available")
                return
                
            device = self.coordinator.data["devices"].get(self._device_id)
            if not device:
                _LOGGER.error("Device %s not found in coordinator data", self._device_id)
                return
            
            # Find the building ID for this device
            building_id = None
            for building in self.coordinator.data.get("buildings", []):
                building_id = building.get("id")
                break
                
            if not building_id:
                _LOGGER.error("No building ID found for device %s", self._device_id)
                return
            
            # Create device helper and set the demand state
            from pysensorlinx.sensorlinx import SensorlinxDevice
            device_helper = SensorlinxDevice(self.coordinator.sensorlinx, building_id, self._device_id)
            
            if self.entity_description.key == "permanent_heat_demand":
                await device_helper.set_permanent_hd(state)
                _LOGGER.debug("Set permanent heat demand to %s for device %s", state, self._device_id)
            elif self.entity_description.key == "permanent_cool_demand":
                await device_helper.set_permanent_cd(state)
                _LOGGER.debug("Set permanent cool demand to %s for device %s", state, self._device_id)
            
            # Refresh coordinator data
            await self.coordinator.async_request_refresh()
            
        except Exception as exc:
            _LOGGER.error("Failed to set %s to %s for device %s: %s", 
                         self.entity_description.key, state, self._device_id, exc)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        )
