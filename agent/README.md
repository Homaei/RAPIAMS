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



# RAPIAMS Agent: Comprehensive Installation and 
      Configuration Guide
    2 
    3 This document provides a complete guide to installing, 
      configuring, and running the RAPIAMS monitoring agent on a 
      Raspberry Pi.
    4 
    5 ## 1. Overview
    6 
    7 The RAPIAMS Agent is a powerful, lightweight monitoring tool
      designed to run on Raspberry Pi devices. It collects a wide 
      range of system metrics, sends them to a central RAPIAMS 
      backend for analysis and visualization, and can be 
      configured to send alerts based on predefined thresholds.
    8 
    9 ## 2. Features
   10 
   11 *   **Comprehensive System Monitoring:** CPU, memory, disk, 
      network, and temperature.
   12 *   **GPIO Monitoring and Control:** Read the state of GPIO 
      pins and control output devices.
   13 *   **Custom Script Execution:** Extend the agent's 
      capabilities by running your own scripts.
   14 *   **Alerting:** Configure thresholds for metrics to 
      trigger alerts.
   15 *   **Automated Installation:** A simple installation script
      to get you up and running quickly.
   16 *   **Robust and Reliable:** Runs as a `systemd` service 
      with automatic restarts.
   17 *   **Flexible Configuration:** Easy-to-use interactive 
      setup and detailed manual configuration options.
   18 
   19 ## 3. Prerequisites
   20 
   21 Before you begin, ensure you have the following:
   22 
   23 *   A Raspberry Pi with a fresh installation of Raspberry Pi
      OS (or a compatible Debian-based Linux distribution).
   24 *   Internet connectivity on the Raspberry Pi.
   25 *   Root (sudo) access to the Raspberry Pi.
   26 
   27 ## 4. Installation
   28 
   29 The installation process is automated with an installation 
      script.
   30 
   31 1.  **Clone the repository or copy the agent files** to your
      Raspberry Pi.
   32 
   33 2.  **Navigate to the `agent` directory:**
      cd /path/to/RAPIAMS-main/agent
   1 
   2 3.  **Run the installation script:**
      sudo ./install.sh

    1 
    2 The installation script will perform the following actions:
    3 
    4 *   Install system dependencies (Python 3, pip, etc.).
    5 *   Create a dedicated user (`rpi-monitor`) to run the 
      agent.
    6 *   Create necessary directories for the agent, 
      configuration, logs, and data.
    7 *   Copy the agent files to `/opt/rpi-monitoring-agent`.
    8 *   Set up a Python virtual environment and install the 
      required Python packages.
    9 *   Create a `systemd` service to run the agent 
      automatically on boot.
   10 *   Set up log rotation.
   11 *   Create a default configuration file.
   12 
   13 ## 5. Configuration
   14 
   15 There are two ways to configure the agent: using the 
      interactive setup script or by manually editing the 
      configuration file.
   16 
   17 ### 5.1. Using the Interactive Setup
   18 
   19 The easiest way to configure the agent is to use the 
      `setup-env.sh` script.
   20 
   21 1.  **Navigate to the agent's installation directory:**
      cd /opt/rpi-monitoring-agent
   1 
   2 2.  **Run the setup script:**
      ./setup-env.sh

    1 
    2 The script will prompt you for the following information:
    3 
    4 *   **API Endpoint URL:** The URL of your RAPIAMS backend 
      server (e.g., `http://your-server.com:8000`).
    5 *   **API Key:** The API key for the device, obtained from 
      the RAPIAMS backend.
    6 *   **Device ID:** A unique identifier for this Raspberry Pi
      (defaults to the hostname).
    7 *   **Collection Interval:** The frequency (in seconds) at 
      which the agent sends data to the server (defaults to 30).
    8 *   **Log Level:** The desired logging level (DEBUG, INFO, 
      WARNING, ERROR; defaults to INFO).
    9 
   10 This script will create a `.env` file in the current 
      directory and also update the main JSON configuration file.
   11 
   12 ### 5.2. Manual Configuration
   13 
   14 You can also configure the agent by directly editing the 
      JSON configuration file.
   15 
   16 1.  **Open the configuration file in a text editor:**
      sudo nano /etc/rpi-monitor/agent_config.json

    1 
    2 2.  **Edit the values as needed.** The file is a standard 
      JSON file, and you can edit the values for each key.
    3 
    4 ### 5.3. Server Configuration
    5 
    6 The following parameters in `agent_config.json` are related 
      to the server and data collection:
    7 
    8 *   `api_endpoint`: The full URL of the RAPIAMS backend API.
    9 *   `api_key`: The secret API key for this device.
   10 *   `device_id`: A unique name for this device.
   11 *   `collection_interval`: The interval in seconds for 
      sending metrics.
   12 *   `max_retries`: The number of times to retry sending data
      if the connection fails.
   13 *   `retry_delay`: The delay in seconds between retries.
   14 *   `enable_ssl_verify`: Set to `false` if your server uses 
      a self-signed SSL certificate.
   15 
   16 ### 5.4. Wi-Fi Configuration
   17 
   18 The agent does not directly manage the Raspberry Pi's Wi-Fi 
      connection. You should configure Wi-Fi using the standard 
      Raspberry Pi OS tools (e.g., `raspi-config` or by editing 
      `/etc/wpa_supplicant/wpa_supplicant.conf`).
   19 
   20 The agent will monitor the network connection and report its
      status to the RAPIAMS backend.
   21 
   22 ### 5.5. GPIO Configuration
   23 
   24 The agent can monitor and control GPIO pins.
   25 
   26 1.  **Enable GPIO monitoring** in 
      `/etc/rpi-monitor/agent_config.json`:
      "enable_gpio_monitoring": true,
   1 
   2 2.  **Define which GPIO pins to monitor** by adding their BCM
     numbers to the `gpio_pins` list:
      "gpio_pins": [18, 24, 25],

   1 
   2 3.  **For advanced GPIO control (output devices),** you can 
     define devices in a separate `gpio_config.json` file (the 
     location of this file can be configured in the main config). 
     An example is provided in the agent directory.
   3 
   4     **Example `gpio_config.json`:**
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

   1 
   2 ### 5.6. Custom Scripts
   3 
   4 The agent can execute custom scripts and report their output 
     as metrics.
   5 
   6 1.  **Add your script's information** to the `custom_scripts`
     section of `/etc/rpi-monitor/agent_config.json`. The key is 
     the metric name and the value is the path to the script.
      "custom_scripts": {
        "sensor_temp": "/opt/scripts/temp_sensor.sh"
      }
   1 
   2 2.  **Ensure your script is executable:**
      chmod +x /opt/scripts/temp_sensor.sh

   1 
   2 Your script should output a single numeric value or a JSON 
     object.
   3 
   4 ### 5.7. Alerting
   5 
   6 You can configure thresholds for various metrics to trigger 
     alerts in the RAPIAMS backend. These are defined in the 
     `alert_thresholds` section of the configuration file.
   7 
   8 **Example:**
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

   1 
   2 ## 6. Running the Agent
   3 
   4 ### 6.1. As a Systemd Service
   5 
   6 The recommended way to run the agent is as a `systemd` 
     service, which allows it to start automatically on boot.
   7 
   8 *   **Start the service:**
      sudo systemctl start rpi-monitoring-agent
   1 
   2 *   **Enable the service to start on boot:**
      sudo systemctl enable rpi-monitoring-agent

   1 
   2 *   **Check the status of the service:**
      sudo systemctl status rpi-monitoring-agent
   1 
   2 *   **Stop the service:**
      sudo systemctl stop rpi-monitoring-agent

   1 
   2 ### 6.2. Manually
   3 
   4 You can also run the agent directly for testing or debugging 
     purposes.
   5 
   6 1.  **Navigate to the agent's installation directory:**
      cd /opt/rpi-monitoring-agent
   1 
   2 2.  **Activate the Python virtual environment:**
      source venv/bin/activate
   1 
   2 3.  **Run the main agent script:**
      python3 enhanced_main.py
   1 
   2 ## 7. Logging
   3 
   4 *   **Systemd Logs:** The primary logs are managed by 
     `journald`. To view them:
      sudo journalctl -u rpi-monitoring-agent -f
    1 
    2 *   **Log Files:** The agent also writes to log files in 
      `/var/log/rpi-monitor/`.
    3     *   `agent.log`: General information and metric 
      collection logs.
    4     *   `agent_errors.log`: Error messages.
    5 
    6 Log rotation is handled automatically.
    7 
    8 ## 8. Troubleshooting
    9 
   10 *   **Service Fails to Start:**
   11     *   Check the service status for errors: `sudo systemctl
      status rpi-monitoring-agent`
   12     *   Check the journald logs: `sudo journalctl -u 
      rpi-monitoring-agent`
   13     *   Verify that the configuration file at 
      `/etc/rpi-monitor/agent_config.json` is valid JSON.
   14 
   15 *   **"API Connection Failed" Errors:**
   16     *   Ensure your Raspberry Pi has internet connectivity: 
      `ping 8.8.8.8`
   17     *   Verify that the `api_endpoint` in your configuration
      is correct.
   18     *   Check that your RAPIAMS backend server is running 
      and accessible from the Raspberry Pi.
   19 
   20 *   **"GPIO Permission Denied" Errors:**
   21     *   The `rpi-monitor` user needs to be a member of the 
      `gpio` group. The installation script should handle this, 
      but you can verify with `groups rpi-monitor`.
   22     *   If needed, add the user to the group: `sudo usermod 
      -a -G gpio rpi-monitor` and restart the agent.

