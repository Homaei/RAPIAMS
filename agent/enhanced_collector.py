"""
Enhanced Metrics Collector - Advanced system metrics collection
Adapted from Telegram monitoring system for API backend integration
"""

import asyncio
import logging
import platform
import socket
import subprocess
import os
import psutil
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
import json

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

from utils.helpers import safe_execute, run_command, format_bytes

logger = logging.getLogger('monitoring.collector')


class EnhancedMetricsCollector:
    """Enhanced metrics collector with comprehensive system monitoring"""

    def __init__(self, config, monitoring_modules: Dict[str, Any]):
        """
        Initialize the enhanced metrics collector
        
        Args:
            config: Agent configuration
            monitoring_modules: Dictionary of monitoring module instances
        """
        self.config = config
        self.modules = monitoring_modules
        self.hostname = socket.gethostname()
        self.boot_time = datetime.fromtimestamp(psutil.boot_time())
        self.logger = logger
        
        # Initialize GPIO if available and enabled
        if GPIO_AVAILABLE and self.config.enable_gpio_monitoring:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                self.logger.info("GPIO monitoring enabled")
            except Exception as e:
                self.logger.warning(f"Failed to initialize GPIO: {e}")
                GPIO_AVAILABLE = False
    
    @safe_execute
    async def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information for device registration"""
        try:
            uname = platform.uname()
            
            # Get Raspberry Pi model info
            model_info = await self._get_pi_model_info()
            
            # Get network interfaces
            network_info = await self._get_network_interfaces()
            
            system_info = {
                'hostname': self.hostname,
                'model': model_info.get('model', uname.machine),
                'os_version': f"{uname.system} {uname.release}",
                'kernel_version': uname.version,
                'agent_version': self.config.agent_version,
                'cpu_cores': psutil.cpu_count(),
                'ram_total_mb': psutil.virtual_memory().total // (1024 * 1024),
                'storage_total_gb': psutil.disk_usage('/').total / (1024**3),
                'ip_address': network_info.get('primary_ip'),
                'mac_address': network_info.get('primary_mac'),
                'architecture': uname.machine,
                'python_version': platform.python_version(),
                'boot_time': self.boot_time.isoformat(),
                'interfaces': network_info.get('interfaces', {}),
                'gpio_available': GPIO_AVAILABLE and self.config.enable_gpio_monitoring,
                'gpio_pins': self.config.gpio_pins if GPIO_AVAILABLE else [],
                'monitoring_features': {
                    'detailed_monitoring': self.config.enable_detailed_monitoring,
                    'process_monitoring': self.config.enable_process_monitoring,
                    'service_monitoring': self.config.enable_service_monitoring,
                    'security_monitoring': self.config.enable_security_monitoring,
                    'network_monitoring': self.config.enable_network_monitoring,
                    'gpio_monitoring': self.config.enable_gpio_monitoring and GPIO_AVAILABLE
                }
            }
            
            # Add Raspberry Pi specific info
            if model_info:
                system_info.update(model_info)
            
            return system_info
            
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return {
                'hostname': self.hostname,
                'agent_version': self.config.agent_version,
                'error': str(e)
            }
    
    @safe_execute
    async def _get_pi_model_info(self) -> Dict[str, Any]:
        """Get Raspberry Pi model information"""
        try:
            model_info = {}
            
            # Try to read from /proc/cpuinfo
            if os.path.exists('/proc/cpuinfo'):
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                    
                # Extract model information
                for line in cpuinfo.split('\n'):
                    if line.startswith('Model'):
                        model_info['model'] = line.split(':', 1)[1].strip()
                    elif line.startswith('Hardware'):
                        model_info['hardware'] = line.split(':', 1)[1].strip()
                    elif line.startswith('Revision'):
                        model_info['revision'] = line.split(':', 1)[1].strip()
                    elif line.startswith('Serial'):
                        model_info['serial'] = line.split(':', 1)[1].strip()
            
            # Try to get temperature capability
            if os.path.exists('/sys/class/thermal/thermal_zone0/temp'):
                model_info['temperature_monitoring'] = True
            
            # Check for vcgencmd (VideoCore GPU command)
            try:
                result = subprocess.run(['vcgencmd', 'version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    model_info['vcgencmd_available'] = True
                    model_info['gpu_info'] = result.stdout.strip()
            except:
                model_info['vcgencmd_available'] = False
            
            return model_info
            
        except Exception as e:
            self.logger.error(f"Error getting Pi model info: {e}")
            return {}
    
    @safe_execute
    async def _get_network_interfaces(self) -> Dict[str, Any]:
        """Get network interface information"""
        try:
            interfaces = {}
            primary_ip = None
            primary_mac = None
            
            # Get all network interfaces
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            
            for interface_name, addresses in net_if_addrs.items():
                if interface_name == 'lo':  # Skip loopback
                    continue
                
                interface_info = {
                    'name': interface_name,
                    'addresses': [],
                    'is_up': False,
                    'speed': 0
                }
                
                # Get interface stats
                if interface_name in net_if_stats:
                    stats = net_if_stats[interface_name]
                    interface_info['is_up'] = stats.isup
                    interface_info['speed'] = stats.speed
                    interface_info['mtu'] = stats.mtu
                
                # Process addresses
                for addr in addresses:
                    addr_info = {
                        'family': addr.family.name,
                        'address': addr.address
                    }
                    
                    if addr.netmask:
                        addr_info['netmask'] = addr.netmask
                    if addr.broadcast:
                        addr_info['broadcast'] = addr.broadcast
                    
                    interface_info['addresses'].append(addr_info)
                    
                    # Set primary IP and MAC
                    if addr.family.name == 'AF_INET' and not primary_ip:
                        if interface_name.startswith(('eth', 'wlan', 'en', 'wl')):
                            primary_ip = addr.address
                    elif addr.family.name == 'AF_PACKET' and not primary_mac:
                        if interface_name.startswith(('eth', 'wlan', 'en', 'wl')):
                            primary_mac = addr.address
                
                interfaces[interface_name] = interface_info
            
            # Fallback for primary IP
            if not primary_ip:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    primary_ip = s.getsockname()[0]
                    s.close()
                except:
                    pass
            
            return {
                'interfaces': interfaces,
                'primary_ip': primary_ip,
                'primary_mac': primary_mac
            }
            
        except Exception as e:
            self.logger.error(f"Error getting network interfaces: {e}")
            return {}
    
    async def collect_all_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect comprehensive metrics from all monitoring modules"""
        try:
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'device_id': self.config.device_id,
                'collection_time': None
            }
            
            start_time = time.time()
            
            # Collect basic system metrics
            if 'system' in self.modules:
                system_metrics = await self._collect_system_metrics()
                if system_metrics:
                    metrics.update(system_metrics)
            
            # Collect CPU metrics
            if 'cpu' in self.modules:
                cpu_metrics = await self._collect_cpu_metrics()
                if cpu_metrics:
                    metrics.update(cpu_metrics)
            
            # Collect memory metrics
            if 'memory' in self.modules:
                memory_metrics = await self._collect_memory_metrics()
                if memory_metrics:
                    metrics.update(memory_metrics)
            
            # Collect disk metrics
            if 'disk' in self.modules:
                disk_metrics = await self._collect_disk_metrics()
                if disk_metrics:
                    metrics.update(disk_metrics)
            
            # Collect network metrics
            if 'network' in self.modules and self.config.enable_network_monitoring:
                network_metrics = await self._collect_network_metrics()
                if network_metrics:
                    metrics.update(network_metrics)
            
            # Collect process metrics
            if 'process' in self.modules and self.config.enable_process_monitoring:
                process_metrics = await self._collect_process_metrics()
                if process_metrics:
                    metrics.update(process_metrics)
            
            # Collect service metrics
            if 'service' in self.modules and self.config.enable_service_monitoring:
                service_metrics = await self._collect_service_metrics()
                if service_metrics:
                    metrics.update(service_metrics)
            
            # Collect temperature metrics
            if 'temperature' in self.modules:
                temp_metrics = await self._collect_temperature_metrics()
                if temp_metrics:
                    metrics.update(temp_metrics)
            
            # Collect security metrics
            if 'security' in self.modules and self.config.enable_security_monitoring:
                security_metrics = await self._collect_security_metrics()
                if security_metrics:
                    metrics.update(security_metrics)
            
            # Collect GPIO metrics
            if GPIO_AVAILABLE and self.config.enable_gpio_monitoring and self.config.gpio_pins:
                gpio_metrics = await self._collect_gpio_metrics()
                if gpio_metrics:
                    metrics['gpio_states'] = gpio_metrics
            
            # Collect custom script metrics
            if self.config.custom_scripts:
                custom_metrics = await self._collect_custom_metrics()
                if custom_metrics:
                    metrics['custom_metrics'] = custom_metrics
            
            # Calculate collection time
            collection_time = time.time() - start_time
            metrics['collection_time'] = round(collection_time, 3)
            
            # Add uptime
            uptime = (datetime.now() - self.boot_time).total_seconds()
            metrics['uptime_seconds'] = int(uptime)
            
            # Add load averages
            try:
                load_avg = os.getloadavg()
                metrics['load_avg_1'] = load_avg[0]
                metrics['load_avg_5'] = load_avg[1]
                metrics['load_avg_15'] = load_avg[2]
            except:
                pass
            
            self.logger.debug(f"Collected {len(metrics)} metrics in {collection_time:.3f}s")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return None
    
    @safe_execute
    async def _collect_system_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect system-level metrics"""
        try:
            if hasattr(self.modules['system'], 'get_basic_metrics'):
                return await self.modules['system'].get_basic_metrics()
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
        return None
    
    @safe_execute
    async def _collect_cpu_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect CPU metrics"""
        try:
            metrics = {}
            
            # CPU usage percentage
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics['cpu_percent'] = cpu_percent
            
            # CPU frequency
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                metrics['cpu_frequency'] = cpu_freq.current
                metrics['cpu_freq_min'] = cpu_freq.min
                metrics['cpu_freq_max'] = cpu_freq.max
            
            # CPU count
            metrics['cpu_cores'] = psutil.cpu_count(logical=False)
            metrics['cpu_logical_cores'] = psutil.cpu_count(logical=True)
            
            # Per-CPU usage
            if self.config.enable_detailed_monitoring:
                cpu_percents = psutil.cpu_percent(percpu=True)
                metrics['cpu_per_core'] = cpu_percents
            
            # CPU times
            cpu_times = psutil.cpu_times()
            metrics['cpu_times'] = {
                'user': cpu_times.user,
                'system': cpu_times.system,
                'idle': cpu_times.idle,
                'iowait': getattr(cpu_times, 'iowait', 0),
                'irq': getattr(cpu_times, 'irq', 0),
                'softirq': getattr(cpu_times, 'softirq', 0)
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting CPU metrics: {e}")
            return None
    
    @safe_execute
    async def _collect_memory_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect memory metrics"""
        try:
            metrics = {}
            
            # Virtual memory
            memory = psutil.virtual_memory()
            metrics['memory_used_mb'] = memory.used // (1024 * 1024)
            metrics['memory_available_mb'] = memory.available // (1024 * 1024)
            metrics['memory_total_mb'] = memory.total // (1024 * 1024)
            metrics['memory_percent'] = memory.percent
            metrics['memory_free_mb'] = memory.free // (1024 * 1024)
            metrics['memory_buffers_mb'] = getattr(memory, 'buffers', 0) // (1024 * 1024)
            metrics['memory_cached_mb'] = getattr(memory, 'cached', 0) // (1024 * 1024)
            
            # Swap memory
            swap = psutil.swap_memory()
            metrics['swap_used_mb'] = swap.used // (1024 * 1024)
            metrics['swap_total_mb'] = swap.total // (1024 * 1024)
            metrics['swap_percent'] = swap.percent
            metrics['swap_free_mb'] = swap.free // (1024 * 1024)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting memory metrics: {e}")
            return None
    
    @safe_execute
    async def _collect_disk_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect disk metrics"""
        try:
            metrics = {}
            
            # Root filesystem usage
            disk_usage = psutil.disk_usage('/')
            metrics['disk_used_gb'] = disk_usage.used / (1024**3)
            metrics['disk_available_gb'] = disk_usage.free / (1024**3)
            metrics['disk_total_gb'] = disk_usage.total / (1024**3)
            metrics['disk_percent'] = (disk_usage.used / disk_usage.total) * 100
            
            # Disk I/O statistics
            disk_io = psutil.disk_io_counters()
            if disk_io:
                metrics['disk_read_bytes'] = disk_io.read_bytes
                metrics['disk_write_bytes'] = disk_io.write_bytes
                metrics['disk_read_count'] = disk_io.read_count
                metrics['disk_write_count'] = disk_io.write_count
                metrics['disk_read_time'] = disk_io.read_time
                metrics['disk_write_time'] = disk_io.write_time
            
            # Additional disk usage for detailed monitoring
            if self.config.enable_detailed_monitoring:
                disk_partitions = psutil.disk_partitions()
                partitions = {}
                
                for partition in disk_partitions:
                    try:
                        partition_usage = psutil.disk_usage(partition.mountpoint)
                        partitions[partition.mountpoint] = {
                            'device': partition.device,
                            'fstype': partition.fstype,
                            'total_gb': partition_usage.total / (1024**3),
                            'used_gb': partition_usage.used / (1024**3),
                            'free_gb': partition_usage.free / (1024**3),
                            'percent': (partition_usage.used / partition_usage.total) * 100
                        }
                    except:
                        continue
                
                metrics['disk_partitions'] = partitions
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting disk metrics: {e}")
            return None
    
    @safe_execute
    async def _collect_network_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect network metrics"""
        try:
            metrics = {}
            
            # Network I/O statistics
            net_io = psutil.net_io_counters()
            if net_io:
                metrics['network_sent_bytes'] = net_io.bytes_sent
                metrics['network_recv_bytes'] = net_io.bytes_recv
                metrics['network_packets_sent'] = net_io.packets_sent
                metrics['network_packets_recv'] = net_io.packets_recv
                metrics['network_error_in'] = net_io.errin
                metrics['network_error_out'] = net_io.errout
                metrics['network_drop_in'] = net_io.dropin
                metrics['network_drop_out'] = net_io.dropout
            
            # Per-interface statistics for detailed monitoring
            if self.config.enable_detailed_monitoring:
                net_io_per_interface = psutil.net_io_counters(pernic=True)
                interfaces = {}
                
                for interface, stats in net_io_per_interface.items():
                    if interface != 'lo':  # Skip loopback
                        interfaces[interface] = {
                            'bytes_sent': stats.bytes_sent,
                            'bytes_recv': stats.bytes_recv,
                            'packets_sent': stats.packets_sent,
                            'packets_recv': stats.packets_recv,
                            'errin': stats.errin,
                            'errout': stats.errout,
                            'dropin': stats.dropin,
                            'dropout': stats.dropout
                        }
                
                metrics['network_interfaces'] = interfaces
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting network metrics: {e}")
            return None
    
    @safe_execute
    async def _collect_process_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect process metrics"""
        try:
            metrics = {}
            
            # Process counts by status
            processes = list(psutil.process_iter(['status']))
            status_counts = {'running': 0, 'sleeping': 0, 'zombie': 0, 'stopped': 0, 'idle': 0}
            
            for proc in processes:
                try:
                    status = proc.info['status']
                    if status in status_counts:
                        status_counts[status] += 1
                except:
                    continue
            
            metrics['processes_running'] = status_counts['running']
            metrics['processes_sleeping'] = status_counts['sleeping']
            metrics['processes_zombie'] = status_counts['zombie']
            metrics['processes_stopped'] = status_counts['stopped']
            metrics['processes_total'] = len(processes)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting process metrics: {e}")
            return None
    
    @safe_execute
    async def _collect_service_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect service metrics"""
        try:
            if hasattr(self.modules['service'], 'get_service_metrics'):
                return await self.modules['service'].get_service_metrics()
        except Exception as e:
            self.logger.error(f"Error collecting service metrics: {e}")
        return None
    
    @safe_execute
    async def _collect_temperature_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect temperature metrics"""
        try:
            metrics = {}
            
            # CPU temperature
            cpu_temp = await self._get_cpu_temperature()
            if cpu_temp is not None:
                metrics['cpu_temperature'] = cpu_temp
            
            # Additional temperature sensors
            if hasattr(psutil, 'sensors_temperatures'):
                try:
                    temps = psutil.sensors_temperatures()
                    if temps:
                        temp_data = {}
                        for name, entries in temps.items():
                            temp_data[name] = [{
                                'label': entry.label or 'unlabeled',
                                'current': entry.current,
                                'high': entry.high,
                                'critical': entry.critical
                            } for entry in entries]
                        metrics['temperature_sensors'] = temp_data
                except:
                    pass
            
            return metrics if metrics else None
            
        except Exception as e:
            self.logger.error(f"Error collecting temperature metrics: {e}")
            return None
    
    @safe_execute
    async def _collect_security_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect security metrics"""
        try:
            if hasattr(self.modules['security'], 'get_security_metrics'):
                return await self.modules['security'].get_security_metrics()
        except Exception as e:
            self.logger.error(f"Error collecting security metrics: {e}")
        return None
    
    @safe_execute
    async def _collect_gpio_metrics(self) -> Optional[Dict[int, int]]:
        """Collect GPIO state metrics"""
        if not GPIO_AVAILABLE or not self.config.gpio_pins:
            return None
        
        try:
            gpio_states = {}
            
            for pin in self.config.gpio_pins:
                try:
                    GPIO.setup(pin, GPIO.IN)
                    state = GPIO.input(pin)
                    gpio_states[pin] = state
                except Exception as e:
                    self.logger.warning(f"Error reading GPIO pin {pin}: {e}")
                    gpio_states[pin] = -1  # Error state
            
            return gpio_states
            
        except Exception as e:
            self.logger.error(f"Error collecting GPIO metrics: {e}")
            return None
    
    @safe_execute
    async def _collect_custom_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect custom script metrics"""
        if not self.config.custom_scripts:
            return None
        
        try:
            custom_metrics = {}
            
            for script_name, script_path in self.config.custom_scripts.items():
                try:
                    if os.path.exists(script_path) and os.access(script_path, os.X_OK):
                        result = subprocess.run(
                            [script_path],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        
                        if result.returncode == 0:
                            output = result.stdout.strip()
                            try:
                                # Try to parse as JSON first
                                custom_metrics[script_name] = json.loads(output)
                            except json.JSONDecodeError:
                                try:
                                    # Try to parse as float
                                    custom_metrics[script_name] = float(output)
                                except ValueError:
                                    # Store as string
                                    custom_metrics[script_name] = output
                        else:
                            self.logger.warning(f"Custom script {script_name} failed with code {result.returncode}")
                            custom_metrics[script_name] = None
                    else:
                        self.logger.warning(f"Custom script {script_name} not found or not executable: {script_path}")
                        custom_metrics[script_name] = None
                        
                except Exception as e:
                    self.logger.error(f"Error running custom script {script_name}: {e}")
                    custom_metrics[script_name] = None
            
            return custom_metrics if custom_metrics else None
            
        except Exception as e:
            self.logger.error(f"Error collecting custom metrics: {e}")
            return None
    
    @safe_execute
    async def _get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature"""
        try:
            # Try Raspberry Pi thermal zone
            thermal_file = '/sys/class/thermal/thermal_zone0/temp'
            if os.path.exists(thermal_file):
                with open(thermal_file, 'r') as f:
                    temp = float(f.read().strip()) / 1000.0
                    return temp
            
            # Try vcgencmd for Raspberry Pi
            try:
                result = subprocess.run(
                    ['vcgencmd', 'measure_temp'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    import re
                    match = re.search(r"temp=([0-9.]+)", result.stdout)
                    if match:
                        return float(match.group(1))
            except:
                pass
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting CPU temperature: {e}")
            return None