# SensorLinx Home Assistant Integration

A custom Home Assistant integration for SensorLinx devices using the [pysensorlinx](https://pypi.org/project/pysensorlinx/) Python library.

## Features

- **Sensor Monitoring**: Monitor temperature, humidity, pressure, energy consumption, and power usage from your SensorLinx devices
- **Binary Sensors**: Track device connectivity, alarms, maintenance mode, and heating/cooling status
- **Climate Control**: Control thermostats and heat pumps with temperature setting and HVAC mode control
- **Real-time Updates**: Automatic polling of device data every 5 minutes
- **Multiple Buildings**: Support for multiple buildings and devices per account

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations" 
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL and select "Integration" as the category
5. Click "Add"
6. Find "SensorLinx" in the integration list and click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `sensorlinx` folder to your `custom_components` directory
2. Restart Home Assistant
3. Add the integration through the UI

## Configuration

1. In Home Assistant, go to **Configuration** > **Integrations**
2. Click the **+** button to add a new integration
3. Search for "SensorLinx"
4. Enter your SensorLinx username and password
5. Click **Submit**

The integration will automatically discover all your devices and create entities for:
- Temperature, humidity, pressure, energy, and power sensors
- Device connectivity and status binary sensors  
- Climate control entities for thermostats and heat pumps

## Supported Devices

This integration works with any SensorLinx-compatible device that provides:
- Sensor data (temperature, humidity, pressure, energy, power)
- Device status information
- Climate control capabilities (for thermostats/heat pumps)

## Device Parameters

The integration automatically maps SensorLinx device parameters to Home Assistant entities:

### Sensors
- `temperature` → Temperature sensor
- `humidity` → Humidity sensor  
- `pressure` → Pressure sensor
- `energy` → Energy sensor
- `power` → Power sensor

### Binary Sensors
- `online` → Connectivity status
- `alarm` → Alarm status
- `maintenance` → Maintenance mode
- `heating` → Heating status
- `cooling` → Cooling status

### Climate Controls
- `current_temperature` → Current temperature reading
- `target_temperature` → Target temperature setting
- `hvac_mode` → HVAC operation mode
- `heating`/`cooling` → Current HVAC action

## Troubleshooting

### Authentication Issues
- Verify your SensorLinx username and password are correct
- Check that your account has access to the devices you want to monitor

### Connection Issues  
- Ensure your Home Assistant instance has internet connectivity
- Check the Home Assistant logs for specific error messages

### Missing Entities
- Not all devices may support all sensor types
- Only devices with available parameters will create corresponding entities
- Check your device configuration in the SensorLinx app/portal

## Development

This integration is built using:
- [pysensorlinx](https://pypi.org/project/pysensorlinx/) - Python library for SensorLinx API
- Home Assistant's DataUpdateCoordinator for efficient data management
- Modern Home Assistant integration patterns and best practices

## Support

For issues related to:
- **Integration functionality**: Open an issue in this repository
- **SensorLinx API/devices**: Contact SensorLinx support
- **pysensorlinx library**: Check the [library repository](https://github.com/your_username/pysensorlinx)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
