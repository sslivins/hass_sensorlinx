# SensorLinx Integration for Home Assistant

![SensorLinx Logo](https://via.placeholder.com/150x50/0066cc/ffffff?text=SensorLinx)

A comprehensive Home Assistant integration for SensorLinx IoT devices, providing seamless connectivity and control of your smart sensors, thermostats, and heat pumps.

## Features

✅ **Comprehensive Device Support**
- Temperature, humidity, pressure sensors
- Energy consumption and power monitoring  
- Device connectivity and status tracking
- Climate control for thermostats and heat pumps

✅ **Real-time Monitoring**
- Automatic data updates every 5 minutes
- Live device status and alarm notifications
- Maintenance mode detection

✅ **Climate Control**
- Set target temperatures
- Control HVAC modes (Heat, Cool, Auto, Off)
- Monitor current heating/cooling status

✅ **Multi-Building Support**
- Manage devices across multiple locations
- Organized device discovery and setup

## Quick Setup

1. **Install via HACS** (recommended)
   - Add this repository as a custom repository
   - Install the SensorLinx integration
   - Restart Home Assistant

2. **Configure Integration**
   - Go to Settings → Devices & Services
   - Click "Add Integration" and search for "SensorLinx"
   - Enter your SensorLinx credentials
   - All devices will be automatically discovered

3. **Start Monitoring**
   - View sensors in your Dashboard
   - Control climate devices
   - Set up automations based on sensor data

## Requirements

- Home Assistant 2023.1.0 or newer
- Active SensorLinx account with device access
- Internet connectivity for API communication

## Device Compatibility

This integration works with all SensorLinx-compatible devices including:
- Smart temperature/humidity sensors
- Pressure monitoring devices
- Energy meters and power monitors
- Smart thermostats
- Heat pump controllers
- Building automation systems

## Support & Documentation

- 📚 [Full Documentation](https://github.com/your_username/hass_sensorlinx)
- 🐛 [Report Issues](https://github.com/your_username/hass_sensorlinx/issues)
- 💬 [Community Forum](https://community.home-assistant.io/)

---

*This integration uses the [pysensorlinx](https://pypi.org/project/pysensorlinx/) Python library to communicate with SensorLinx devices.*
