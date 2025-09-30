"""
Network Monitor Module
Monitors network interfaces, connections, traffic, and connectivity
"""

import psutil
import socket
import time
import logging
import subprocess
import ipaddress
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import json
import threading
from collections import deque
import statistics


class NetworkMonitor:
    def __init__(self, history_size: int = 300):  # 5 minutes of history at 1-second intervals
        self.logger = logging.getLogger(__name__)
        self.history_size = history_size
        self.interface_stats_history = {}
        self.connection_history = deque(maxlen=history_size)
        self._monitoring = False
        self._monitor_thread = None
        self._lock = threading.Lock()
        self._last_net_io = None

    def get_network_interfaces(self) -> Dict[str, Any]:
        """Get comprehensive network interface information"""
        try:
            interfaces = {}

            # Get interface addresses
            if_addrs = psutil.net_if_addrs()

            # Get interface statistics
            if_stats = psutil.net_if_stats()

            for interface_name, addresses in if_addrs.items():
                interface_info = {
                    'name': interface_name,
                    'addresses': [],
                    'statistics': {},
                    'status': 'unknown'
                }

                # Process addresses
                for addr in addresses:
                    addr_info = {'family': addr.family}

                    if addr.family == socket.AF_INET:  # IPv4
                        addr_info.update({
                            'type': 'IPv4',
                            'address': addr.address,
                            'netmask': addr.netmask,
                            'broadcast': addr.broadcast
                        })
                    elif addr.family == socket.AF_INET6:  # IPv6
                        addr_info.update({
                            'type': 'IPv6',
                            'address': addr.address,
                            'netmask': addr.netmask
                        })
                    elif addr.family == psutil.AF_LINK:  # MAC address
                        addr_info.update({
                            'type': 'MAC',
                            'address': addr.address
                        })

                    interface_info['addresses'].append(addr_info)

                # Add statistics if available
                if interface_name in if_stats:
                    stats = if_stats[interface_name]
                    interface_info['statistics'] = {
                        'is_up': stats.isup,
                        'duplex': self._get_duplex_name(stats.duplex),
                        'speed': f"{stats.speed} Mbps" if stats.speed > 0 else "Unknown",
                        'mtu': stats.mtu
                    }
                    interface_info['status'] = 'up' if stats.isup else 'down'

                interfaces[interface_name] = interface_info

            return {
                'timestamp': datetime.now().isoformat(),
                'interfaces': interfaces,
                'interface_count': len(interfaces)
            }

        except Exception as e:
            self.logger.error(f"Error getting network interfaces: {e}")
            return {"error": str(e)}

    def get_network_io_stats(self) -> Dict[str, Any]:
        """Get network I/O statistics"""
        try:
            # Overall network I/O
            net_io = psutil.net_io_counters()

            # Per-interface I/O
            per_nic_io = psutil.net_io_counters(pernic=True)

            result = {
                'timestamp': datetime.now().isoformat(),
                'total': {
                    'bytes_sent': self._bytes_to_human(net_io.bytes_sent),
                    'bytes_recv': self._bytes_to_human(net_io.bytes_recv),
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                    'errin': net_io.errin,
                    'errout': net_io.errout,
                    'dropin': net_io.dropin,
                    'dropout': net_io.dropout
                },
                'per_interface': {}
            }

            # Add per-interface statistics
            for interface, counters in per_nic_io.items():
                result['per_interface'][interface] = {
                    'bytes_sent': self._bytes_to_human(counters.bytes_sent),
                    'bytes_recv': self._bytes_to_human(counters.bytes_recv),
                    'packets_sent': counters.packets_sent,
                    'packets_recv': counters.packets_recv,
                    'errors_in': counters.errin,
                    'errors_out': counters.errout,
                    'drops_in': counters.dropin,
                    'drops_out': counters.dropout
                }

            return result

        except Exception as e:
            self.logger.error(f"Error getting network I/O stats: {e}")
            return {"error": str(e)}

    def get_network_connections(self, kind: str = 'inet') -> Dict[str, Any]:
        """Get network connections"""
        try:
            connections = psutil.net_connections(kind=kind)

            connection_stats = {
                'total_connections': len(connections),
                'by_status': {},
                'by_family': {},
                'listening_ports': [],
                'connections': []
            }

            for conn in connections:
                # Count by status
                status = conn.status if conn.status else 'UNKNOWN'
                connection_stats['by_status'][status] = connection_stats['by_status'].get(status, 0) + 1

                # Count by family
                family_name = self._get_family_name(conn.family)
                connection_stats['by_family'][family_name] = connection_stats['by_family'].get(family_name, 0) + 1

                # Collect listening ports
                if conn.status == 'LISTEN' and conn.laddr:
                    connection_stats['listening_ports'].append({
                        'port': conn.laddr.port,
                        'address': conn.laddr.ip,
                        'family': family_name,
                        'process': self._get_process_info(conn.pid) if conn.pid else None
                    })

                # Add detailed connection info (limit to first 50)
                if len(connection_stats['connections']) < 50:
                    conn_info = {
                        'family': family_name,
                        'type': self._get_socket_type_name(conn.type),
                        'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                        'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                        'status': status,
                        'process': self._get_process_info(conn.pid) if conn.pid else None
                    }
                    connection_stats['connections'].append(conn_info)

            return {
                'timestamp': datetime.now().isoformat(),
                **connection_stats
            }

        except Exception as e:
            self.logger.error(f"Error getting network connections: {e}")
            return {"error": str(e)}

    def test_connectivity(self, hosts: List[str] = None) -> Dict[str, Any]:
        """Test network connectivity to various hosts"""
        if hosts is None:
            hosts = ['8.8.8.8', 'google.com', '1.1.1.1', 'github.com']

        results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {
                'total_tests': len(hosts),
                'successful': 0,
                'failed': 0
            }
        }

        for host in hosts:
            test_result = self._ping_host(host)
            results['tests'].append(test_result)

            if test_result['success']:
                results['summary']['successful'] += 1
            else:
                results['summary']['failed'] += 1

        results['summary']['success_rate'] = (results['summary']['successful'] / results['summary']['total_tests']) * 100

        return results

    def get_network_speed_test(self, interface: str = None) -> Dict[str, Any]:
        """Perform a simple network throughput test"""
        try:
            if interface and interface not in psutil.net_if_stats():
                return {"error": f"Interface {interface} not found"}

            # Get initial I/O counters
            if interface:
                initial_io = psutil.net_io_counters(pernic=True)[interface]
            else:
                initial_io = psutil.net_io_counters()

            initial_time = time.time()

            # Wait for measurement period
            time.sleep(2)

            # Get final I/O counters
            if interface:
                final_io = psutil.net_io_counters(pernic=True)[interface]
            else:
                final_io = psutil.net_io_counters()

            final_time = time.time()
            time_delta = final_time - initial_time

            # Calculate rates
            bytes_sent_rate = (final_io.bytes_sent - initial_io.bytes_sent) / time_delta
            bytes_recv_rate = (final_io.bytes_recv - initial_io.bytes_recv) / time_delta

            return {
                'timestamp': datetime.now().isoformat(),
                'interface': interface or 'all',
                'measurement_duration': round(time_delta, 2),
                'upload_speed': {
                    'bytes_per_second': bytes_sent_rate,
                    'mbps': round((bytes_sent_rate * 8) / (1024 * 1024), 2),
                    'human': self._bytes_to_human(bytes_sent_rate) + '/s'
                },
                'download_speed': {
                    'bytes_per_second': bytes_recv_rate,
                    'mbps': round((bytes_recv_rate * 8) / (1024 * 1024), 2),
                    'human': self._bytes_to_human(bytes_recv_rate) + '/s'
                }
            }

        except Exception as e:
            self.logger.error(f"Error performing network speed test: {e}")
            return {"error": str(e)}

    def scan_local_network(self, network: str = None) -> Dict[str, Any]:
        """Scan local network for active hosts"""
        try:
            if network is None:
                # Try to determine local network
                network = self._get_local_network()

            if not network:
                return {"error": "Could not determine local network"}

            active_hosts = []
            network_obj = ipaddress.ip_network(network, strict=False)

            # Limit scan to reasonable subnet sizes
            if network_obj.num_addresses > 256:
                return {"error": "Network too large to scan (max 256 addresses)"}

            for ip in network_obj.hosts():
                if self._ping_host(str(ip), timeout=1)['success']:
                    host_info = {
                        'ip': str(ip),
                        'hostname': self._get_hostname(str(ip))
                    }
                    active_hosts.append(host_info)

            return {
                'timestamp': datetime.now().isoformat(),
                'network': network,
                'total_addresses': network_obj.num_addresses,
                'active_hosts': active_hosts,
                'active_count': len(active_hosts)
            }

        except Exception as e:
            self.logger.error(f"Error scanning local network: {e}")
            return {"error": str(e)}

    def start_monitoring(self, interval: float = 1.0):
        """Start continuous network monitoring"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        self.logger.info("Network monitoring started")

    def stop_monitoring(self):
        """Stop continuous network monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.logger.info("Network monitoring stopped")

    def _monitor_loop(self, interval: float):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                timestamp = datetime.now()

                # Monitor network I/O per interface
                per_nic_io = psutil.net_io_counters(pernic=True)

                if self._last_net_io:
                    for interface, current_io in per_nic_io.items():
                        if interface in self._last_net_io:
                            last_io = self._last_net_io[interface]

                            # Calculate rates
                            bytes_sent_rate = (current_io.bytes_sent - last_io.bytes_sent) / interval
                            bytes_recv_rate = (current_io.bytes_recv - last_io.bytes_recv) / interval

                            with self._lock:
                                if interface not in self.interface_stats_history:
                                    self.interface_stats_history[interface] = deque(maxlen=self.history_size)

                                self.interface_stats_history[interface].append({
                                    'timestamp': timestamp,
                                    'bytes_sent_rate': bytes_sent_rate,
                                    'bytes_recv_rate': bytes_recv_rate,
                                    'packets_sent_rate': (current_io.packets_sent - last_io.packets_sent) / interval,
                                    'packets_recv_rate': (current_io.packets_recv - last_io.packets_recv) / interval
                                })

                self._last_net_io = per_nic_io

                # Monitor connection count
                try:
                    connections = psutil.net_connections()
                    with self._lock:
                        self.connection_history.append({
                            'timestamp': timestamp,
                            'total_connections': len(connections),
                            'established_connections': len([c for c in connections if c.status == 'ESTABLISHED'])
                        })
                except:
                    pass  # Ignore connection monitoring errors

                time.sleep(interval)

            except Exception as e:
                self.logger.error(f"Error in network monitoring loop: {e}")
                time.sleep(interval)

    def get_network_alerts(self,
                          high_traffic_threshold_mbps: float = 50,
                          connection_threshold: int = 1000) -> Dict[str, Any]:
        """Check for network-related alerts"""
        try:
            alerts = []

            # Check for high traffic
            speed_test = self.get_network_speed_test()
            if 'error' not in speed_test:
                upload_mbps = speed_test['upload_speed']['mbps']
                download_mbps = speed_test['download_speed']['mbps']

                if upload_mbps > high_traffic_threshold_mbps:
                    alerts.append({
                        'type': 'high_upload_traffic',
                        'level': 'warning',
                        'message': f"High upload traffic: {upload_mbps:.2f} Mbps",
                        'value': upload_mbps
                    })

                if download_mbps > high_traffic_threshold_mbps:
                    alerts.append({
                        'type': 'high_download_traffic',
                        'level': 'warning',
                        'message': f"High download traffic: {download_mbps:.2f} Mbps",
                        'value': download_mbps
                    })

            # Check connection count
            connections = self.get_network_connections()
            if 'error' not in connections:
                total_connections = connections['total_connections']
                if total_connections > connection_threshold:
                    alerts.append({
                        'type': 'high_connection_count',
                        'level': 'warning',
                        'message': f"High number of network connections: {total_connections}",
                        'value': total_connections
                    })

            # Check interface status
            interfaces = self.get_network_interfaces()
            if 'error' not in interfaces:
                for name, interface in interfaces['interfaces'].items():
                    if interface['status'] == 'down' and not name.startswith('lo'):
                        alerts.append({
                            'type': 'interface_down',
                            'level': 'warning',
                            'message': f"Network interface {name} is down",
                            'interface': name
                        })

            return {
                'timestamp': datetime.now().isoformat(),
                'alerts': alerts,
                'alert_count': len(alerts)
            }

        except Exception as e:
            self.logger.error(f"Error checking network alerts: {e}")
            return {"error": str(e)}

    def _ping_host(self, host: str, timeout: int = 3) -> Dict[str, Any]:
        """Ping a host to test connectivity"""
        try:
            # Use ping command
            cmd = ['ping', '-c', '1', '-W', str(timeout), host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 2)

            success = result.returncode == 0
            response_time = None

            if success and result.stdout:
                # Extract response time from ping output
                for line in result.stdout.split('\n'):
                    if 'time=' in line:
                        try:
                            time_part = line.split('time=')[1].split()[0]
                            response_time = float(time_part)
                            break
                        except:
                            pass

            return {
                'host': host,
                'success': success,
                'response_time_ms': response_time,
                'error': result.stderr if not success else None
            }

        except subprocess.TimeoutExpired:
            return {
                'host': host,
                'success': False,
                'response_time_ms': None,
                'error': 'Timeout'
            }
        except Exception as e:
            return {
                'host': host,
                'success': False,
                'response_time_ms': None,
                'error': str(e)
            }

    def _get_local_network(self) -> Optional[str]:
        """Get local network CIDR"""
        try:
            # Get default route interface
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                        # Assume /24 network for simplicity
                        network = ipaddress.ip_network(f"{addr.address}/24", strict=False)
                        return str(network)
            return None
        except:
            return None

    def _get_hostname(self, ip: str) -> Optional[str]:
        """Get hostname for IP address"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return None

    def _get_process_info(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get process information for PID"""
        try:
            proc = psutil.Process(pid)
            return {
                'pid': pid,
                'name': proc.name(),
                'username': proc.username()
            }
        except:
            return None

    @staticmethod
    def _get_duplex_name(duplex: int) -> str:
        """Convert duplex code to name"""
        duplex_map = {
            1: 'Half',
            2: 'Full',
            0: 'Unknown'
        }
        return duplex_map.get(duplex, 'Unknown')

    @staticmethod
    def _get_family_name(family: int) -> str:
        """Convert address family to name"""
        family_map = {
            socket.AF_INET: 'IPv4',
            socket.AF_INET6: 'IPv6',
            socket.AF_UNIX: 'Unix',
        }
        return family_map.get(family, 'Unknown')

    @staticmethod
    def _get_socket_type_name(sock_type: int) -> str:
        """Convert socket type to name"""
        type_map = {
            socket.SOCK_STREAM: 'TCP',
            socket.SOCK_DGRAM: 'UDP',
            socket.SOCK_RAW: 'Raw'
        }
        return type_map.get(sock_type, 'Unknown')

    @staticmethod
    def _bytes_to_human(bytes_value: float) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"


# Example usage
if __name__ == "__main__":
    monitor = NetworkMonitor()

    print("=== Network Interfaces ===")
    interfaces = monitor.get_network_interfaces()
    print(json.dumps(interfaces, indent=2))

    print("\n=== Network I/O Statistics ===")
    io_stats = monitor.get_network_io_stats()
    print(json.dumps(io_stats, indent=2))

    print("\n=== Network Connections ===")
    connections = monitor.get_network_connections()
    print(json.dumps(connections, indent=2))

    print("\n=== Connectivity Test ===")
    connectivity = monitor.test_connectivity(['8.8.8.8', 'google.com'])
    print(json.dumps(connectivity, indent=2))

    print("\n=== Network Speed Test ===")
    speed_test = monitor.get_network_speed_test()
    print(json.dumps(speed_test, indent=2))

    print("\n=== Network Alerts ===")
    alerts = monitor.get_network_alerts()
    print(json.dumps(alerts, indent=2))