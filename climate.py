"""Platform for climate integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEVICE_TYPE_HEAT_PUMP, DEVICE_TYPE_THERMOSTAT, DOMAIN
from .coordinator import SensorLinxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the climate platform."""
    coordinator: SensorLinxDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    if coordinator.data and "devices" in coordinator.data:
        for device_id, device in coordinator.data["devices"].items():
            device_type = device.get("type", "").lower()
            if device_type in [DEVICE_TYPE_THERMOSTAT, DEVICE_TYPE_HEAT_PUMP]:
                entities.append(
                    SensorLinxClimate(
                        coordinator,
                        device_id,
                        device,
                    )
                )
    
    async_add_entities(entities)


class SensorLinxClimate(CoordinatorEntity, ClimateEntity):
    """Implementation of a SensorLinx climate entity."""

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        
        self._attr_unique_id = f"{device_id}_climate"
        self._attr_name = f"{device.get('name', device_id)} Climate"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        
        # Supported features
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        
        # Supported HVAC modes
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.HEAT,
            HVACMode.COOL,
            HVACMode.AUTO,
        ]
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("type", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
            
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
            
        parameters = device.get("parameters", {})
        # Try to get hot tank temperature first, then cold tank
        temp = parameters.get("temperature_hot_tank") or parameters.get("temperature_cold_tank")
        return temp

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
            
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
            
        parameters = device.get("parameters", {})
        # Get target temperature based on current mode
        hvac_mode = self.hvac_mode
        if hvac_mode == HVACMode.HEAT:
            return parameters.get("target_temperature_hot_tank")
        elif hvac_mode == HVACMode.COOL:
            return parameters.get("target_temperature_cold_tank")
        else:
            # Auto mode - return hot tank target as default
            return parameters.get("target_temperature_hot_tank")

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac operation ie. heat, cool mode."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
            
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
            
        parameters = device.get("parameters", {})
        mode = parameters.get("hvac_mode", "").lower()
        
        if mode == "off":
            return HVACMode.OFF
        elif mode == "heat":
            return HVACMode.HEAT
        elif mode == "cool":
            return HVACMode.COOL
        elif mode == "auto":
            return HVACMode.AUTO
        
        return HVACMode.AUTO  # Default to auto

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
            
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
            
        parameters = device.get("parameters", {})
        
        # Check demand states
        if parameters.get("permanent_heat_demand", False):
            return HVACAction.HEATING
        elif parameters.get("permanent_cool_demand", False):
            return HVACAction.COOLING
        elif self.hvac_mode != HVACMode.OFF:
            return HVACAction.IDLE
        
        return HVACAction.OFF

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
            
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
                # You'll need to implement logic to find which building this device belongs to
                # For now, use the first building
                building_id = building.get("id")
                break
                
            if not building_id:
                _LOGGER.error("No building ID found for device %s", self._device_id)
                return
            
            # Create device helper and set temperature based on current mode
            from pysensorlinx.sensorlinx import SensorlinxDevice, Temperature
            device_helper = SensorlinxDevice(self.coordinator.sensorlinx, building_id, self._device_id)
            
            # Convert temperature to Fahrenheit (SensorLinx uses Fahrenheit)
            temp_f = Temperature(temperature, "C").to_fahrenheit() if self.temperature_unit == UnitOfTemperature.CELSIUS else temperature
            temp_obj = Temperature(temp_f, "F")
            
            hvac_mode = self.hvac_mode
            if hvac_mode == HVACMode.HEAT:
                await device_helper.set_hot_tank_target_temp(temp_obj)
            elif hvac_mode == HVACMode.COOL:
                await device_helper.set_cold_tank_target_temp(temp_obj)
            else:
                # Auto mode - set both hot and cool tank targets
                await device_helper.set_hot_tank_target_temp(temp_obj)
            
            await self.coordinator.async_request_refresh()
        except Exception as exc:
            _LOGGER.error("Failed to set temperature for %s: %s", self._device_id, exc)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
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
            
            # Create device helper and set HVAC mode
            from pysensorlinx.sensorlinx import SensorlinxDevice
            device_helper = SensorlinxDevice(self.coordinator.sensorlinx, building_id, self._device_id)
            
            await device_helper.set_hvac_mode_priority(hvac_mode.value)
            await self.coordinator.async_request_refresh()
        except Exception as exc:
            _LOGGER.error("Failed to set HVAC mode for %s: %s", self._device_id, exc)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        )
