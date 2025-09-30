"""
Monitoring Modules - Comprehensive system monitoring components
Adapted from Telegram monitoring system for API backend integration
"""

import asyncio
import logging
import platform
import os
import time
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import psutil
import socket
import re
import json

from enhanced_config import THRESHOLDS, MONITORING_CONFIG, MONITORED_SERVICES
from utils.helpers import safe_execute, run_command, format_bytes, format_time

logger = logging.getLogger('monitoring.modules')


class SystemMonitor:
    """System-level monitoring and coordination"""

    def __init__(self):
        self.logger = logging.getLogger('monitoring.system')
        self.boot_time = datetime.fromtimestamp(psutil.boot_time())
        self.hostname = socket.gethostname()
        self.pi_model = None
        self._cache = {}
        self._cache_duration = 30

    async def initialize(self) -> bool:
        """Initialize system monitor"""
        try:
            self.logger.info("🚀 Initializing System Monitor...")
            self.pi_model = await self._detect_pi_model()
            self.logger.info("✅ System Monitor initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ System Monitor initialization failed: {e}")
            return False

    @safe_execute
    async def _detect_pi_model(self) -> str:
        """Detect Raspberry Pi model"""
        try:
            if os.path.exists('/proc/cpuinfo'):
                with open('/proc/cpuinfo', 'r') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if line.startswith('Model'):
                            return line.split(':', 1)[1].strip()
            return "Unknown Raspberry Pi"
        except:
            return "Unknown System"

    @safe_execute
    async def get_basic_metrics(self) -> Dict[str, Any]:
        """Get basic system metrics"""
        try:
            uptime = (datetime.now() - self.boot_time).total_seconds()
            
            return {
                'hostname': self.hostname,
                'pi_model': self.pi_model,
                'uptime_seconds': int(uptime),
                'boot_time': self.boot_time.isoformat(),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting basic metrics: {e}")
            return {}


class CPUMonitor:
    """CPU monitoring and metrics collection"""

    def __init__(self):
        self.logger = logging.getLogger('monitoring.cpu')
        self._last_cpu_times = None
        self._cpu_history = []

    async def initialize(self) -> bool:
        """Initialize CPU monitor"""
        try:
            self.logger.info("🚀 Initializing CPU Monitor...")
            # Get initial CPU times
            self._last_cpu_times = psutil.cpu_times()
            self.logger.info("✅ CPU Monitor initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ CPU Monitor initialization failed: {e}")
            return False

    @safe_execute
    async def get_cpu_metrics(self) -> Dict[str, Any]:
        """Get comprehensive CPU metrics"""
        try:
            metrics = {}
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics['usage_percent'] = cpu_percent
            
            # Per-core usage
            cpu_per_core = psutil.cpu_percent(percpu=True)
            metrics['per_core_usage'] = cpu_per_core
            
            # CPU frequency
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                metrics['frequency_current'] = cpu_freq.current
                metrics['frequency_min'] = cpu_freq.min
                metrics['frequency_max'] = cpu_freq.max
            
            # CPU times
            cpu_times = psutil.cpu_times()
            metrics['times'] = {
                'user': cpu_times.user,
                'system': cpu_times.system,
                'idle': cpu_times.idle,
                'iowait': getattr(cpu_times, 'iowait', 0),
                'irq': getattr(cpu_times, 'irq', 0),
                'softirq': getattr(cpu_times, 'softirq', 0)
            }
            
            # CPU count
            metrics['cores_physical'] = psutil.cpu_count(logical=False)
            metrics['cores_logical'] = psutil.cpu_count(logical=True)
            
            # Update history
            self._cpu_history.append({
                'timestamp': datetime.utcnow(),
                'usage': cpu_percent
            })
            
            # Keep only last 100 entries
            if len(self._cpu_history) > 100:
                self._cpu_history = self._cpu_history[-100:]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting CPU metrics: {e}")
            return {}


class MemoryMonitor:
    """Memory monitoring and metrics collection"""

    def __init__(self):
        self.logger = logging.getLogger('monitoring.memory')
        self._memory_history = []

    async def initialize(self) -> bool:
        """Initialize memory monitor"""
        try:
            self.logger.info("🚀 Initializing Memory Monitor...")
            self.logger.info("✅ Memory Monitor initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Memory Monitor initialization failed: {e}")
            return False

    @safe_execute
    async def get_memory_info(self) -> Dict[str, Any]:
        """Get comprehensive memory information"""
        try:
            # Virtual memory
            memory = psutil.virtual_memory()
            
            # Swap memory
            swap = psutil.swap_memory()
            
            metrics = {
                'virtual': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'free': memory.free,
                    'percent': memory.percent,
                    'buffers': getattr(memory, 'buffers', 0),
                    'cached': getattr(memory, 'cached', 0),
                    'shared': getattr(memory, 'shared', 0)
                },
                'swap': {
                    'total': swap.total,
                    'used': swap.used,
                    'free': swap.free,
                    'percent': swap.percent,
                    'sin': swap.sin,
                    'sout': swap.sout
                },
                'percent': memory.percent  # For compatibility
            }
            
            # Update history
            self._memory_history.append({
                'timestamp': datetime.utcnow(),
                'usage': memory.percent
            })
            
            # Keep only last 100 entries
            if len(self._memory_history) > 100:
                self._memory_history = self._memory_history[-100:]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting memory info: {e}")
            return {}


class DiskMonitor:
    """Disk monitoring and metrics collection"""

    def __init__(self):
        self.logger = logging.getLogger('monitoring.disk')
        self._disk_history = []

    async def initialize(self) -> bool:
        """Initialize disk monitor"""
        try:
            self.logger.info("🚀 Initializing Disk Monitor...")
            self.logger.info("✅ Disk Monitor initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Disk Monitor initialization failed: {e}")
            return False

    @safe_execute
    async def get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage information"""
        try:
            disk_usage = {}
            
            # Get all disk partitions
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    disk_usage[partition.mountpoint] = {
                        'device': partition.device,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': (usage.used / usage.total) * 100
                    }
                except PermissionError:
                    continue
                except Exception as e:
                    self.logger.warning(f"Error getting usage for {partition.mountpoint}: {e}")
                    continue
            
            # Get disk I/O statistics
            disk_io = psutil.disk_io_counters()
            if disk_io:
                disk_usage['io_stats'] = {
                    'read_bytes': disk_io.read_bytes,
                    'write_bytes': disk_io.write_bytes,
                    'read_count': disk_io.read_count,
                    'write_count': disk_io.write_count,
                    'read_time': disk_io.read_time,
                    'write_time': disk_io.write_time
                }
            
            return disk_usage
            
        except Exception as e:
            self.logger.error(f"Error getting disk usage: {e}")
            return {}


class NetworkMonitor:
    """Network monitoring and connectivity testing"""

    def __init__(self):
        self.logger = logging.getLogger('monitoring.network')
        self._network_history = []

    async def initialize(self) -> bool:
        """Initialize network monitor"""
        try:
            self.logger.info("🚀 Initializing Network Monitor...")
            self.logger.info("✅ Network Monitor initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Network Monitor initialization failed: {e}")
            return False

    @safe_execute
    async def check_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity"""
        try:
            connectivity = {
                'timestamp': datetime.utcnow().isoformat(),
                'interfaces': {},
                'internet_connected': False,
                'dns_working': False,
                'ping_results': {}
            }
            
            # Check interfaces
            net_if_stats = psutil.net_if_stats()
            for interface, stats in net_if_stats.items():
                if interface != 'lo':  # Skip loopback
                    connectivity['interfaces'][interface] = {
                        'is_up': stats.isup,
                        'speed': stats.speed,
                        'mtu': stats.mtu
                    }
            
            # Test internet connectivity
            try:
                proc = await asyncio.create_subprocess_exec(
                    'ping', '-c', '1', '-W', '3', '8.8.8.8',
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await asyncio.wait_for(proc.wait(), timeout=5)
                connectivity['internet_connected'] = proc.returncode == 0
            except:
                connectivity['internet_connected'] = False
            
            # Test DNS
            try:
                proc = await asyncio.create_subprocess_exec(
                    'nslookup', 'google.com',
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await asyncio.wait_for(proc.wait(), timeout=5)
                connectivity['dns_working'] = proc.returncode == 0
            except:
                connectivity['dns_working'] = False
            
            return connectivity
            
        except Exception as e:
            self.logger.error(f"Error checking connectivity: {e}")
            return {'error': str(e)}


class ProcessMonitor:
    """Process monitoring and management"""

    def __init__(self):
        self.logger = logging.getLogger('monitoring.process')

    async def initialize(self) -> bool:
        """Initialize process monitor"""
        try:
            self.logger.info("🚀 Initializing Process Monitor...")
            self.logger.info("✅ Process Monitor initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Process Monitor initialization failed: {e}")
            return False

    @safe_execute
    async def get_process_summary(self) -> Dict[str, Any]:
        """Get process summary"""
        try:
            processes = list(psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent']))
            
            status_counts = {}
            total_processes = len(processes)
            
            for proc in processes:
                try:
                    status = proc.info['status']
                    status_counts[status] = status_counts.get(status, 0) + 1
                except:
                    continue
            
            # Get top CPU and memory consumers
            cpu_top = sorted(processes, key=lambda p: p.info.get('cpu_percent', 0), reverse=True)[:5]
            memory_top = sorted(processes, key=lambda p: p.info.get('memory_percent', 0), reverse=True)[:5]
            
            return {
                'total': total_processes,
                'by_status': status_counts,
                'top_cpu': [{
                    'pid': p.info['pid'],
                    'name': p.info['name'],
                    'cpu_percent': p.info.get('cpu_percent', 0)
                } for p in cpu_top],
                'top_memory': [{
                    'pid': p.info['pid'],
                    'name': p.info['name'],
                    'memory_percent': p.info.get('memory_percent', 0)
                } for p in memory_top]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting process summary: {e}")
            return {}


class ServiceMonitor:
    """System service monitoring"""

    def __init__(self):
        self.logger = logging.getLogger('monitoring.service')
        self.monitored_services = MONITORED_SERVICES

    async def initialize(self) -> bool:
        """Initialize service monitor"""
        try:
            self.logger.info("🚀 Initializing Service Monitor...")
            self.logger.info("✅ Service Monitor initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Service Monitor initialization failed: {e}")
            return False

    @safe_execute
    async def get_service_metrics(self) -> Dict[str, Any]:
        """Get service status metrics"""
        try:
            service_status = {}
            
            for service_name in self.monitored_services:
                try:
                    # Use systemctl to check service status
                    proc = await asyncio.create_subprocess_exec(
                        'systemctl', 'is-active', service_name,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await proc.communicate()
                    
                    status = stdout.decode().strip()
                    service_status[service_name] = {
                        'active': status == 'active',
                        'status': status
                    }
                    
                except Exception as e:
                    service_status[service_name] = {
                        'active': False,
                        'status': 'unknown',
                        'error': str(e)
                    }
            
            return {'services': service_status}
            
        except Exception as e:
            self.logger.error(f"Error getting service metrics: {e}")
            return {}


class TemperatureMonitor:
    """Temperature monitoring for Raspberry Pi"""

    def __init__(self):
        self.logger = logging.getLogger('monitoring.temperature')
        self.thermal_zone_path = '/sys/class/thermal/thermal_zone0/temp'
        self.vcgencmd_available = False

    async def initialize(self) -> bool:
        """Initialize temperature monitor"""
        try:
            self.logger.info("🚀 Initializing Temperature Monitor...")
            
            # Check if vcgencmd is available
            try:
                proc = await asyncio.create_subprocess_exec(
                    'which', 'vcgencmd',
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await proc.wait()
                self.vcgencmd_available = proc.returncode == 0
            except:
                self.vcgencmd_available = False
            
            self.logger.info("✅ Temperature Monitor initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Temperature Monitor initialization failed: {e}")
            return False

    @safe_execute
    async def get_cpu_temperature(self) -> Optional[Dict[str, float]]:
        """Get CPU temperature"""
        try:
            temperature = None
            
            # Try thermal zone first
            if os.path.exists(self.thermal_zone_path):
                try:
                    with open(self.thermal_zone_path, 'r') as f:
                        temp_str = f.read().strip()
                        temperature = float(temp_str) / 1000.0
                except Exception as e:
                    self.logger.warning(f"Error reading thermal zone: {e}")
            
            # Try vcgencmd if thermal zone failed
            if temperature is None and self.vcgencmd_available:
                try:
                    proc = await asyncio.create_subprocess_exec(
                        'vcgencmd', 'measure_temp',
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await proc.communicate()
                    
                    if proc.returncode == 0:
                        output = stdout.decode().strip()
                        match = re.search(r'temp=([0-9.]+)', output)
                        if match:
                            temperature = float(match.group(1))
                except Exception as e:
                    self.logger.warning(f"Error using vcgencmd: {e}")
            
            if temperature is not None:
                return {
                    'celsius': temperature,
                    'fahrenheit': (temperature * 9/5) + 32
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting CPU temperature: {e}")
            return None


class SecurityMonitor:
    """Security monitoring and threat detection"""

    def __init__(self):
        self.logger = logging.getLogger('monitoring.security')
        self._last_auth_check = None
        self._failed_logins = []

    async def initialize(self) -> bool:
        """Initialize security monitor"""
        try:
            self.logger.info("🚀 Initializing Security Monitor...")
            self.logger.info("✅ Security Monitor initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Security Monitor initialization failed: {e}")
            return False

    @safe_execute
    async def get_security_metrics(self) -> Dict[str, Any]:
        """Get security-related metrics"""
        try:
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'failed_logins_24h': 0,
                'ssh_connections': 0,
                'sudo_attempts': 0
            }
            
            # Check for failed login attempts in auth.log
            try:
                if os.path.exists('/var/log/auth.log'):
                    # Count failed logins in last 24 hours
                    yesterday = datetime.now() - timedelta(days=1)
                    
                    proc = await asyncio.create_subprocess_exec(
                        'grep', '-c', 'Failed password', '/var/log/auth.log',
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.DEVNULL
                    )
                    stdout, _ = await proc.communicate()
                    
                    if proc.returncode == 0:
                        metrics['failed_logins_24h'] = int(stdout.decode().strip())
            except:
                pass
            
            # Check active SSH connections
            try:
                connections = psutil.net_connections(kind='inet')
                ssh_count = sum(1 for conn in connections 
                              if conn.laddr.port == 22 and conn.status == psutil.CONN_ESTABLISHED)
                metrics['ssh_connections'] = ssh_count
            except:
                pass
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting security metrics: {e}")
            return {}


class AlertManager:
    """Alert management and threshold monitoring"""

    def __init__(self):
        self.logger = logging.getLogger('monitoring.alerts')
        self._alert_history = {}
        self._last_alerts = {}

    async def initialize(self) -> bool:
        """Initialize alert manager"""
        try:
            self.logger.info("🚀 Initializing Alert Manager...")
            self.logger.info("✅ Alert Manager initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Alert Manager initialization failed: {e}")
            return False

    async def check_all_alerts(self, modules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check all monitoring modules for alert conditions"""
        alerts = []
        
        try:
            # CPU alerts
            if 'cpu' in modules:
                cpu_alerts = await self._check_cpu_alerts(modules['cpu'])
                alerts.extend(cpu_alerts)
            
            # Memory alerts
            if 'memory' in modules:
                memory_alerts = await self._check_memory_alerts(modules['memory'])
                alerts.extend(memory_alerts)
            
            # Disk alerts
            if 'disk' in modules:
                disk_alerts = await self._check_disk_alerts(modules['disk'])
                alerts.extend(disk_alerts)
            
            # Temperature alerts
            if 'temperature' in modules:
                temp_alerts = await self._check_temperature_alerts(modules['temperature'])
                alerts.extend(temp_alerts)
            
            # Network alerts
            if 'network' in modules:
                network_alerts = await self._check_network_alerts(modules['network'])
                alerts.extend(network_alerts)
            
            # Security alerts
            if 'security' in modules:
                security_alerts = await self._check_security_alerts(modules['security'])
                alerts.extend(security_alerts)
            
            # Filter out duplicate alerts (cooldown period)
            filtered_alerts = self._filter_duplicate_alerts(alerts)
            
            return filtered_alerts
            
        except Exception as e:
            self.logger.error(f"Error checking alerts: {e}")
            return []

    async def _check_cpu_alerts(self, cpu_monitor) -> List[Dict[str, Any]]:
        """Check CPU-related alerts"""
        alerts = []
        
        try:
            cpu_metrics = await cpu_monitor.get_cpu_metrics()
            usage = cpu_metrics.get('usage_percent', 0)
            
            if usage > THRESHOLDS.cpu_usage['danger']:
                alerts.append({
                    'type': 'cpu_usage',
                    'severity': 'critical',
                    'message': f'CPU usage critical: {usage:.1f}%',
                    'value': usage,
                    'threshold': THRESHOLDS.cpu_usage['danger']
                })
            elif usage > THRESHOLDS.cpu_usage['critical']:
                alerts.append({
                    'type': 'cpu_usage',
                    'severity': 'high',
                    'message': f'CPU usage high: {usage:.1f}%',
                    'value': usage,
                    'threshold': THRESHOLDS.cpu_usage['critical']
                })
            
        except Exception as e:
            self.logger.error(f"Error checking CPU alerts: {e}")
        
        return alerts

    async def _check_memory_alerts(self, memory_monitor) -> List[Dict[str, Any]]:
        """Check memory-related alerts"""
        alerts = []
        
        try:
            memory_info = await memory_monitor.get_memory_info()
            usage = memory_info.get('percent', 0)
            
            if usage > THRESHOLDS.memory_usage['danger']:
                alerts.append({
                    'type': 'memory_usage',
                    'severity': 'critical',
                    'message': f'Memory usage critical: {usage:.1f}%',
                    'value': usage,
                    'threshold': THRESHOLDS.memory_usage['danger']
                })
            elif usage > THRESHOLDS.memory_usage['critical']:
                alerts.append({
                    'type': 'memory_usage',
                    'severity': 'high',
                    'message': f'Memory usage high: {usage:.1f}%',
                    'value': usage,
                    'threshold': THRESHOLDS.memory_usage['critical']
                })
            
        except Exception as e:
            self.logger.error(f"Error checking memory alerts: {e}")
        
        return alerts

    async def _check_disk_alerts(self, disk_monitor) -> List[Dict[str, Any]]:
        """Check disk-related alerts"""
        alerts = []
        
        try:
            disk_usage = await disk_monitor.get_disk_usage()
            
            for mountpoint, info in disk_usage.items():
                if mountpoint == 'io_stats':
                    continue
                
                usage = info.get('percent', 0)
                
                if usage > THRESHOLDS.disk_usage['danger']:
                    alerts.append({
                        'type': 'disk_usage',
                        'severity': 'critical',
                        'message': f'Disk usage critical on {mountpoint}: {usage:.1f}%',
                        'value': usage,
                        'threshold': THRESHOLDS.disk_usage['danger'],
                        'mountpoint': mountpoint
                    })
                elif usage > THRESHOLDS.disk_usage['critical']:
                    alerts.append({
                        'type': 'disk_usage',
                        'severity': 'high',
                        'message': f'Disk usage high on {mountpoint}: {usage:.1f}%',
                        'value': usage,
                        'threshold': THRESHOLDS.disk_usage['critical'],
                        'mountpoint': mountpoint
                    })
            
        except Exception as e:
            self.logger.error(f"Error checking disk alerts: {e}")
        
        return alerts

    async def _check_temperature_alerts(self, temp_monitor) -> List[Dict[str, Any]]:
        """Check temperature-related alerts"""
        alerts = []
        
        try:
            temp_info = await temp_monitor.get_cpu_temperature()
            
            if temp_info:
                temp = temp_info.get('celsius', 0)
                
                if temp > THRESHOLDS.cpu_temp['danger']:
                    alerts.append({
                        'type': 'cpu_temperature',
                        'severity': 'critical',
                        'message': f'CPU temperature critical: {temp:.1f}°C',
                        'value': temp,
                        'threshold': THRESHOLDS.cpu_temp['danger']
                    })
                elif temp > THRESHOLDS.cpu_temp['critical']:
                    alerts.append({
                        'type': 'cpu_temperature',
                        'severity': 'high',
                        'message': f'CPU temperature high: {temp:.1f}°C',
                        'value': temp,
                        'threshold': THRESHOLDS.cpu_temp['critical']
                    })
            
        except Exception as e:
            self.logger.error(f"Error checking temperature alerts: {e}")
        
        return alerts

    async def _check_network_alerts(self, network_monitor) -> List[Dict[str, Any]]:
        """Check network-related alerts"""
        alerts = []
        
        try:
            connectivity = await network_monitor.check_connectivity()
            
            if not connectivity.get('internet_connected', True):
                alerts.append({
                    'type': 'network_connectivity',
                    'severity': 'high',
                    'message': 'Internet connectivity lost',
                    'value': False,
                    'threshold': True
                })
            
            if not connectivity.get('dns_working', True):
                alerts.append({
                    'type': 'dns_resolution',
                    'severity': 'medium',
                    'message': 'DNS resolution not working',
                    'value': False,
                    'threshold': True
                })
            
        except Exception as e:
            self.logger.error(f"Error checking network alerts: {e}")
        
        return alerts

    async def _check_security_alerts(self, security_monitor) -> List[Dict[str, Any]]:
        """Check security-related alerts"""
        alerts = []
        
        try:
            security_metrics = await security_monitor.get_security_metrics()
            
            failed_logins = security_metrics.get('failed_logins_24h', 0)
            if failed_logins > 10:
                alerts.append({
                    'type': 'security_failed_logins',
                    'severity': 'high',
                    'message': f'High number of failed logins: {failed_logins} in 24h',
                    'value': failed_logins,
                    'threshold': 10
                })
            
        except Exception as e:
            self.logger.error(f"Error checking security alerts: {e}")
        
        return alerts

    def _filter_duplicate_alerts(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out duplicate alerts based on cooldown period"""
        filtered_alerts = []
        current_time = datetime.utcnow()
        
        for alert in alerts:
            alert_key = f"{alert['type']}_{alert.get('mountpoint', '')}"
            
            # Check if this alert type is in cooldown
            last_alert_time = self._last_alerts.get(alert_key)
            
            if (last_alert_time is None or 
                (current_time - last_alert_time).total_seconds() > MONITORING_CONFIG.alert_cooldown):
                
                # Add timestamp to alert
                alert['timestamp'] = current_time.isoformat()
                
                filtered_alerts.append(alert)
                self._last_alerts[alert_key] = current_time
        
        return filtered_alerts