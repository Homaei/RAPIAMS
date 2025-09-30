"""
System Monitor Module
Monitors overall system information including OS, hardware, uptime, and boot details
"""

import psutil
import platform
import socket
import uuid
import subprocess
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json
import os


class SystemMonitor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._boot_time = None
        self._system_info = None

    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            if self._system_info is None:
                self._system_info = self._collect_static_info()

            # Add dynamic info
            dynamic_info = self._collect_dynamic_info()
            return {**self._system_info, **dynamic_info}

        except Exception as e:
            self.logger.error(f"Error collecting system info: {e}")
            return {"error": str(e)}

    def _collect_static_info(self) -> Dict[str, Any]:
        """Collect static system information that doesn't change"""
        info = {}

        # Platform information
        info['platform'] = {
            'system': platform.system(),
            'node': platform.node(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'architecture': platform.architecture()[0],
            'python_version': platform.python_version()
        }

        # Hardware information
        info['hardware'] = self._get_hardware_info()

        # Network information
        info['network'] = self._get_network_info()

        # OS specific information
        info['os_info'] = self._get_os_info()

        return info

    def _collect_dynamic_info(self) -> Dict[str, Any]:
        """Collect dynamic system information"""
        info = {}

        # Uptime information
        info['uptime'] = self._get_uptime_info()

        # Load average (Unix systems)
        if hasattr(os, 'getloadavg'):
            info['load_average'] = {
                '1min': os.getloadavg()[0],
                '5min': os.getloadavg()[1],
                '15min': os.getloadavg()[2]
            }

        # Process count
        info['processes'] = {
            'total': len(psutil.pids()),
            'running': len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'running']),
            'sleeping': len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'sleeping'])
        }

        # Users information
        info['users'] = self._get_active_users()

        return info

    def _get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware information"""
        hardware = {}

        try:
            # CPU information
            hardware['cpu'] = {
                'physical_cores': psutil.cpu_count(logical=False),
                'logical_cores': psutil.cpu_count(logical=True),
                'max_frequency': f"{psutil.cpu_freq().max:.2f} MHz" if psutil.cpu_freq() else "Unknown",
                'min_frequency': f"{psutil.cpu_freq().min:.2f} MHz" if psutil.cpu_freq() else "Unknown"
            }

            # Memory information
            memory = psutil.virtual_memory()
            hardware['memory'] = {
                'total': self._bytes_to_gb(memory.total),
                'type': 'Virtual Memory'
            }

            # Disk information
            hardware['disks'] = []
            for partition in psutil.disk_partitions():
                try:
                    disk_usage = psutil.disk_usage(partition.mountpoint)
                    hardware['disks'].append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'filesystem': partition.fstype,
                        'total': self._bytes_to_gb(disk_usage.total)
                    })
                except PermissionError:
                    continue

        except Exception as e:
            self.logger.error(f"Error getting hardware info: {e}")
            hardware['error'] = str(e)

        return hardware

    def _get_network_info(self) -> Dict[str, Any]:
        """Get network configuration information"""
        network = {}

        try:
            # Hostname and IP
            network['hostname'] = socket.gethostname()
            network['fqdn'] = socket.getfqdn()

            # Network interfaces
            network['interfaces'] = []
            for interface, addrs in psutil.net_if_addrs().items():
                interface_info = {'name': interface, 'addresses': []}
                for addr in addrs:
                    if addr.family == socket.AF_INET:  # IPv4
                        interface_info['addresses'].append({
                            'type': 'IPv4',
                            'address': addr.address,
                            'netmask': addr.netmask
                        })
                    elif addr.family == socket.AF_INET6:  # IPv6
                        interface_info['addresses'].append({
                            'type': 'IPv6',
                            'address': addr.address
                        })
                if interface_info['addresses']:
                    network['interfaces'].append(interface_info)

            # MAC address
            network['mac_address'] = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                                             for elements in range(0, 2*6, 2)][::-1])

        except Exception as e:
            self.logger.error(f"Error getting network info: {e}")
            network['error'] = str(e)

        return network

    def _get_os_info(self) -> Dict[str, Any]:
        """Get OS specific information"""
        os_info = {}

        try:
            # Try to get distribution info (Linux)
            if platform.system() == 'Linux':
                try:
                    with open('/etc/os-release', 'r') as f:
                        os_release = {}
                        for line in f:
                            if '=' in line:
                                key, value = line.strip().split('=', 1)
                                os_release[key] = value.strip('"')
                        os_info['distribution'] = os_release
                except:
                    pass

                # Kernel information
                try:
                    os_info['kernel'] = {
                        'version': platform.release(),
                        'architecture': platform.machine()
                    }
                except:
                    pass

            # Environment variables (selected)
            os_info['environment'] = {
                'PATH': os.environ.get('PATH', 'Not available'),
                'HOME': os.environ.get('HOME', 'Not available'),
                'USER': os.environ.get('USER', 'Not available'),
                'SHELL': os.environ.get('SHELL', 'Not available')
            }

        except Exception as e:
            self.logger.error(f"Error getting OS info: {e}")
            os_info['error'] = str(e)

        return os_info

    def _get_uptime_info(self) -> Dict[str, Any]:
        """Get system uptime information"""
        try:
            if self._boot_time is None:
                self._boot_time = datetime.fromtimestamp(psutil.boot_time())

            uptime_delta = datetime.now() - self._boot_time

            return {
                'boot_time': self._boot_time.isoformat(),
                'uptime_seconds': int(uptime_delta.total_seconds()),
                'uptime_human': self._format_uptime(uptime_delta),
                'current_time': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting uptime info: {e}")
            return {"error": str(e)}

    def _get_active_users(self) -> List[Dict[str, Any]]:
        """Get information about active users"""
        users = []
        try:
            for user in psutil.users():
                users.append({
                    'name': user.name,
                    'terminal': user.terminal,
                    'host': user.host,
                    'started': datetime.fromtimestamp(user.started).isoformat() if user.started else None
                })
        except Exception as e:
            self.logger.error(f"Error getting users info: {e}")
            users = [{"error": str(e)}]
        return users

    def get_system_performance_summary(self) -> Dict[str, Any]:
        """Get a quick performance summary"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()

            # Disk usage (root partition)
            disk = psutil.disk_usage('/')

            # Load average (if available)
            load_avg = None
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()

            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': (disk.used / disk.total) * 100,
                'load_average': {
                    '1min': load_avg[0] if load_avg else None,
                    '5min': load_avg[1] if load_avg else None,
                    '15min': load_avg[2] if load_avg else None
                } if load_avg else None,
                'processes_total': len(psutil.pids())
            }
        except Exception as e:
            self.logger.error(f"Error getting performance summary: {e}")
            return {"error": str(e)}

    def get_system_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            performance = self.get_system_performance_summary()

            # Determine health status based on metrics
            health_issues = []
            health_score = 100

            if performance.get('cpu_percent', 0) > 80:
                health_issues.append("High CPU usage")
                health_score -= 20

            if performance.get('memory_percent', 0) > 85:
                health_issues.append("High memory usage")
                health_score -= 20

            if performance.get('disk_percent', 0) > 90:
                health_issues.append("High disk usage")
                health_score -= 30

            load_avg = performance.get('load_average', {})
            if load_avg and load_avg.get('5min', 0) > psutil.cpu_count():
                health_issues.append("High system load")
                health_score -= 15

            # Overall status
            if health_score >= 80:
                status = "Healthy"
            elif health_score >= 60:
                status = "Warning"
            elif health_score >= 40:
                status = "Critical"
            else:
                status = "Emergency"

            return {
                'status': status,
                'health_score': max(0, health_score),
                'issues': health_issues,
                'metrics': performance,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting health status: {e}")
            return {
                "status": "Unknown",
                "health_score": 0,
                "error": str(e)
            }

    def execute_system_command(self, command: str) -> Dict[str, Any]:
        """Execute a system command safely"""
        try:
            # Security: Only allow specific safe commands
            allowed_commands = [
                'whoami', 'pwd', 'date', 'uptime', 'uname -a',
                'df -h', 'free -h', 'ps aux', 'netstat -tuln',
                'systemctl status', 'journalctl --no-pager -n 20'
            ]

            if command not in allowed_commands:
                return {
                    "error": "Command not allowed",
                    "allowed_commands": allowed_commands
                }

            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=30
            )

            return {
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "timestamp": datetime.now().isoformat()
            }

        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except Exception as e:
            self.logger.error(f"Error executing command: {e}")
            return {"error": str(e)}

    @staticmethod
    def _bytes_to_gb(bytes_value: int) -> str:
        """Convert bytes to GB"""
        gb = bytes_value / (1024**3)
        return f"{gb:.2f} GB"

    @staticmethod
    def _format_uptime(uptime_delta: timedelta) -> str:
        """Format uptime in human readable format"""
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if days:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

        return ", ".join(parts) if parts else f"{seconds} seconds"


# Example usage
if __name__ == "__main__":
    monitor = SystemMonitor()

    print("=== System Information ===")
    info = monitor.get_system_info()
    print(json.dumps(info, indent=2, default=str))

    print("\n=== Performance Summary ===")
    performance = monitor.get_system_performance_summary()
    print(json.dumps(performance, indent=2))

    print("\n=== Health Status ===")
    health = monitor.get_system_health_status()
    print(json.dumps(health, indent=2))