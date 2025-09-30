"""
Disk Monitor Module
Monitors disk usage, I/O, and file system information
"""

import psutil
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import threading
from collections import deque
import statistics
import shutil


class DiskMonitor:
    def __init__(self, history_size: int = 300):  # 5 minutes of history at 1-second intervals
        self.logger = logging.getLogger(__name__)
        self.history_size = history_size
        self.disk_usage_history = {}
        self.disk_io_history = deque(maxlen=history_size)
        self._monitoring = False
        self._monitor_thread = None
        self._lock = threading.Lock()
        self._last_io_counters = None

    def get_disk_info(self) -> Dict[str, Any]:
        """Get comprehensive disk information"""
        try:
            disk_info = {
                'partitions': [],
                'summary': {
                    'total_partitions': 0,
                    'total_space_gb': 0,
                    'total_used_gb': 0,
                    'total_free_gb': 0,
                    'average_usage_percent': 0
                }
            }

            total_size = 0
            total_used = 0
            total_free = 0
            usage_percentages = []

            # Get all disk partitions
            for partition in psutil.disk_partitions(all=False):  # Only physical devices
                try:
                    partition_usage = psutil.disk_usage(partition.mountpoint)

                    partition_info = {
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'filesystem': partition.fstype,
                        'size': {
                            'total': self._bytes_to_human(partition_usage.total),
                            'used': self._bytes_to_human(partition_usage.used),
                            'free': self._bytes_to_human(partition_usage.free),
                            'total_gb': round(partition_usage.total / (1024**3), 2),
                            'used_gb': round(partition_usage.used / (1024**3), 2),
                            'free_gb': round(partition_usage.free / (1024**3), 2)
                        },
                        'usage_percent': round((partition_usage.used / partition_usage.total) * 100, 2),
                        'status': self._get_disk_status((partition_usage.used / partition_usage.total) * 100),
                        'options': partition.opts if hasattr(partition, 'opts') else 'Unknown'
                    }

                    disk_info['partitions'].append(partition_info)

                    # Add to totals
                    total_size += partition_usage.total
                    total_used += partition_usage.used
                    total_free += partition_usage.free
                    usage_percentages.append(partition_info['usage_percent'])

                except PermissionError:
                    # Skip partitions we can't access
                    continue
                except Exception as e:
                    self.logger.warning(f"Error accessing partition {partition.device}: {e}")
                    continue

            # Calculate summary
            disk_info['summary'] = {
                'total_partitions': len(disk_info['partitions']),
                'total_space_gb': round(total_size / (1024**3), 2),
                'total_used_gb': round(total_used / (1024**3), 2),
                'total_free_gb': round(total_free / (1024**3), 2),
                'overall_usage_percent': round((total_used / total_size) * 100, 2) if total_size > 0 else 0,
                'average_usage_percent': round(statistics.mean(usage_percentages), 2) if usage_percentages else 0
            }

            return disk_info

        except Exception as e:
            self.logger.error(f"Error getting disk info: {e}")
            return {"error": str(e)}

    def get_disk_usage(self, path: str = '/') -> Dict[str, Any]:
        """Get disk usage for a specific path"""
        try:
            if not os.path.exists(path):
                return {"error": f"Path {path} does not exist"}

            usage = psutil.disk_usage(path)

            return {
                'timestamp': datetime.now().isoformat(),
                'path': path,
                'total_gb': round(usage.total / (1024**3), 2),
                'used_gb': round(usage.used / (1024**3), 2),
                'free_gb': round(usage.free / (1024**3), 2),
                'usage_percent': round((usage.used / usage.total) * 100, 2),
                'status': self._get_disk_status((usage.used / usage.total) * 100)
            }

        except Exception as e:
            self.logger.error(f"Error getting disk usage for {path}: {e}")
            return {"error": str(e)}

    def get_disk_io_stats(self) -> Dict[str, Any]:
        """Get disk I/O statistics"""
        try:
            # Overall I/O stats
            io_counters = psutil.disk_io_counters()
            if not io_counters:
                return {"error": "Disk I/O statistics not available"}

            # Per-disk I/O stats
            per_disk_io = psutil.disk_io_counters(perdisk=True)

            result = {
                'timestamp': datetime.now().isoformat(),
                'total': {
                    'read_count': io_counters.read_count,
                    'write_count': io_counters.write_count,
                    'read_bytes': self._bytes_to_human(io_counters.read_bytes),
                    'write_bytes': self._bytes_to_human(io_counters.write_bytes),
                    'read_time': io_counters.read_time,
                    'write_time': io_counters.write_time,
                    'busy_time': getattr(io_counters, 'busy_time', 'N/A')
                },
                'per_disk': {}
            }

            # Add per-disk statistics
            for disk, counters in per_disk_io.items():
                result['per_disk'][disk] = {
                    'read_count': counters.read_count,
                    'write_count': counters.write_count,
                    'read_bytes': self._bytes_to_human(counters.read_bytes),
                    'write_bytes': self._bytes_to_human(counters.write_bytes),
                    'read_time': counters.read_time,
                    'write_time': counters.write_time
                }

            return result

        except Exception as e:
            self.logger.error(f"Error getting disk I/O stats: {e}")
            return {"error": str(e)}

    def get_large_files(self, path: str = '/', min_size_mb: int = 100, limit: int = 20) -> Dict[str, Any]:
        """Find large files in a directory"""
        try:
            if not os.path.exists(path):
                return {"error": f"Path {path} does not exist"}

            large_files = []
            min_size_bytes = min_size_mb * 1024 * 1024

            def scan_directory(directory: str, depth: int = 0):
                if depth > 3:  # Limit recursion depth
                    return

                try:
                    for entry in os.scandir(directory):
                        try:
                            if entry.is_file(follow_symlinks=False):
                                stat_info = entry.stat()
                                if stat_info.st_size >= min_size_bytes:
                                    large_files.append({
                                        'path': entry.path,
                                        'size_mb': round(stat_info.st_size / (1024**2), 2),
                                        'size_human': self._bytes_to_human(stat_info.st_size),
                                        'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                                        'accessed': datetime.fromtimestamp(stat_info.st_atime).isoformat()
                                    })
                            elif entry.is_dir(follow_symlinks=False):
                                scan_directory(entry.path, depth + 1)
                        except (PermissionError, FileNotFoundError, OSError):
                            continue
                except (PermissionError, FileNotFoundError, OSError):
                    pass

            scan_directory(path)

            # Sort by size (largest first) and limit results
            large_files.sort(key=lambda x: x['size_mb'], reverse=True)
            large_files = large_files[:limit]

            total_size_mb = sum(file_info['size_mb'] for file_info in large_files)

            return {
                'timestamp': datetime.now().isoformat(),
                'search_path': path,
                'min_size_mb': min_size_mb,
                'files_found': len(large_files),
                'total_size_mb': round(total_size_mb, 2),
                'files': large_files
            }

        except Exception as e:
            self.logger.error(f"Error finding large files: {e}")
            return {"error": str(e)}

    def get_directory_sizes(self, path: str = '/', depth: int = 2) -> Dict[str, Any]:
        """Get sizes of subdirectories"""
        try:
            if not os.path.exists(path):
                return {"error": f"Path {path} does not exist"}

            directory_sizes = []

            for entry in os.scandir(path):
                try:
                    if entry.is_dir(follow_symlinks=False):
                        size = self._get_directory_size(entry.path)
                        if size > 0:
                            directory_sizes.append({
                                'name': entry.name,
                                'path': entry.path,
                                'size_mb': round(size / (1024**2), 2),
                                'size_human': self._bytes_to_human(size)
                            })
                except (PermissionError, FileNotFoundError, OSError):
                    continue

            # Sort by size (largest first)
            directory_sizes.sort(key=lambda x: x['size_mb'], reverse=True)

            total_size_mb = sum(dir_info['size_mb'] for dir_info in directory_sizes)

            return {
                'timestamp': datetime.now().isoformat(),
                'path': path,
                'directories_found': len(directory_sizes),
                'total_size_mb': round(total_size_mb, 2),
                'directories': directory_sizes[:20]  # Limit to top 20
            }

        except Exception as e:
            self.logger.error(f"Error getting directory sizes: {e}")
            return {"error": str(e)}

    def start_monitoring(self, interval: float = 1.0):
        """Start continuous disk monitoring"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        self.logger.info("Disk monitoring started")

    def stop_monitoring(self):
        """Stop continuous disk monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.logger.info("Disk monitoring stopped")

    def _monitor_loop(self, interval: float):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                timestamp = datetime.now()

                # Monitor disk usage for all partitions
                for partition in psutil.disk_partitions(all=False):
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        usage_percent = (usage.used / usage.total) * 100

                        with self._lock:
                            if partition.device not in self.disk_usage_history:
                                self.disk_usage_history[partition.device] = deque(maxlen=self.history_size)

                            self.disk_usage_history[partition.device].append({
                                'timestamp': timestamp,
                                'usage_percent': usage_percent,
                                'used_gb': usage.used / (1024**3),
                                'free_gb': usage.free / (1024**3)
                            })
                    except (PermissionError, OSError):
                        continue

                # Monitor disk I/O
                io_counters = psutil.disk_io_counters()
                if io_counters and self._last_io_counters:
                    # Calculate I/O rates
                    time_delta = interval
                    read_rate = (io_counters.read_bytes - self._last_io_counters.read_bytes) / time_delta
                    write_rate = (io_counters.write_bytes - self._last_io_counters.write_bytes) / time_delta

                    with self._lock:
                        self.disk_io_history.append({
                            'timestamp': timestamp,
                            'read_rate_mbps': read_rate / (1024**2),
                            'write_rate_mbps': write_rate / (1024**2),
                            'total_reads': io_counters.read_count,
                            'total_writes': io_counters.write_count
                        })

                self._last_io_counters = io_counters
                time.sleep(interval)

            except Exception as e:
                self.logger.error(f"Error in disk monitoring loop: {e}")
                time.sleep(interval)

    def get_disk_alerts(self, warning_threshold: float = 80, critical_threshold: float = 90) -> Dict[str, Any]:
        """Check for disk usage alerts"""
        try:
            alerts = []

            for partition in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    usage_percent = (usage.used / usage.total) * 100

                    if usage_percent > critical_threshold:
                        alerts.append({
                            'type': 'disk_usage',
                            'level': 'critical',
                            'message': f"Critical disk usage on {partition.device} ({partition.mountpoint}): {usage_percent:.1f}%",
                            'device': partition.device,
                            'mountpoint': partition.mountpoint,
                            'usage_percent': usage_percent,
                            'free_gb': round(usage.free / (1024**3), 2)
                        })
                    elif usage_percent > warning_threshold:
                        alerts.append({
                            'type': 'disk_usage',
                            'level': 'warning',
                            'message': f"High disk usage on {partition.device} ({partition.mountpoint}): {usage_percent:.1f}%",
                            'device': partition.device,
                            'mountpoint': partition.mountpoint,
                            'usage_percent': usage_percent,
                            'free_gb': round(usage.free / (1024**3), 2)
                        })

                    # Check for very low free space (less than 1GB)
                    free_gb = usage.free / (1024**3)
                    if free_gb < 1.0:
                        alerts.append({
                            'type': 'low_free_space',
                            'level': 'critical',
                            'message': f"Very low free space on {partition.device}: {free_gb:.2f} GB",
                            'device': partition.device,
                            'mountpoint': partition.mountpoint,
                            'free_gb': free_gb
                        })

                except (PermissionError, OSError):
                    continue

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
            self.logger.error(f"Error checking disk alerts: {e}")
            return {"error": str(e)}

    def get_disk_health_recommendations(self) -> Dict[str, Any]:
        """Get disk health and optimization recommendations"""
        try:
            recommendations = []

            for partition in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    usage_percent = (usage.used / usage.total) * 100

                    # High usage recommendations
                    if usage_percent > 85:
                        recommendations.append({
                            'type': 'cleanup',
                            'device': partition.device,
                            'message': f"Consider cleaning up {partition.mountpoint} - {usage_percent:.1f}% full",
                            'priority': 'high' if usage_percent > 95 else 'medium'
                        })

                    # Small partition recommendations
                    total_gb = usage.total / (1024**3)
                    if total_gb < 10:
                        recommendations.append({
                            'type': 'small_partition',
                            'device': partition.device,
                            'message': f"Small partition detected ({total_gb:.1f} GB). Consider expansion if needed",
                            'priority': 'low'
                        })

                except (PermissionError, OSError):
                    continue

            # General recommendations
            recommendations.append({
                'type': 'maintenance',
                'message': "Run regular disk cleanup and consider setting up log rotation",
                'priority': 'info'
            })

            return {
                'timestamp': datetime.now().isoformat(),
                'recommendations': recommendations,
                'recommendation_count': len(recommendations)
            }

        except Exception as e:
            self.logger.error(f"Error getting disk recommendations: {e}")
            return {"error": str(e)}

    def _get_directory_size(self, path: str) -> int:
        """Get total size of a directory"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    try:
                        filepath = os.path.join(dirpath, filename)
                        if not os.path.islink(filepath):
                            total_size += os.path.getsize(filepath)
                    except (PermissionError, FileNotFoundError, OSError):
                        continue
        except (PermissionError, FileNotFoundError, OSError):
            pass
        return total_size

    @staticmethod
    def _bytes_to_human(bytes_value: int) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"

    @staticmethod
    def _get_disk_status(usage_percent: float) -> str:
        """Get disk status based on usage percentage"""
        if usage_percent >= 95:
            return "Critical"
        elif usage_percent >= 85:
            return "High"
        elif usage_percent >= 70:
            return "Moderate"
        else:
            return "Normal"


# Example usage
if __name__ == "__main__":
    monitor = DiskMonitor()

    print("=== Disk Information ===")
    info = monitor.get_disk_info()
    print(json.dumps(info, indent=2))

    print("\n=== Disk Usage (/) ===")
    usage = monitor.get_disk_usage('/')
    print(json.dumps(usage, indent=2))

    print("\n=== Disk I/O Statistics ===")
    io_stats = monitor.get_disk_io_stats()
    print(json.dumps(io_stats, indent=2))

    print("\n=== Large Files ===")
    large_files = monitor.get_large_files('/', min_size_mb=50, limit=5)
    print(json.dumps(large_files, indent=2))

    print("\n=== Directory Sizes ===")
    dir_sizes = monitor.get_directory_sizes('/')
    print(json.dumps(dir_sizes, indent=2))

    print("\n=== Disk Alerts ===")
    alerts = monitor.get_disk_alerts()
    print(json.dumps(alerts, indent=2))

    print("\n=== Disk Recommendations ===")
    recommendations = monitor.get_disk_health_recommendations()
    print(json.dumps(recommendations, indent=2))