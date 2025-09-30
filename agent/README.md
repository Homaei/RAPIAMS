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