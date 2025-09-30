#!/usr/bin/env python3
"""
RAPIAMS Agent - Enhanced Main Module
Complete monitoring solution with all Telegram bot modules migrated
"""

import asyncio
import json
import logging
import signal
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional
import threading

# Import existing enhanced modules
from enhanced_config import EnhancedAgentConfig
from enhanced_collector import EnhancedMetricsCollector
from enhanced_sender import EnhancedMetricsSender

# Import new monitoring modules
from modules import (
    SystemMonitor, CPUMonitor, MemoryMonitor, DiskMonitor,
    NetworkMonitor, TemperatureMonitor, UserManager,
    initialize_all_monitors, get_available_modules
)


class RAPIAMSAgent:
    """Enhanced RAPIAMS Agent with comprehensive monitoring capabilities"""

    def __init__(self, config_path: str = "enhanced_config.py"):
        self.config = EnhancedAgentConfig()
        self.collector = EnhancedMetricsCollector(self.config)
        self.sender = EnhancedMetricsSender(self.config)

        # Initialize monitoring modules
        self.monitors = {}
        self.monitoring_threads = {}
        self.running = False

        # Setup logging
        self._setup_logging()

        # Initialize signal handlers
        self._setup_signal_handlers()

        # Initialize all monitoring modules
        self._initialize_monitors()

        self.logger.info("RAPIAMS Agent initialized with enhanced monitoring")

    def _setup_logging(self):
        """Setup enhanced logging configuration"""
        log_level = getattr(logging, self.config.LOG_LEVEL.upper(), logging.INFO)

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/var/log/rapiams-agent.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger(__name__)

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()

    def _initialize_monitors(self):
        """Initialize all available monitoring modules"""
        try:
            # Initialize core system monitors
            self.monitors['system'] = SystemMonitor()
            self.monitors['cpu'] = CPUMonitor(history_size=self.config.HISTORY_SIZE)
            self.monitors['memory'] = MemoryMonitor(history_size=self.config.HISTORY_SIZE)
            self.monitors['disk'] = DiskMonitor(history_size=self.config.HISTORY_SIZE)
            self.monitors['network'] = NetworkMonitor(history_size=self.config.HISTORY_SIZE)
            self.monitors['temperature'] = TemperatureMonitor(history_size=self.config.HISTORY_SIZE)
            self.monitors['users'] = UserManager(history_size=self.config.HISTORY_SIZE)

            # Initialize legacy monitors if available
            try:
                legacy_monitors = initialize_all_monitors()
                for name, monitor in legacy_monitors.items():
                    if name not in self.monitors:
                        self.monitors[name] = monitor
            except Exception as e:
                self.logger.warning(f"Some legacy monitors could not be initialized: {e}")

            self.logger.info(f"Initialized {len(self.monitors)} monitoring modules")

        except Exception as e:
            self.logger.error(f"Error initializing monitors: {e}")
            raise

    async def start(self):
        """Start the enhanced agent with all monitoring capabilities"""
        self.logger.info("Starting RAPIAMS Agent with enhanced monitoring...")
        self.running = True

        try:
            # Start individual monitor threads
            await self._start_monitoring_threads()

            # Start main collection and sending loop
            await self._run_main_loop()

        except Exception as e:
            self.logger.error(f"Error in main agent loop: {e}")
        finally:
            await self.stop()

    async def _start_monitoring_threads(self):
        """Start background monitoring threads for each module"""
        try:
            # Start CPU monitoring
            if 'cpu' in self.monitors:
                self.monitors['cpu'].start_monitoring(interval=self.config.CPU_MONITOR_INTERVAL)

            # Start memory monitoring
            if 'memory' in self.monitors:
                self.monitors['memory'].start_monitoring(interval=self.config.MEMORY_MONITOR_INTERVAL)

            # Start disk monitoring
            if 'disk' in self.monitors:
                self.monitors['disk'].start_monitoring(interval=self.config.DISK_MONITOR_INTERVAL)

            # Start network monitoring
            if 'network' in self.monitors:
                self.monitors['network'].start_monitoring(interval=self.config.NETWORK_MONITOR_INTERVAL)

            # Start temperature monitoring
            if 'temperature' in self.monitors:
                self.monitors['temperature'].start_monitoring(interval=self.config.TEMPERATURE_MONITOR_INTERVAL)

            # Start user monitoring
            if 'users' in self.monitors:
                self.monitors['users'].start_monitoring(interval=self.config.USER_MONITOR_INTERVAL)

            self.logger.info("All monitoring threads started")

        except Exception as e:
            self.logger.error(f"Error starting monitoring threads: {e}")

    async def _run_main_loop(self):
        """Main collection and sending loop"""
        while self.running:
            try:
                # Collect comprehensive metrics
                metrics = await self._collect_comprehensive_metrics()

                # Send metrics to backend
                if metrics:
                    success = await self.sender.send_enhanced_metrics(metrics)
                    if success:
                        self.logger.debug("Metrics sent successfully")
                    else:
                        self.logger.warning("Failed to send metrics")

                # Wait for next collection cycle
                await asyncio.sleep(self.config.COLLECTION_INTERVAL)

            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(self.config.ERROR_RETRY_INTERVAL)

    async def _collect_comprehensive_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive metrics from all monitoring modules"""
        try:
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'device_id': self.config.DEVICE_ID,
                'agent_version': '2.0.0',
                'modules': {}
            }

            # Collect basic metrics using existing collector
            basic_metrics = await self.collector.collect_all_metrics()
            if basic_metrics:
                metrics['basic'] = basic_metrics

            # Collect enhanced metrics from new modules
            await self._collect_system_metrics(metrics)
            await self._collect_performance_metrics(metrics)
            await self._collect_security_metrics(metrics)
            await self._collect_user_metrics(metrics)

            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting comprehensive metrics: {e}")
            return {}

    async def _collect_system_metrics(self, metrics: Dict[str, Any]):
        """Collect system-level metrics"""
        try:
            if 'system' in self.monitors:
                # System information
                system_info = self.monitors['system'].get_system_info()
                metrics['modules']['system'] = {
                    'info': system_info,
                    'health': self.monitors['system'].get_system_health_status(),
                    'performance': self.monitors['system'].get_system_performance_summary()
                }

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")

    async def _collect_performance_metrics(self, metrics: Dict[str, Any]):
        """Collect performance metrics from CPU, memory, disk, network"""
        try:
            # CPU metrics
            if 'cpu' in self.monitors:
                metrics['modules']['cpu'] = {
                    'usage': self.monitors['cpu'].get_cpu_usage(),
                    'info': self.monitors['cpu'].get_cpu_info(),
                    'load_average': self.monitors['cpu'].get_cpu_load_average(),
                    'alerts': self.monitors['cpu'].get_cpu_alerts(),
                    'temperature': self.monitors['cpu'].get_cpu_temperature()
                }

            # Memory metrics
            if 'memory' in self.monitors:
                metrics['modules']['memory'] = {
                    'usage': self.monitors['memory'].get_memory_usage(),
                    'info': self.monitors['memory'].get_memory_info(),
                    'top_processes': self.monitors['memory'].get_top_memory_processes(10),
                    'alerts': self.monitors['memory'].get_memory_alerts(),
                    'recommendations': self.monitors['memory'].get_memory_recommendations()
                }

            # Disk metrics
            if 'disk' in self.monitors:
                metrics['modules']['disk'] = {
                    'info': self.monitors['disk'].get_disk_info(),
                    'usage': self.monitors['disk'].get_disk_usage('/'),
                    'io_stats': self.monitors['disk'].get_disk_io_stats(),
                    'alerts': self.monitors['disk'].get_disk_alerts()
                }

            # Network metrics
            if 'network' in self.monitors:
                metrics['modules']['network'] = {
                    'interfaces': self.monitors['network'].get_network_interfaces(),
                    'io_stats': self.monitors['network'].get_network_io_stats(),
                    'connections': self.monitors['network'].get_network_connections(),
                    'connectivity': self.monitors['network'].test_connectivity(['8.8.8.8', 'google.com']),
                    'alerts': self.monitors['network'].get_network_alerts()
                }

            # Temperature metrics
            if 'temperature' in self.monitors:
                metrics['modules']['temperature'] = {
                    'all_sensors': self.monitors['temperature'].get_all_temperatures(),
                    'cpu_temperature': self.monitors['temperature'].get_cpu_temperature(),
                    'alerts': self.monitors['temperature'].get_temperature_alerts(),
                    'throttling': self.monitors['temperature'].get_thermal_throttling_status()
                }

        except Exception as e:
            self.logger.error(f"Error collecting performance metrics: {e}")

    async def _collect_security_metrics(self, metrics: Dict[str, Any]):
        """Collect security-related metrics"""
        try:
            if 'users' in self.monitors:
                metrics['modules']['security'] = {
                    'user_security': self.monitors['users'].get_user_security_info(),
                    'active_users': self.monitors['users'].get_active_users(),
                    'login_history': self.monitors['users'].get_login_history(days=1)
                }

        except Exception as e:
            self.logger.error(f"Error collecting security metrics: {e}")

    async def _collect_user_metrics(self, metrics: Dict[str, Any]):
        """Collect user management metrics"""
        try:
            if 'users' in self.monitors:
                metrics['modules']['users'] = {
                    'all_users': self.monitors['users'].get_all_users(),
                    'groups': self.monitors['users'].get_user_groups()
                }

        except Exception as e:
            self.logger.error(f"Error collecting user metrics: {e}")

    async def stop(self):
        """Stop the agent and cleanup resources"""
        self.logger.info("Stopping RAPIAMS Agent...")
        self.running = False

        try:
            # Stop all monitoring threads
            for name, monitor in self.monitors.items():
                if hasattr(monitor, 'stop_monitoring'):
                    try:
                        monitor.stop_monitoring()
                        self.logger.debug(f"Stopped {name} monitor")
                    except Exception as e:
                        self.logger.warning(f"Error stopping {name} monitor: {e}")

            # Stop collector and sender
            if hasattr(self.collector, 'stop'):
                await self.collector.stop()

            if hasattr(self.sender, 'stop'):
                await self.sender.stop()

            self.logger.info("RAPIAMS Agent stopped successfully")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the agent and all monitors"""
        try:
            status = {
                'timestamp': datetime.utcnow().isoformat(),
                'agent_running': self.running,
                'available_modules': get_available_modules(),
                'active_monitors': list(self.monitors.keys()),
                'config': {
                    'device_id': self.config.DEVICE_ID,
                    'collection_interval': self.config.COLLECTION_INTERVAL,
                    'backend_url': self.config.BACKEND_URL
                }
            }

            # Add monitor-specific status
            for name, monitor in self.monitors.items():
                if hasattr(monitor, 'get_status'):
                    try:
                        status[f'{name}_status'] = monitor.get_status()
                    except:
                        pass

            return status

        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {"error": str(e)}

    async def execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command received from the backend"""
        try:
            command_type = command.get('type')
            command_params = command.get('parameters', {})

            self.logger.info(f"Executing command: {command_type}")

            if command_type == 'get_status':
                return self.get_status()

            elif command_type == 'get_system_info':
                if 'system' in self.monitors:
                    return self.monitors['system'].get_system_info()

            elif command_type == 'get_performance_summary':
                if 'system' in self.monitors:
                    return self.monitors['system'].get_system_performance_summary()

            elif command_type == 'restart_monitoring':
                await self._restart_monitoring()
                return {"success": True, "message": "Monitoring restarted"}

            elif command_type == 'update_config':
                # Update configuration
                for key, value in command_params.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
                return {"success": True, "message": "Configuration updated"}

            else:
                return {"error": f"Unknown command type: {command_type}"}

        except Exception as e:
            self.logger.error(f"Error executing command {command.get('type')}: {e}")
            return {"error": str(e)}

    async def _restart_monitoring(self):
        """Restart all monitoring threads"""
        try:
            # Stop existing monitoring
            for monitor in self.monitors.values():
                if hasattr(monitor, 'stop_monitoring'):
                    monitor.stop_monitoring()

            # Wait a moment
            await asyncio.sleep(2)

            # Restart monitoring
            await self._start_monitoring_threads()

            self.logger.info("Monitoring restarted successfully")

        except Exception as e:
            self.logger.error(f"Error restarting monitoring: {e}")


async def main():
    """Main entry point for the enhanced RAPIAMS Agent"""
    try:
        # Create and start the agent
        agent = RAPIAMSAgent()

        print("🚀 Starting RAPIAMS Agent v2.0.0 with comprehensive monitoring...")
        print(f"📊 Available modules: {', '.join(get_available_modules().keys())}")

        await agent.start()

    except KeyboardInterrupt:
        print("\n⏹️  Agent stopped by user")
    except Exception as e:
        print(f"❌ Error starting agent: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())