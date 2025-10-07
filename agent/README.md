# Enhanced Raspberry Pi Monitoring Agent

**Advanced monitoring agent adapted from Telegram monitoring system for API backend integration**

## Overview

This enhanced monitoring agent provides comprehensive system monitoring for Raspberry Pi devices, sending real-time metrics to your API backend. It's built on the foundation of a sophisticated Telegram monitoring system, adapted for modern API integration.

## Features

### 📋 Comprehensive Monitoring
- **System Metrics**: CPU, Memory, Disk, Network, Temperature
- **Process Monitoring**: Running processes, resource usage
- **Service Monitoring**: Systemd services status
- **Security Monitoring**: Failed logins, SSH connections
- **GPIO Monitoring**: Digital pin states (Raspberry Pi specific)
- **Custom Scripts**: Execute and monitor custom metrics scripts

### 🚀 Advanced Features
- **Real-time Alerts**: Configurable thresholds with cooldown periods
- **Multi-level Logging**: Comprehensive logging with rotation
- **Retry Logic**: Robust error handling and automatic recovery
- **Health Checks**: Self-monitoring and diagnostics
- **Performance Optimized**: Efficient async operations
- **Security Focused**: Input validation and secure communications

### 🔧 Management Tools
- **CLI Management**: Rich command-line interface
- **Configuration Wizard**: Easy setup and configuration
- **Testing Tools**: Connectivity and functionality testing
- **Service Integration**: Systemd service with auto-restart

## Quick Start

### 1. Installation

```bash
# Download and run the installation script
sudo ./install.sh
```

### 2. Configuration

```bash
# Run the environment setup wizard
./setup-env.sh

# Or configure manually
python3 management.py configure
```

### 3. Testing

```bash
# Test configuration and connectivity
python3 management.py test

# Test metrics collection
python3 management.py collect --duration 60
```

### 4. Running

```bash
# Start as systemd service
sudo systemctl start rpi-monitoring-agent
sudo systemctl enable rpi-monitoring-agent

# Or run directly
python3 enhanced_main.py
```

## Configuration

### Environment Variables

```bash
# Required
API_ENDPOINT=https://your-backend.com
API_KEY=your-device-api-key
DEVICE_ID=raspberry-pi-001

# Optional
COLLECTION_INTERVAL=30
LOG_LEVEL=INFO
ENABLE_GPIO_MONITORING=true
GPIO_PINS=18,24,25
```

### JSON Configuration

```json
{
  "api_endpoint": "https://your-backend.com",
  "api_key": "your-device-api-key",
  "device_id": "raspberry-pi-001",
  "collection_interval": 30,
  "log_level": "INFO",
  "enable_detailed_monitoring": true,
  "enable_process_monitoring": true,
  "enable_service_monitoring": true,
  "enable_security_monitoring": true,
  "enable_network_monitoring": true,
  "enable_gpio_monitoring": true,
  "gpio_pins": [18, 24, 25],
  "custom_scripts": {
    "sensor_temp": "/opt/scripts/temp_sensor.sh"
  },
  "alert_thresholds": {
    "cpu_percent": {
      "info": 30.0,
      "warning": 70.0,
      "critical": 85.0,
      "danger": 95.0
    },
    "memory_percent": {
      "info": 50.0,
      "warning": 75.0,
      "critical": 85.0,
      "danger": 95.0
    },
    "disk_percent": {
      "info": 60.0,
      "warning": 75.0,
      "critical": 85.0,
      "danger": 95.0
    },
    "temperature_celsius": {
      "info": 40.0,
      "warning": 60.0,
      "critical": 75.0,
      "danger": 85.0
    }
  }
}
```

## API Integration

### Device Registration

The agent automatically registers with your backend API:

```python
POST /api/v1/agent/register
{
  "device_id": "raspberry-pi-001",
  "hostname": "raspberrypi",
  "model": "Raspberry Pi 4 Model B Rev 1.4",
  "os_version": "Linux 6.1.21-v8+",
  "agent_version": "2.0.0-enhanced",
  "cpu_cores": 4,
  "ram_total_mb": 8192,
  "storage_total_gb": 64.0,
  "ip_address": "192.168.1.100",
  "mac_address": "dc:a6:32:xx:xx:xx"
}
```

### Metrics Submission

```python
POST /api/v1/metrics/submit
Headers: X-API-Key: your-device-api-key
{
  "timestamp": "2024-01-01T12:00:00Z",
  "cpu_percent": 45.2,
  "cpu_temperature": 52.3,
  "memory_percent": 67.8,
  "memory_used_mb": 5500,
  "disk_percent": 23.1,
  "network_sent_bytes": 1024000,
  "network_recv_bytes": 2048000,
  "processes_total": 145,
  "uptime_seconds": 86400,
  "load_avg_1": 0.5,
  "gpio_states": {"18": 1, "24": 0},
  "custom_metrics": {"sensor_temp": 25.4}
}
```

### Alert Notifications

```python
POST /api/v1/agent/alert
Headers: X-API-Key: your-device-api-key
{
  "type": "cpu_temperature",
  "severity": "critical",
  "message": "CPU temperature critical: 85.2°C",
  "value": 85.2,
  "threshold": 85.0,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Management Commands

### Testing and Diagnostics

```bash
# Test configuration and connectivity
python3 management.py test

# Test metrics collection for 60 seconds
python3 management.py collect --duration 60

# Show agent status
python3 management.py status
```

### Configuration Management

```bash
# Interactive configuration wizard
python3 management.py configure

# Generate config with specific values
python3 management.py configure \
  --api-endpoint https://api.example.com \
  --api-key your-key \
  --device-id pi-living-room
```

## Service Management

### Systemd Service

```bash
# Service control
sudo systemctl start rpi-monitoring-agent
sudo systemctl stop rpi-monitoring-agent
sudo systemctl restart rpi-monitoring-agent
sudo systemctl enable rpi-monitoring-agent

# Check status
sudo systemctl status rpi-monitoring-agent

# View logs
sudo journalctl -u rpi-monitoring-agent -f
sudo journalctl -u rpi-monitoring-agent --since "1 hour ago"
```

### Log Files

```bash
# Agent logs
tail -f /var/log/rpi-monitor/agent.log
tail -f /var/log/rpi-monitor/agent_errors.log

# System logs
journalctl -u rpi-monitoring-agent -f
```

## Custom Scripts

You can add custom monitoring scripts that return numeric values or JSON:

### Example Temperature Sensor Script

```bash
#!/bin/bash
# /opt/scripts/temp_sensor.sh

# Read from DS18B20 temperature sensor
if [ -f /sys/bus/w1/devices/28-*/w1_slave ]; then
    temp=$(cat /sys/bus/w1/devices/28-*/w1_slave | grep 't=' | awk -F 't=' '{print $2/1000}')
    echo $temp
else
    echo "null"
fi
```

### JSON Output Script

```bash
#!/bin/bash
# /opt/scripts/multi_sensor.sh

echo '{
  "temperature": 25.4,
  "humidity": 60.2,
  "pressure": 1013.25
}'
```

## GPIO Monitoring

Monitor digital GPIO pins on Raspberry Pi:

```json
{
  "gpio_pins": [18, 24, 25],
  "enable_gpio_monitoring": true
}
```

GPIO states are included in metrics as:
```json
{
  "gpio_states": {
    "18": 1,
    "24": 0,
    "25": 1
  }
}
```

## Alert System

### Threshold Configuration

Alerts are triggered when metrics exceed configured thresholds:

- **Info**: Informational level (30% CPU)
- **Warning**: Warning level (70% CPU)
- **Critical**: Critical level (85% CPU)
- **Danger**: Emergency level (95% CPU)

### Alert Types

- `cpu_usage`: CPU utilization percentage
- `memory_usage`: Memory utilization percentage
- `disk_usage`: Disk utilization percentage
- `cpu_temperature`: CPU temperature in Celsius
- `network_connectivity`: Internet connectivity status
- `security_failed_logins`: Excessive failed login attempts

### Cooldown Period

Alerts have a cooldown period (default: 5 minutes) to prevent spam.

## Security Features

### Input Validation
- All inputs are sanitized and validated
- Command injection prevention
- Safe file operations

### Network Security
- TLS/SSL verification (configurable)
- API key authentication
- Rate limiting support

### System Security
- Runs as non-root user
- Minimal permissions
- Secure file permissions

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   ```bash
   # Check network connectivity
   ping google.com
   
   # Test API endpoint
   curl -I https://your-api-endpoint.com/health
   
   # Verify API key
   python3 management.py test
   ```

2. **GPIO Permission Denied**
   ```bash
   # Add user to gpio group
   sudo usermod -a -G gpio rpi-monitor
   
   # Restart service
   sudo systemctl restart rpi-monitoring-agent
   ```

3. **High CPU Usage**
   ```bash
   # Check collection interval
   # Increase interval in configuration
   "collection_interval": 60
   ```

4. **Service Won't Start**
   ```bash
   # Check service status
   sudo systemctl status rpi-monitoring-agent
   
   # Check logs
   sudo journalctl -u rpi-monitoring-agent -n 50
   
   # Test configuration
   python3 management.py test
   ```

### Debug Mode

```bash
# Run with debug logging
LOG_LEVEL=DEBUG python3 enhanced_main.py

# Or edit configuration
{
  "log_level": "DEBUG"
}
```

## Performance Tuning

### Collection Interval
- Default: 30 seconds
- Minimum recommended: 10 seconds
- For battery-powered devices: 300+ seconds

### Feature Toggling
Disable unused features to reduce resource usage:

```json
{
  "enable_detailed_monitoring": false,
  "enable_process_monitoring": false,
  "enable_security_monitoring": false
}
```

### Resource Usage
- Memory: ~50-100MB
- CPU: ~1-5% (depends on collection interval)
- Network: ~1-10KB per metric submission

## File Locations

```
/opt/rpi-monitoring-agent/     # Agent installation
/etc/rpi-monitor/              # Configuration files
/var/log/rpi-monitor/          # Log files
/var/lib/rpi-monitor/          # Data files
/etc/systemd/system/rpi-monitoring-agent.service  # Service file
```

## Development

### Requirements
- Python 3.8+
- Raspberry Pi OS (or compatible Linux)
- Network connectivity
- API backend (see main project)

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Adapted from the advanced Telegram monitoring system
- Built for integration with the FastAPI backend
- Optimized for Raspberry Pi hardware
- Inspired by modern IoT monitoring practices

## Support

For support and documentation:
- GitHub Issues: [Project Repository]
- Documentation: `/docs` endpoint on your API backend
- Configuration examples in this README


//////////////////////////////////////


# RAPIAMS Agent

A powerful, lightweight monitoring tool designed to run on Raspberry Pi devices for comprehensive system monitoring and alerting.

## Overview

The RAPIAMS Agent collects a wide range of system metrics from your Raspberry Pi, sends them to a central RAPIAMS backend for analysis and visualization, and can be configured to send alerts based on predefined thresholds.

## Features

- **Comprehensive System Monitoring:** Monitor CPU usage, memory, disk space, network activity, and temperature
- **GPIO Monitoring and Control:** Read the state of GPIO pins and control output devices
- **Custom Script Execution:** Extend functionality by running your own scripts and reporting their output as metrics
- **Alerting:** Configure thresholds for metrics to trigger alerts when limits are exceeded
- **Automated Installation:** Simple installation script gets you running quickly
- **Robust and Reliable:** Runs as a systemd service with automatic restarts
- **Flexible Configuration:** Easy-to-use interactive setup and detailed manual configuration options

## Prerequisites

Before installing the RAPIAMS Agent, ensure you have:

- A Raspberry Pi with a fresh installation of Raspberry Pi OS (or compatible Debian-based Linux distribution)
- Internet connectivity on the Raspberry Pi
- Root (sudo) access to the Raspberry Pi

## Installation

The installation process is fully automated using the provided installation script.

### Steps

1. **Clone the repository or copy the agent files** to your Raspberry Pi

2. **Navigate to the agent directory:**
   ```bash
   cd /path/to/RAPIAMS-main/agent
   ```

3. **Run the installation script:**
   ```bash
   sudo ./install.sh
   ```

### What the Installation Script Does

The installation script automatically:

- Installs system dependencies (Python 3, pip, etc.)
- Creates a dedicated user (`rpi-monitor`) to run the agent
- Creates necessary directories for the agent, configuration, logs, and data
- Copies agent files to `/opt/rpi-monitoring-agent`
- Sets up a Python virtual environment and installs required Python packages
- Creates a systemd service for automatic startup on boot
- Sets up log rotation
- Creates a default configuration file

## Configuration

You can configure the RAPIAMS Agent in two ways: using the interactive setup script or by manually editing the configuration file.

### Interactive Setup (Recommended)

The easiest way to configure the agent is using the `setup-env.sh` script.

1. **Navigate to the agent's installation directory:**
   ```bash
   cd /opt/rpi-monitoring-agent
   ```

2. **Run the setup script:**
   ```bash
   ./setup-env.sh
   ```

The script will prompt you for:

- **API Endpoint URL:** The URL of your RAPIAMS backend server (e.g., `http://your-server.com:8000`)
- **API Key:** The API key for the device, obtained from the RAPIAMS backend
- **Device ID:** A unique identifier for this Raspberry Pi (defaults to hostname)
- **Collection Interval:** Frequency in seconds for sending data to the server (defaults to 30)
- **Log Level:** Desired logging level - DEBUG, INFO, WARNING, or ERROR (defaults to INFO)

The script creates a `.env` file and updates the main JSON configuration file.

### Manual Configuration

You can also configure the agent by directly editing the JSON configuration file.

1. **Open the configuration file:**
   ```bash
   sudo nano /etc/rpi-monitor/agent_config.json
   ```

2. **Edit the values as needed.** The file is standard JSON format.

### Server Configuration Parameters

The following parameters in `agent_config.json` control server communication and data collection:

- `api_endpoint`: The full URL of the RAPIAMS backend API
- `api_key`: The secret API key for this device
- `device_id`: A unique name for this device
- `collection_interval`: The interval in seconds for sending metrics
- `max_retries`: Number of times to retry sending data if connection fails
- `retry_delay`: Delay in seconds between retries
- `enable_ssl_verify`: Set to `false` if your server uses a self-signed SSL certificate

### Wi-Fi Configuration

The agent does not directly manage the Raspberry Pi's Wi-Fi connection. Configure Wi-Fi using standard Raspberry Pi OS tools:

- Use `raspi-config`, or
- Edit `/etc/wpa_supplicant/wpa_supplicant.conf`

The agent will monitor the network connection and report its status to the RAPIAMS backend.

### GPIO Configuration

The agent can monitor and control GPIO pins.

1. **Enable GPIO monitoring** in `/etc/rpi-monitor/agent_config.json`:
   ```json
   "enable_gpio_monitoring": true,
   ```

2. **Define GPIO pins to monitor** by adding their BCM numbers to the `gpio_pins` list:
   ```json
   "gpio_pins": [18, 24, 25],
   ```

3. **For advanced GPIO control (output devices),** define devices in a separate `gpio_config.json` file:

   **Example `gpio_config.json`:**
   ```json
   {
     "gpio_devices": {
       "buzzer": {
         "pin": 17,
         "mode": "OUTPUT",
         "active_state": "HIGH",
         "initial_state": "LOW",
         "description": "Test buzzer for GPIO verification"
       }
     },
     "gpio_settings": {
       "mode": "BCM",
       "warnings": false
     }
   }
   ```

### Custom Scripts

The agent can execute custom scripts and report their output as metrics.

1. **Add script information** to the `custom_scripts` section of `/etc/rpi-monitor/agent_config.json`:
   ```json
   "custom_scripts": {
     "sensor_temp": "/opt/scripts/temp_sensor.sh"
   }
   ```

2. **Ensure your script is executable:**
   ```bash
   chmod +x /opt/scripts/temp_sensor.sh
   ```

Your script should output either a single numeric value or a JSON object.

### Alerting

Configure thresholds for various metrics to trigger alerts in the RAPIAMS backend. Define these in the `alert_thresholds` section of the configuration file.

**Example:**
```json
"alert_thresholds": {
  "cpu_percent": {
    "warning": 70.0,
    "critical": 85.0
  },
  "temperature_celsius": {
    "warning": 60.0,
    "critical": 75.0
  }
}
```

## Running the Agent

### As a Systemd Service (Recommended)

The recommended way to run the agent is as a systemd service, which allows automatic startup on boot.

**Start the service:**
```bash
sudo systemctl start rpi-monitoring-agent
```

**Enable the service to start on boot:**
```bash
sudo systemctl enable rpi-monitoring-agent
```

**Check the status of the service:**
```bash
sudo systemctl status rpi-monitoring-agent
```

**Stop the service:**
```bash
sudo systemctl stop rpi-monitoring-agent
```

### Manually (for Testing/Debugging)

You can also run the agent directly for testing or debugging purposes.

1. **Navigate to the agent's installation directory:**
   ```bash
   cd /opt/rpi-monitoring-agent
   ```

2. **Activate the Python virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Run the main agent script:**
   ```bash
   python3 enhanced_main.py
   ```

## Logging

### Systemd Logs

The primary logs are managed by `journald`. To view them:

```bash
sudo journalctl -u rpi-monitoring-agent -f
```

### Log Files

The agent also writes to log files in `/var/log/rpi-monitor/`:

- `agent.log`: General information and metric collection logs
- `agent_errors.log`: Error messages

Log rotation is handled automatically.

## Troubleshooting

### Service Fails to Start

- Check the service status for errors:
  ```bash
  sudo systemctl status rpi-monitoring-agent
  ```
- Check the journald logs:
  ```bash
  sudo journalctl -u rpi-monitoring-agent
  ```
- Verify that the configuration file at `/etc/rpi-monitor/agent_config.json` is valid JSON

### "API Connection Failed" Errors

- Ensure your Raspberry Pi has internet connectivity:
  ```bash
  ping 8.8.8.8
  ```
- Verify that the `api_endpoint` in your configuration is correct
- Check that your RAPIAMS backend server is running and accessible from the Raspberry Pi

### "GPIO Permission Denied" Errors

- The `rpi-monitor` user needs to be a member of the `gpio` group. The installation script should handle this, but you can verify with:
  ```bash
  groups rpi-monitor
  ```
- If needed, add the user to the group:
  ```bash
  sudo usermod -a -G gpio rpi-monitor
  ```
  Then restart the agent.

## Support

For issues, questions, or feature requests, please refer to the project documentation or contact your system administrator.

## License

Please refer to the LICENSE file in the project repository for licensing information.
