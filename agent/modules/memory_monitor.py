"""
Memory Monitor Module
Monitors RAM, swap, and memory usage by processes
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


class MemoryMonitor:
    def __init__(self, history_size: int = 300):  # 5 minutes of history at 1-second intervals
        self.logger = logging.getLogger(__name__)
        self.history_size = history_size
        self.memory_history = deque(maxlen=history_size)
        self.swap_history = deque(maxlen=history_size)
        self._monitoring = False
        self._monitor_thread = None
        self._lock = threading.Lock()

    def get_memory_info(self) -> Dict[str, Any]:
        """Get comprehensive memory information"""
        try:
            # Virtual memory (RAM)
            virtual_mem = psutil.virtual_memory()

            # Swap memory
            swap_mem = psutil.swap_memory()

            memory_info = {
                'virtual_memory': {
                    'total': self._bytes_to_human(virtual_mem.total),
                    'available': self._bytes_to_human(virtual_mem.available),
                    'used': self._bytes_to_human(virtual_mem.used),
                    'free': self._bytes_to_human(virtual_mem.free),
                    'percent': virtual_mem.percent,
                    'active': self._bytes_to_human(getattr(virtual_mem, 'active', 0)),
                    'inactive': self._bytes_to_human(getattr(virtual_mem, 'inactive', 0)),
                    'buffers': self._bytes_to_human(getattr(virtual_mem, 'buffers', 0)),
                    'cached': self._bytes_to_human(getattr(virtual_mem, 'cached', 0)),
                    'shared': self._bytes_to_human(getattr(virtual_mem, 'shared', 0))
                },
                'swap_memory': {
                    'total': self._bytes_to_human(swap_mem.total),
                    'used': self._bytes_to_human(swap_mem.used),
                    'free': self._bytes_to_human(swap_mem.free),
                    'percent': swap_mem.percent,
                    'sin': self._bytes_to_human(swap_mem.sin),  # bytes swapped in
                    'sout': self._bytes_to_human(swap_mem.sout)  # bytes swapped out
                }
            }

            # Memory status
            memory_info['status'] = {
                'virtual_memory': self._get_memory_status(virtual_mem.percent),
                'swap_memory': self._get_memory_status(swap_mem.percent),
                'overall': self._get_overall_memory_status(virtual_mem.percent, swap_mem.percent)
            }

            return memory_info

        except Exception as e:
            self.logger.error(f"Error getting memory info: {e}")
            return {"error": str(e)}

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage"""
        try:
            virtual_mem = psutil.virtual_memory()
            swap_mem = psutil.swap_memory()

            return {
                'timestamp': datetime.now().isoformat(),
                'virtual_memory': {
                    'total_gb': round(virtual_mem.total / (1024**3), 2),
                    'used_gb': round(virtual_mem.used / (1024**3), 2),
                    'available_gb': round(virtual_mem.available / (1024**3), 2),
                    'percent': virtual_mem.percent
                },
                'swap_memory': {
                    'total_gb': round(swap_mem.total / (1024**3), 2),
                    'used_gb': round(swap_mem.used / (1024**3), 2),
                    'percent': swap_mem.percent
                },
                'status': self._get_overall_memory_status(virtual_mem.percent, swap_mem.percent)
            }

        except Exception as e:
            self.logger.error(f"Error getting memory usage: {e}")
            return {"error": str(e)}

    def get_top_memory_processes(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get top memory consuming processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info', 'username']):
                try:
                    proc_info = proc.info
                    # Add memory details
                    if proc_info['memory_info']:
                        proc_info['memory_mb'] = round(proc_info['memory_info'].rss / (1024**2), 2)
                        proc_info['virtual_memory_mb'] = round(proc_info['memory_info'].vms / (1024**2), 2)
                    else:
                        proc_info['memory_mb'] = 0
                        proc_info['virtual_memory_mb'] = 0

                    if proc_info['memory_percent'] and proc_info['memory_percent'] > 0:
                        processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort by memory usage and return top N
            processes.sort(key=lambda x: x['memory_percent'] or 0, reverse=True)
            return processes[:count]

        except Exception as e:
            self.logger.error(f"Error getting top memory processes: {e}")
            return [{"error": str(e)}]

    def get_memory_by_category(self) -> Dict[str, Any]:
        """Get memory usage categorized by process types"""
        try:
            categories = {
                'system': [],
                'browsers': [],
                'development': [],
                'media': [],
                'games': [],
                'office': [],
                'other': []
            }

            # Define process categories
            category_keywords = {
                'system': ['systemd', 'kernel', 'kthread', 'ksoftirq', 'ssh', 'dbus', 'NetworkManager'],
                'browsers': ['firefox', 'chrome', 'chromium', 'safari', 'edge', 'opera'],
                'development': ['python', 'node', 'java', 'code', 'vim', 'emacs', 'git', 'docker'],
                'media': ['vlc', 'mplayer', 'spotify', 'steam', 'gimp', 'ffmpeg'],
                'games': ['game', 'steam', 'minecraft'],
                'office': ['libreoffice', 'calc', 'writer', 'excel', 'word', 'powerpoint']
            }

            total_memory_by_category = {cat: 0 for cat in categories.keys()}

            for proc in psutil.process_iter(['name', 'memory_info']):
                try:
                    proc_name = proc.info['name'].lower()
                    memory_mb = proc.info['memory_info'].rss / (1024**2) if proc.info['memory_info'] else 0

                    categorized = False
                    for category, keywords in category_keywords.items():
                        if any(keyword in proc_name for keyword in keywords):
                            categories[category].append({
                                'name': proc.info['name'],
                                'memory_mb': round(memory_mb, 2)
                            })
                            total_memory_by_category[category] += memory_mb
                            categorized = True
                            break

                    if not categorized:
                        categories['other'].append({
                            'name': proc.info['name'],
                            'memory_mb': round(memory_mb, 2)
                        })
                        total_memory_by_category['other'] += memory_mb

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort categories by total memory usage
            for category in categories:
                categories[category].sort(key=lambda x: x['memory_mb'], reverse=True)

            return {
                'timestamp': datetime.now().isoformat(),
                'categories': categories,
                'totals': {cat: round(total, 2) for cat, total in total_memory_by_category.items()},
                'summary': sorted(
                    [{'category': cat, 'total_mb': round(total, 2)}
                     for cat, total in total_memory_by_category.items()],
                    key=lambda x: x['total_mb'], reverse=True
                )
            }

        except Exception as e:
            self.logger.error(f"Error getting memory by category: {e}")
            return {"error": str(e)}

    def start_monitoring(self, interval: float = 1.0):
        """Start continuous memory monitoring"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        self.logger.info("Memory monitoring started")

    def stop_monitoring(self):
        """Stop continuous memory monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.logger.info("Memory monitoring stopped")

    def _monitor_loop(self, interval: float):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                virtual_mem = psutil.virtual_memory()
                swap_mem = psutil.swap_memory()
                timestamp = datetime.now()

                with self._lock:
                    self.memory_history.append({
                        'timestamp': timestamp,
                        'virtual_percent': virtual_mem.percent,
                        'virtual_used_gb': virtual_mem.used / (1024**3),
                        'virtual_available_gb': virtual_mem.available / (1024**3)
                    })

                    self.swap_history.append({
                        'timestamp': timestamp,
                        'swap_percent': swap_mem.percent,
                        'swap_used_gb': swap_mem.used / (1024**3)
                    })

                time.sleep(interval)

            except Exception as e:
                self.logger.error(f"Error in memory monitoring loop: {e}")
                time.sleep(interval)

    def get_memory_history(self, minutes: int = 5) -> Dict[str, Any]:
        """Get memory usage history"""
        try:
            with self._lock:
                if not self.memory_history:
                    return {"error": "No history available. Start monitoring first."}

                cutoff_time = datetime.now() - timedelta(minutes=minutes)
                recent_memory = [
                    entry for entry in self.memory_history
                    if entry['timestamp'] > cutoff_time
                ]
                recent_swap = [
                    entry for entry in self.swap_history
                    if entry['timestamp'] > cutoff_time
                ]

                if not recent_memory:
                    return {"error": f"No data available for the last {minutes} minutes"}

                # Calculate statistics for virtual memory
                virtual_percent_values = [entry['virtual_percent'] for entry in recent_memory]
                swap_percent_values = [entry['swap_percent'] for entry in recent_swap if entry['swap_percent'] > 0]

                return {
                    'period_minutes': minutes,
                    'data_points': len(recent_memory),
                    'virtual_memory_stats': {
                        'average_percent': statistics.mean(virtual_percent_values),
                        'min_percent': min(virtual_percent_values),
                        'max_percent': max(virtual_percent_values),
                        'median_percent': statistics.median(virtual_percent_values)
                    },
                    'swap_memory_stats': {
                        'average_percent': statistics.mean(swap_percent_values) if swap_percent_values else 0,
                        'max_percent': max(swap_percent_values) if swap_percent_values else 0
                    },
                    'timeline': [
                        {
                            'timestamp': entry['timestamp'].isoformat(),
                            'virtual_percent': entry['virtual_percent'],
                            'virtual_used_gb': round(entry['virtual_used_gb'], 2),
                            'virtual_available_gb': round(entry['virtual_available_gb'], 2)
                        }
                        for entry in recent_memory[-60:]  # Last 60 data points
                    ]
                }

        except Exception as e:
            self.logger.error(f"Error getting memory history: {e}")
            return {"error": str(e)}

    def get_memory_alerts(self, warning_threshold: float = 80, critical_threshold: float = 90) -> Dict[str, Any]:
        """Check for memory usage alerts"""
        try:
            virtual_mem = psutil.virtual_memory()
            swap_mem = psutil.swap_memory()

            alerts = []

            # Virtual memory alerts
            if virtual_mem.percent > critical_threshold:
                alerts.append({
                    'type': 'virtual_memory',
                    'level': 'critical',
                    'message': f"Critical memory usage: {virtual_mem.percent:.1f}%",
                    'current_value': virtual_mem.percent,
                    'threshold': critical_threshold
                })
            elif virtual_mem.percent > warning_threshold:
                alerts.append({
                    'type': 'virtual_memory',
                    'level': 'warning',
                    'message': f"High memory usage: {virtual_mem.percent:.1f}%",
                    'current_value': virtual_mem.percent,
                    'threshold': warning_threshold
                })

            # Swap memory alerts
            if swap_mem.total > 0 and swap_mem.percent > critical_threshold:
                alerts.append({
                    'type': 'swap_memory',
                    'level': 'critical',
                    'message': f"Critical swap usage: {swap_mem.percent:.1f}%",
                    'current_value': swap_mem.percent,
                    'threshold': critical_threshold
                })
            elif swap_mem.total > 0 and swap_mem.percent > warning_threshold:
                alerts.append({
                    'type': 'swap_memory',
                    'level': 'warning',
                    'message': f"High swap usage: {swap_mem.percent:.1f}%",
                    'current_value': swap_mem.percent,
                    'threshold': warning_threshold
                })

            # Available memory too low
            available_gb = virtual_mem.available / (1024**3)
            if available_gb < 0.5:  # Less than 500MB available
                alerts.append({
                    'type': 'low_available',
                    'level': 'critical',
                    'message': f"Very low available memory: {available_gb:.2f} GB",
                    'current_value': available_gb,
                    'threshold': 0.5
                })
            elif available_gb < 1.0:  # Less than 1GB available
                alerts.append({
                    'type': 'low_available',
                    'level': 'warning',
                    'message': f"Low available memory: {available_gb:.2f} GB",
                    'current_value': available_gb,
                    'threshold': 1.0
                })

            return {
                'timestamp': datetime.now().isoformat(),
                'virtual_memory_percent': virtual_mem.percent,
                'swap_memory_percent': swap_mem.percent,
                'available_memory_gb': available_gb,
                'thresholds': {
                    'warning': warning_threshold,
                    'critical': critical_threshold
                },
                'alerts': alerts,
                'alert_count': len(alerts)
            }

        except Exception as e:
            self.logger.error(f"Error checking memory alerts: {e}")
            return {"error": str(e)}

    def get_memory_recommendations(self) -> Dict[str, Any]:
        """Get memory optimization recommendations"""
        try:
            virtual_mem = psutil.virtual_memory()
            swap_mem = psutil.swap_memory()
            recommendations = []

            # High memory usage recommendations
            if virtual_mem.percent > 85:
                recommendations.append({
                    'type': 'high_usage',
                    'message': "Consider closing unnecessary applications or adding more RAM",
                    'priority': 'high'
                })

            # Swap usage recommendations
            if swap_mem.total > 0 and swap_mem.percent > 50:
                recommendations.append({
                    'type': 'swap_usage',
                    'message': "High swap usage detected. Consider adding more RAM for better performance",
                    'priority': 'medium'
                })

            # No swap recommendations
            if swap_mem.total == 0:
                recommendations.append({
                    'type': 'no_swap',
                    'message': "No swap space configured. Consider adding swap for better stability",
                    'priority': 'low'
                })

            # Memory fragmentation (Linux specific)
            if hasattr(virtual_mem, 'buffers') and hasattr(virtual_mem, 'cached'):
                cache_percent = ((virtual_mem.buffers + virtual_mem.cached) / virtual_mem.total) * 100
                if cache_percent > 30:
                    recommendations.append({
                        'type': 'cache_optimization',
                        'message': f"High cache usage ({cache_percent:.1f}%). This is generally good but can be cleared if needed",
                        'priority': 'info'
                    })

            return {
                'timestamp': datetime.now().isoformat(),
                'recommendations': recommendations,
                'recommendation_count': len(recommendations)
            }

        except Exception as e:
            self.logger.error(f"Error getting memory recommendations: {e}")
            return {"error": str(e)}

    @staticmethod
    def _bytes_to_human(bytes_value: int) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"

    @staticmethod
    def _get_memory_status(percent: float) -> str:
        """Get memory status based on percentage"""
        if percent >= 95:
            return "Critical"
        elif percent >= 85:
            return "High"
        elif percent >= 70:
            return "Moderate"
        else:
            return "Normal"

    @staticmethod
    def _get_overall_memory_status(virtual_percent: float, swap_percent: float) -> str:
        """Get overall memory status"""
        if virtual_percent >= 95 or swap_percent >= 95:
            return "Critical"
        elif virtual_percent >= 85 or swap_percent >= 85:
            return "High"
        elif virtual_percent >= 70 or swap_percent >= 70:
            return "Moderate"
        else:
            return "Normal"


# Example usage
if __name__ == "__main__":
    monitor = MemoryMonitor()

    print("=== Memory Information ===")
    info = monitor.get_memory_info()
    print(json.dumps(info, indent=2))

    print("\n=== Memory Usage ===")
    usage = monitor.get_memory_usage()
    print(json.dumps(usage, indent=2))

    print("\n=== Top Memory Processes ===")
    top_processes = monitor.get_top_memory_processes(5)
    print(json.dumps(top_processes, indent=2))

    print("\n=== Memory by Category ===")
    by_category = monitor.get_memory_by_category()
    print(json.dumps(by_category, indent=2))

    print("\n=== Memory Alerts ===")
    alerts = monitor.get_memory_alerts()
    print(json.dumps(alerts, indent=2))

    print("\n=== Memory Recommendations ===")
    recommendations = monitor.get_memory_recommendations()
    print(json.dumps(recommendations, indent=2))