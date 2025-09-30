"""
Temperature Monitor Module
Monitors CPU, GPU, and system temperatures
"""

import psutil
import os
import time
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import threading
from collections import deque
import statistics
import glob


class TemperatureMonitor:
    def __init__(self, history_size: int = 300):  # 5 minutes of history at 1-second intervals
        self.logger = logging.getLogger(__name__)
        self.history_size = history_size
        self.temperature_history = {}
        self._monitoring = False
        self._monitor_thread = None
        self._lock = threading.Lock()

    def get_all_temperatures(self) -> Dict[str, Any]:
        """Get all available temperature sensors"""
        try:
            temperatures = {
                'timestamp': datetime.now().isoformat(),
                'sensors': {},
                'summary': {
                    'total_sensors': 0,
                    'average_temp': 0,
                    'max_temp': 0,
                    'critical_sensors': 0,
                    'warning_sensors': 0
                }
            }

            # Try psutil sensors first
            psutil_temps = self._get_psutil_temperatures()
            if psutil_temps:
                temperatures['sensors'].update(psutil_temps)

            # Try additional methods for Raspberry Pi
            rpi_temps = self._get_raspberry_pi_temperatures()
            if rpi_temps:
                temperatures['sensors'].update(rpi_temps)

            # Try thermal zone readings (Linux)
            thermal_temps = self._get_thermal_zone_temperatures()
            if thermal_temps:
                temperatures['sensors'].update(thermal_temps)

            # Try NVIDIA GPU temperatures
            nvidia_temps = self._get_nvidia_temperatures()
            if nvidia_temps:
                temperatures['sensors'].update(nvidia_temps)

            # Calculate summary
            all_temps = []
            critical_count = 0
            warning_count = 0

            for sensor_group in temperatures['sensors'].values():
                if isinstance(sensor_group, list):
                    for sensor in sensor_group:
                        if isinstance(sensor, dict) and 'current' in sensor:
                            temp = sensor['current']
                            all_temps.append(temp)

                            # Check thresholds
                            if temp >= 80:  # Critical threshold
                                critical_count += 1
                            elif temp >= 70:  # Warning threshold
                                warning_count += 1

            if all_temps:
                temperatures['summary'] = {
                    'total_sensors': len(all_temps),
                    'average_temp': round(statistics.mean(all_temps), 2),
                    'max_temp': round(max(all_temps), 2),
                    'min_temp': round(min(all_temps), 2),
                    'critical_sensors': critical_count,
                    'warning_sensors': warning_count
                }

            return temperatures

        except Exception as e:
            self.logger.error(f"Error getting temperatures: {e}")
            return {"error": str(e)}

    def _get_psutil_temperatures(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get temperatures using psutil"""
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                return {}

            result = {}
            for name, entries in temps.items():
                sensor_list = []
                for entry in entries:
                    sensor_info = {
                        'label': entry.label or f"{name}_sensor",
                        'current': entry.current,
                        'high': entry.high if entry.high else None,
                        'critical': entry.critical if entry.critical else None,
                        'status': self._get_temperature_status(entry.current, entry.high, entry.critical)
                    }
                    sensor_list.append(sensor_info)
                result[name] = sensor_list

            return result

        except Exception as e:
            self.logger.debug(f"psutil temperature reading failed: {e}")
            return {}

    def _get_raspberry_pi_temperatures(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get Raspberry Pi specific temperatures"""
        try:
            rpi_temps = {}

            # CPU temperature from /sys/class/thermal/thermal_zone0/temp
            cpu_temp_file = '/sys/class/thermal/thermal_zone0/temp'
            if os.path.exists(cpu_temp_file):
                with open(cpu_temp_file, 'r') as f:
                    temp_raw = int(f.read().strip())
                    temp_celsius = temp_raw / 1000.0

                rpi_temps['raspberry_pi_cpu'] = [{
                    'label': 'CPU Temperature',
                    'current': temp_celsius,
                    'high': 70.0,
                    'critical': 80.0,
                    'status': self._get_temperature_status(temp_celsius, 70.0, 80.0)
                }]

            # GPU temperature (vcgencmd)
            gpu_temp = self._get_raspberry_pi_gpu_temp()
            if gpu_temp:
                rpi_temps['raspberry_pi_gpu'] = [{
                    'label': 'GPU Temperature',
                    'current': gpu_temp,
                    'high': 70.0,
                    'critical': 80.0,
                    'status': self._get_temperature_status(gpu_temp, 70.0, 80.0)
                }]

            return rpi_temps

        except Exception as e:
            self.logger.debug(f"Raspberry Pi temperature reading failed: {e}")
            return {}

    def _get_raspberry_pi_gpu_temp(self) -> Optional[float]:
        """Get Raspberry Pi GPU temperature using vcgencmd"""
        try:
            result = subprocess.run(['vcgencmd', 'measure_temp'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Output format: temp=42.8'C
                temp_str = result.stdout.strip()
                if 'temp=' in temp_str:
                    temp_value = temp_str.split('=')[1].replace("'C", "")
                    return float(temp_value)
        except Exception as e:
            self.logger.debug(f"vcgencmd failed: {e}")
        return None

    def _get_thermal_zone_temperatures(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get temperatures from thermal zones (Linux)"""
        try:
            thermal_temps = {}
            thermal_zones = glob.glob('/sys/class/thermal/thermal_zone*/temp')

            for zone_file in thermal_zones:
                try:
                    zone_name = os.path.basename(os.path.dirname(zone_file))

                    with open(zone_file, 'r') as f:
                        temp_raw = int(f.read().strip())
                        temp_celsius = temp_raw / 1000.0

                    # Try to get zone type
                    type_file = os.path.join(os.path.dirname(zone_file), 'type')
                    zone_type = 'Unknown'
                    if os.path.exists(type_file):
                        with open(type_file, 'r') as f:
                            zone_type = f.read().strip()

                    thermal_temps[f'thermal_{zone_name}'] = [{
                        'label': f'{zone_type} ({zone_name})',
                        'current': temp_celsius,
                        'high': None,
                        'critical': None,
                        'status': self._get_temperature_status(temp_celsius)
                    }]

                except Exception as e:
                    self.logger.debug(f"Error reading thermal zone {zone_file}: {e}")
                    continue

            return thermal_temps

        except Exception as e:
            self.logger.debug(f"Thermal zone reading failed: {e}")
            return {}

    def _get_nvidia_temperatures(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get NVIDIA GPU temperatures"""
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=temperature.gpu,temperature.memory',
                                   '--format=csv,noheader,nounits'],
                                  capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                nvidia_temps = {}
                lines = result.stdout.strip().split('\n')

                for i, line in enumerate(lines):
                    temps = line.split(', ')
                    if len(temps) >= 2:
                        gpu_temp = float(temps[0])
                        mem_temp = float(temps[1]) if temps[1] != '[Not Supported]' else None

                        gpu_sensors = [{
                            'label': f'GPU {i} Core',
                            'current': gpu_temp,
                            'high': 83.0,
                            'critical': 95.0,
                            'status': self._get_temperature_status(gpu_temp, 83.0, 95.0)
                        }]

                        if mem_temp is not None:
                            gpu_sensors.append({
                                'label': f'GPU {i} Memory',
                                'current': mem_temp,
                                'high': 95.0,
                                'critical': 105.0,
                                'status': self._get_temperature_status(mem_temp, 95.0, 105.0)
                            })

                        nvidia_temps[f'nvidia_gpu_{i}'] = gpu_sensors

                return nvidia_temps

        except FileNotFoundError:
            self.logger.debug("nvidia-smi not found")
        except Exception as e:
            self.logger.debug(f"NVIDIA temperature reading failed: {e}")

        return {}

    def get_cpu_temperature(self) -> Dict[str, Any]:
        """Get specifically CPU temperature"""
        try:
            all_temps = self.get_all_temperatures()
            cpu_temps = []

            # Look for CPU-related sensors
            for sensor_name, sensors in all_temps.get('sensors', {}).items():
                if 'cpu' in sensor_name.lower() or 'core' in sensor_name.lower():
                    if isinstance(sensors, list):
                        cpu_temps.extend(sensors)

            if cpu_temps:
                current_temps = [sensor['current'] for sensor in cpu_temps]
                return {
                    'timestamp': datetime.now().isoformat(),
                    'sensors': cpu_temps,
                    'average_temperature': round(statistics.mean(current_temps), 2),
                    'max_temperature': round(max(current_temps), 2),
                    'min_temperature': round(min(current_temps), 2),
                    'status': self._get_overall_temperature_status(max(current_temps))
                }
            else:
                return {"error": "No CPU temperature sensors found"}

        except Exception as e:
            self.logger.error(f"Error getting CPU temperature: {e}")
            return {"error": str(e)}

    def start_monitoring(self, interval: float = 1.0):
        """Start continuous temperature monitoring"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        self.logger.info("Temperature monitoring started")

    def stop_monitoring(self):
        """Stop continuous temperature monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.logger.info("Temperature monitoring stopped")

    def _monitor_loop(self, interval: float):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                timestamp = datetime.now()
                all_temps = self.get_all_temperatures()

                if 'sensors' in all_temps:
                    with self._lock:
                        for sensor_group, sensors in all_temps['sensors'].items():
                            if isinstance(sensors, list):
                                for sensor in sensors:
                                    if isinstance(sensor, dict) and 'current' in sensor:
                                        sensor_key = f"{sensor_group}_{sensor.get('label', 'unknown')}"

                                        if sensor_key not in self.temperature_history:
                                            self.temperature_history[sensor_key] = deque(maxlen=self.history_size)

                                        self.temperature_history[sensor_key].append({
                                            'timestamp': timestamp,
                                            'temperature': sensor['current'],
                                            'status': sensor.get('status', 'unknown')
                                        })

                time.sleep(interval)

            except Exception as e:
                self.logger.error(f"Error in temperature monitoring loop: {e}")
                time.sleep(interval)

    def get_temperature_history(self, sensor: str = None, minutes: int = 5) -> Dict[str, Any]:
        """Get temperature history"""
        try:
            with self._lock:
                if not self.temperature_history:
                    return {"error": "No history available. Start monitoring first."}

                cutoff_time = datetime.now() - timedelta(minutes=minutes)
                result = {}

                sensors_to_check = [sensor] if sensor else list(self.temperature_history.keys())

                for sensor_key in sensors_to_check:
                    if sensor_key in self.temperature_history:
                        recent_data = [
                            entry for entry in self.temperature_history[sensor_key]
                            if entry['timestamp'] > cutoff_time
                        ]

                        if recent_data:
                            temps = [entry['temperature'] for entry in recent_data]
                            result[sensor_key] = {
                                'data_points': len(recent_data),
                                'statistics': {
                                    'average': round(statistics.mean(temps), 2),
                                    'min': round(min(temps), 2),
                                    'max': round(max(temps), 2),
                                    'median': round(statistics.median(temps), 2)
                                },
                                'timeline': [
                                    {
                                        'timestamp': entry['timestamp'].isoformat(),
                                        'temperature': entry['temperature'],
                                        'status': entry['status']
                                    }
                                    for entry in recent_data[-60:]  # Last 60 data points
                                ]
                            }

                return {
                    'period_minutes': minutes,
                    'sensors': result
                }

        except Exception as e:
            self.logger.error(f"Error getting temperature history: {e}")
            return {"error": str(e)}

    def get_temperature_alerts(self, warning_threshold: float = 70, critical_threshold: float = 80) -> Dict[str, Any]:
        """Check for temperature alerts"""
        try:
            alerts = []
            all_temps = self.get_all_temperatures()

            if 'sensors' in all_temps:
                for sensor_group, sensors in all_temps['sensors'].items():
                    if isinstance(sensors, list):
                        for sensor in sensors:
                            if isinstance(sensor, dict) and 'current' in sensor:
                                temp = sensor['current']
                                label = sensor.get('label', 'Unknown')

                                if temp >= critical_threshold:
                                    alerts.append({
                                        'type': 'temperature',
                                        'level': 'critical',
                                        'sensor': f"{sensor_group}_{label}",
                                        'message': f"Critical temperature: {temp:.1f}°C",
                                        'temperature': temp,
                                        'threshold': critical_threshold
                                    })
                                elif temp >= warning_threshold:
                                    alerts.append({
                                        'type': 'temperature',
                                        'level': 'warning',
                                        'sensor': f"{sensor_group}_{label}",
                                        'message': f"High temperature: {temp:.1f}°C",
                                        'temperature': temp,
                                        'threshold': warning_threshold
                                    })

            return {
                'timestamp': datetime.now().isoformat(),
                'thresholds': {
                    'warning': warning_threshold,
                    'critical': critical_threshold
                },
                'alerts': alerts,
                'alert_count': len(alerts)
            }

        except Exception as e:
            self.logger.error(f"Error checking temperature alerts: {e}")
            return {"error": str(e)}

    def get_thermal_throttling_status(self) -> Dict[str, Any]:
        """Check for thermal throttling (Raspberry Pi specific)"""
        try:
            throttling_info = {
                'timestamp': datetime.now().isoformat(),
                'is_throttled': False,
                'current_issues': [],
                'past_issues': [],
                'raw_status': None
            }

            # Check Raspberry Pi throttling status
            try:
                result = subprocess.run(['vcgencmd', 'get_throttled'],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Output format: throttled=0x50000
                    status_line = result.stdout.strip()
                    if 'throttled=' in status_line:
                        hex_value = status_line.split('=')[1]
                        throttle_status = int(hex_value, 16)
                        throttling_info['raw_status'] = hex_value

                        # Decode throttling bits
                        # Bit 0: Under-voltage detected
                        # Bit 1: Arm frequency capped
                        # Bit 2: Currently throttled
                        # Bit 3: Soft temperature limit active
                        # Bit 16: Under-voltage has occurred
                        # Bit 17: Arm frequency capping has occurred
                        # Bit 18: Throttling has occurred
                        # Bit 19: Soft temperature limit has occurred

                        current_issues = []
                        past_issues = []

                        if throttle_status & 0x1:
                            current_issues.append("Under-voltage detected")
                        if throttle_status & 0x2:
                            current_issues.append("ARM frequency capped")
                        if throttle_status & 0x4:
                            current_issues.append("Currently throttled")
                        if throttle_status & 0x8:
                            current_issues.append("Soft temperature limit active")

                        if throttle_status & 0x10000:
                            past_issues.append("Under-voltage occurred")
                        if throttle_status & 0x20000:
                            past_issues.append("ARM frequency capping occurred")
                        if throttle_status & 0x40000:
                            past_issues.append("Throttling occurred")
                        if throttle_status & 0x80000:
                            past_issues.append("Soft temperature limit occurred")

                        throttling_info['current_issues'] = current_issues
                        throttling_info['past_issues'] = past_issues
                        throttling_info['is_throttled'] = len(current_issues) > 0

            except Exception as e:
                self.logger.debug(f"vcgencmd throttling check failed: {e}")

            return throttling_info

        except Exception as e:
            self.logger.error(f"Error checking thermal throttling: {e}")
            return {"error": str(e)}

    @staticmethod
    def _get_temperature_status(temp: float, high_thresh: float = None, critical_thresh: float = None) -> str:
        """Get temperature status based on thresholds"""
        if critical_thresh and temp >= critical_thresh:
            return "Critical"
        elif high_thresh and temp >= high_thresh:
            return "High"
        elif temp >= 80:  # Default critical
            return "Critical"
        elif temp >= 70:  # Default high
            return "High"
        elif temp >= 60:  # Warm
            return "Warm"
        else:
            return "Normal"

    @staticmethod
    def _get_overall_temperature_status(max_temp: float) -> str:
        """Get overall temperature status"""
        if max_temp >= 85:
            return "Critical"
        elif max_temp >= 75:
            return "Hot"
        elif max_temp >= 65:
            return "Warm"
        else:
            return "Normal"


# Example usage
if __name__ == "__main__":
    monitor = TemperatureMonitor()

    print("=== All Temperatures ===")
    all_temps = monitor.get_all_temperatures()
    print(json.dumps(all_temps, indent=2))

    print("\n=== CPU Temperature ===")
    cpu_temp = monitor.get_cpu_temperature()
    print(json.dumps(cpu_temp, indent=2))

    print("\n=== Temperature Alerts ===")
    alerts = monitor.get_temperature_alerts()
    print(json.dumps(alerts, indent=2))

    print("\n=== Thermal Throttling Status ===")
    throttling = monitor.get_thermal_throttling_status()
    print(json.dumps(throttling, indent=2))