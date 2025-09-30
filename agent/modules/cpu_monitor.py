"""
CPU Monitor Module
Monitors CPU usage, frequency, temperature, and processes
"""

import psutil
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import threading
from collections import deque
import statistics


class CPUMonitor:
    def __init__(self, history_size: int = 300):  # 5 minutes of history at 1-second intervals
        self.logger = logging.getLogger(__name__)
        self.history_size = history_size
        self.cpu_history = deque(maxlen=history_size)
        self.per_cpu_history = {}
        self._monitoring = False
        self._monitor_thread = None
        self._lock = threading.Lock()

    def get_cpu_info(self) -> Dict[str, Any]:
        """Get comprehensive CPU information"""
        try:
            cpu_info = {}

            # Basic CPU information
            cpu_info['cores'] = {
                'physical': psutil.cpu_count(logical=False),
                'logical': psutil.cpu_count(logical=True)
            }

            # CPU frequency
            freq = psutil.cpu_freq()
            if freq:
                cpu_info['frequency'] = {
                    'current': f"{freq.current:.2f} MHz",
                    'min': f"{freq.min:.2f} MHz" if freq.min else "Unknown",
                    'max': f"{freq.max:.2f} MHz" if freq.max else "Unknown"
                }

            # CPU times
            cpu_times = psutil.cpu_times()
            total_time = sum(cpu_times)
            cpu_info['times'] = {
                'user': f"{(cpu_times.user / total_time) * 100:.2f}%",
                'system': f"{(cpu_times.system / total_time) * 100:.2f}%",
                'idle': f"{(cpu_times.idle / total_time) * 100:.2f}%",
                'iowait': f"{(cpu_times.iowait / total_time) * 100:.2f}%" if hasattr(cpu_times, 'iowait') else "N/A",
                'irq': f"{(cpu_times.irq / total_time) * 100:.2f}%" if hasattr(cpu_times, 'irq') else "N/A",
                'softirq': f"{(cpu_times.softirq / total_time) * 100:.2f}%" if hasattr(cpu_times, 'softirq') else "N/A"
            }

            # CPU stats
            cpu_stats = psutil.cpu_stats()
            cpu_info['stats'] = {
                'ctx_switches': cpu_stats.ctx_switches,
                'interrupts': cpu_stats.interrupts,
                'soft_interrupts': cpu_stats.soft_interrupts,
                'syscalls': cpu_stats.syscalls if hasattr(cpu_stats, 'syscalls') else "N/A"
            }

            return cpu_info

        except Exception as e:
            self.logger.error(f"Error getting CPU info: {e}")
            return {"error": str(e)}

    def get_cpu_usage(self, interval: float = 1.0, per_cpu: bool = False) -> Dict[str, Any]:
        """Get current CPU usage"""
        try:
            timestamp = datetime.now().isoformat()

            if per_cpu:
                # Per-CPU usage
                per_cpu_percent = psutil.cpu_percent(interval=interval, percpu=True)
                return {
                    'timestamp': timestamp,
                    'total': sum(per_cpu_percent) / len(per_cpu_percent),
                    'per_cpu': [f"{cpu:.2f}%" for cpu in per_cpu_percent],
                    'cores': len(per_cpu_percent)
                }
            else:
                # Total CPU usage
                cpu_percent = psutil.cpu_percent(interval=interval)
                return {
                    'timestamp': timestamp,
                    'usage_percent': cpu_percent,
                    'status': self._get_cpu_status(cpu_percent)
                }

        except Exception as e:
            self.logger.error(f"Error getting CPU usage: {e}")
            return {"error": str(e)}

    def get_cpu_load_average(self) -> Dict[str, Any]:
        """Get CPU load average (Unix systems only)"""
        try:
            import os
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
                cpu_count = psutil.cpu_count()

                return {
                    'timestamp': datetime.now().isoformat(),
                    'load_average': {
                        '1min': load_avg[0],
                        '5min': load_avg[1],
                        '15min': load_avg[2]
                    },
                    'cpu_count': cpu_count,
                    'load_percentage': {
                        '1min': f"{(load_avg[0] / cpu_count) * 100:.2f}%",
                        '5min': f"{(load_avg[1] / cpu_count) * 100:.2f}%",
                        '15min': f"{(load_avg[2] / cpu_count) * 100:.2f}%"
                    },
                    'status': self._get_load_status(load_avg[1], cpu_count)
                }
            else:
                return {"error": "Load average not available on this system"}

        except Exception as e:
            self.logger.error(f"Error getting load average: {e}")
            return {"error": str(e)}

    def get_top_cpu_processes(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get top CPU consuming processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username']):
                try:
                    proc_info = proc.info
                    # Get actual CPU percent with a short interval
                    proc_info['cpu_percent'] = proc.cpu_percent()
                    if proc_info['cpu_percent'] is not None and proc_info['cpu_percent'] > 0:
                        processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort by CPU usage and return top N
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            return processes[:count]

        except Exception as e:
            self.logger.error(f"Error getting top CPU processes: {e}")
            return [{"error": str(e)}]

    def start_monitoring(self, interval: float = 1.0):
        """Start continuous CPU monitoring"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        self.logger.info("CPU monitoring started")

    def stop_monitoring(self):
        """Stop continuous CPU monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.logger.info("CPU monitoring stopped")

    def _monitor_loop(self, interval: float):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                # Get overall CPU usage
                cpu_percent = psutil.cpu_percent(interval=interval)
                per_cpu_percent = psutil.cpu_percent(percpu=True)

                timestamp = datetime.now()

                with self._lock:
                    # Store overall CPU usage
                    self.cpu_history.append({
                        'timestamp': timestamp,
                        'usage': cpu_percent
                    })

                    # Store per-CPU usage
                    for i, usage in enumerate(per_cpu_percent):
                        if i not in self.per_cpu_history:
                            self.per_cpu_history[i] = deque(maxlen=self.history_size)
                        self.per_cpu_history[i].append({
                            'timestamp': timestamp,
                            'usage': usage
                        })

            except Exception as e:
                self.logger.error(f"Error in CPU monitoring loop: {e}")
                time.sleep(interval)

    def get_cpu_history(self, minutes: int = 5) -> Dict[str, Any]:
        """Get CPU usage history"""
        try:
            with self._lock:
                if not self.cpu_history:
                    return {"error": "No history available. Start monitoring first."}

                cutoff_time = datetime.now() - timedelta(minutes=minutes)
                recent_history = [
                    entry for entry in self.cpu_history
                    if entry['timestamp'] > cutoff_time
                ]

                if not recent_history:
                    return {"error": f"No data available for the last {minutes} minutes"}

                # Calculate statistics
                usage_values = [entry['usage'] for entry in recent_history]

                return {
                    'period_minutes': minutes,
                    'data_points': len(recent_history),
                    'statistics': {
                        'average': statistics.mean(usage_values),
                        'min': min(usage_values),
                        'max': max(usage_values),
                        'median': statistics.median(usage_values)
                    },
                    'timeline': [
                        {
                            'timestamp': entry['timestamp'].isoformat(),
                            'usage': entry['usage']
                        }
                        for entry in recent_history[-60:]  # Last 60 data points
                    ]
                }

        except Exception as e:
            self.logger.error(f"Error getting CPU history: {e}")
            return {"error": str(e)}

    def get_cpu_alerts(self, warning_threshold: float = 70, critical_threshold: float = 85) -> Dict[str, Any]:
        """Check for CPU usage alerts"""
        try:
            current_usage = psutil.cpu_percent(interval=1)

            # Check load average if available
            load_alert = None
            try:
                import os
                if hasattr(os, 'getloadavg'):
                    load_avg = os.getloadavg()[1]  # 5-minute average
                    cpu_count = psutil.cpu_count()
                    load_percent = (load_avg / cpu_count) * 100

                    if load_percent > critical_threshold:
                        load_alert = {
                            'level': 'critical',
                            'message': f"High load average: {load_avg:.2f} ({load_percent:.1f}% of CPU capacity)"
                        }
                    elif load_percent > warning_threshold:
                        load_alert = {
                            'level': 'warning',
                            'message': f"Elevated load average: {load_avg:.2f} ({load_percent:.1f}% of CPU capacity)"
                        }
            except:
                pass

            # CPU usage alert
            usage_alert = None
            if current_usage > critical_threshold:
                usage_alert = {
                    'level': 'critical',
                    'message': f"Critical CPU usage: {current_usage:.1f}%"
                }
            elif current_usage > warning_threshold:
                usage_alert = {
                    'level': 'warning',
                    'message': f"High CPU usage: {current_usage:.1f}%"
                }

            alerts = []
            if usage_alert:
                alerts.append(usage_alert)
            if load_alert:
                alerts.append(load_alert)

            return {
                'timestamp': datetime.now().isoformat(),
                'current_usage': current_usage,
                'thresholds': {
                    'warning': warning_threshold,
                    'critical': critical_threshold
                },
                'alerts': alerts,
                'alert_count': len(alerts)
            }

        except Exception as e:
            self.logger.error(f"Error checking CPU alerts: {e}")
            return {"error": str(e)}

    def get_cpu_temperature(self) -> Dict[str, Any]:
        """Get CPU temperature (if available)"""
        try:
            temps = psutil.sensors_temperatures()
            cpu_temps = []

            # Look for CPU temperature sensors
            for name, entries in temps.items():
                if 'cpu' in name.lower() or 'core' in name.lower() or 'proc' in name.lower():
                    for entry in entries:
                        cpu_temps.append({
                            'sensor': f"{name}_{entry.label}" if entry.label else name,
                            'temperature': entry.current,
                            'high': entry.high if entry.high else None,
                            'critical': entry.critical if entry.critical else None
                        })

            if cpu_temps:
                avg_temp = sum(temp['temperature'] for temp in cpu_temps) / len(cpu_temps)
                max_temp = max(temp['temperature'] for temp in cpu_temps)

                return {
                    'timestamp': datetime.now().isoformat(),
                    'sensors': cpu_temps,
                    'average_temperature': avg_temp,
                    'max_temperature': max_temp,
                    'status': self._get_temperature_status(max_temp)
                }
            else:
                return {"error": "No CPU temperature sensors found"}

        except Exception as e:
            self.logger.error(f"Error getting CPU temperature: {e}")
            return {"error": str(e)}

    @staticmethod
    def _get_cpu_status(usage: float) -> str:
        """Get CPU status based on usage"""
        if usage >= 90:
            return "Critical"
        elif usage >= 70:
            return "High"
        elif usage >= 50:
            return "Moderate"
        else:
            return "Normal"

    @staticmethod
    def _get_load_status(load: float, cpu_count: int) -> str:
        """Get load status based on load average"""
        load_percent = (load / cpu_count) * 100
        if load_percent >= 100:
            return "Overloaded"
        elif load_percent >= 80:
            return "High Load"
        elif load_percent >= 60:
            return "Moderate Load"
        else:
            return "Normal Load"

    @staticmethod
    def _get_temperature_status(temp: float) -> str:
        """Get temperature status"""
        if temp >= 80:
            return "Critical"
        elif temp >= 70:
            return "Hot"
        elif temp >= 60:
            return "Warm"
        else:
            return "Normal"


# Example usage
if __name__ == "__main__":
    monitor = CPUMonitor()

    print("=== CPU Information ===")
    info = monitor.get_cpu_info()
    print(json.dumps(info, indent=2))

    print("\n=== CPU Usage ===")
    usage = monitor.get_cpu_usage(per_cpu=True)
    print(json.dumps(usage, indent=2))

    print("\n=== Load Average ===")
    load = monitor.get_cpu_load_average()
    print(json.dumps(load, indent=2))

    print("\n=== Top CPU Processes ===")
    top_processes = monitor.get_top_cpu_processes(5)
    print(json.dumps(top_processes, indent=2))

    print("\n=== CPU Temperature ===")
    temp = monitor.get_cpu_temperature()
    print(json.dumps(temp, indent=2))

    print("\n=== CPU Alerts ===")
    alerts = monitor.get_cpu_alerts()
    print(json.dumps(alerts, indent=2))