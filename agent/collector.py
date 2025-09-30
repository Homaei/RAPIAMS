import psutil
import platform
import socket
import subprocess
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional
import logging

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

logger = logging.getLogger(__name__)


class MetricsCollector:
    def __init__(self, config):
        self.config = config
        self.hostname = socket.gethostname()
        self.boot_time = datetime.fromtimestamp(psutil.boot_time())
        
        if GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
    
    def get_system_info(self) -> Dict[str, Any]:
        try:
            uname = platform.uname()
            
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                model_match = re.search(r'Model\s+:\s+(.+)', cpuinfo)
                model = model_match.group(1) if model_match else uname.machine
            
            return {
                'hostname': self.hostname,
                'model': model,
                'os_version': f"{uname.system} {uname.release}",
                'kernel_version': uname.version,
                'agent_version': self.config.agent_version,
                'cpu_cores': psutil.cpu_count(),
                'ram_total_mb': psutil.virtual_memory().total // (1024 * 1024),
                'storage_total_gb': psutil.disk_usage('/').total / (1024**3),
                'ip_address': self.get_ip_address(),
                'mac_address': self.get_mac_address()
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {}
    
    def get_ip_address(self) -> Optional[str]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return None
    
    def get_mac_address(self) -> Optional[str]:
        try:
            for interface in psutil.net_if_addrs():
                if interface.startswith('eth') or interface.startswith('wlan'):
                    addrs = psutil.net_if_addrs()[interface]
                    for addr in addrs:
                        if addr.family == psutil.AF_LINK:
                            return addr.address
        except:
            return None
    
    async def collect_metrics(self) -> Dict[str, Any]:
        metrics = {
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics['cpu_percent'] = cpu_percent
            metrics['cpu_frequency'] = psutil.cpu_freq().current if psutil.cpu_freq() else None
            
            cpu_temp = self.get_cpu_temperature()
            if cpu_temp:
                metrics['cpu_temperature'] = cpu_temp
        except Exception as e:
            logger.error(f"Error collecting CPU metrics: {e}")
        
        try:
            memory = psutil.virtual_memory()
            metrics['memory_used_mb'] = memory.used // (1024 * 1024)
            metrics['memory_available_mb'] = memory.available // (1024 * 1024)
            metrics['memory_percent'] = memory.percent
            
            swap = psutil.swap_memory()
            metrics['swap_used_mb'] = swap.used // (1024 * 1024)
            metrics['swap_percent'] = swap.percent
        except Exception as e:
            logger.error(f"Error collecting memory metrics: {e}")
        
        try:
            disk = psutil.disk_usage('/')
            metrics['disk_used_gb'] = disk.used / (1024**3)
            metrics['disk_available_gb'] = disk.free / (1024**3)
            metrics['disk_percent'] = disk.percent
            
            disk_io = psutil.disk_io_counters()
            if disk_io:
                metrics['disk_read_bytes'] = disk_io.read_bytes
                metrics['disk_write_bytes'] = disk_io.write_bytes
        except Exception as e:
            logger.error(f"Error collecting disk metrics: {e}")
        
        try:
            net_io = psutil.net_io_counters()
            metrics['network_sent_bytes'] = net_io.bytes_sent
            metrics['network_recv_bytes'] = net_io.bytes_recv
            metrics['network_packets_sent'] = net_io.packets_sent
            metrics['network_packets_recv'] = net_io.packets_recv
            metrics['network_error_in'] = net_io.errin
            metrics['network_error_out'] = net_io.errout
        except Exception as e:
            logger.error(f"Error collecting network metrics: {e}")
        
        try:
            process_status = psutil.process_iter(['status'])
            processes = {'running': 0, 'sleeping': 0, 'total': 0}
            
            for proc in process_status:
                processes['total'] += 1
                status = proc.info['status']
                if status == psutil.STATUS_RUNNING:
                    processes['running'] += 1
                elif status == psutil.STATUS_SLEEPING:
                    processes['sleeping'] += 1
            
            metrics['processes_running'] = processes['running']
            metrics['processes_sleeping'] = processes['sleeping']
            metrics['processes_total'] = processes['total']
        except Exception as e:
            logger.error(f"Error collecting process metrics: {e}")
        
        try:
            uptime = (datetime.now() - self.boot_time).total_seconds()
            metrics['uptime_seconds'] = int(uptime)
            
            load_avg = os.getloadavg()
            metrics['load_avg_1'] = load_avg[0]
            metrics['load_avg_5'] = load_avg[1]
            metrics['load_avg_15'] = load_avg[2]
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
        
        if GPIO_AVAILABLE and self.config.gpio_pins:
            metrics['gpio_states'] = self.get_gpio_states()
        
        if self.config.custom_scripts:
            metrics['custom_metrics'] = self.run_custom_scripts()
        
        return metrics
    
    def get_cpu_temperature(self) -> Optional[float]:
        try:
            temp_file = '/sys/class/thermal/thermal_zone0/temp'
            if os.path.exists(temp_file):
                with open(temp_file, 'r') as f:
                    temp = float(f.read()) / 1000.0
                    return temp
            
            result = subprocess.run(
                ['vcgencmd', 'measure_temp'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                match = re.search(r"temp=([0-9.]+)", result.stdout)
                if match:
                    return float(match.group(1))
        except:
            pass
        
        return None
    
    def get_gpio_states(self) -> Dict[int, int]:
        states = {}
        
        if not GPIO_AVAILABLE:
            return states
        
        try:
            for pin in self.config.gpio_pins:
                GPIO.setup(pin, GPIO.IN)
                states[pin] = GPIO.input(pin)
        except Exception as e:
            logger.error(f"Error reading GPIO states: {e}")
        
        return states
    
    def run_custom_scripts(self) -> Dict[str, Any]:
        custom_metrics = {}
        
        for script_name, script_path in self.config.custom_scripts.items():
            try:
                if os.path.exists(script_path) and os.access(script_path, os.X_OK):
                    result = subprocess.run(
                        [script_path],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        try:
                            value = float(result.stdout.strip())
                            custom_metrics[script_name] = value
                        except ValueError:
                            custom_metrics[script_name] = result.stdout.strip()
            except Exception as e:
                logger.error(f"Error running custom script {script_name}: {e}")
        
        return custom_metrics
    
    def get_disk_usage(self) -> Optional[Dict[str, Any]]:
        try:
            disk = psutil.disk_usage('/')
            return {
                'used_gb': disk.used / (1024**3),
                'free_gb': disk.free / (1024**3),
                'percent': disk.percent
            }
        except:
            return None