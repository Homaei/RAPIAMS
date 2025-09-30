#!/usr/bin/env python3
"""
Advanced Raspberry Pi Monitoring Agent - Enhanced Version
Adapted from Telegram monitoring system for API backend integration

Description: Production-ready Raspberry Pi monitoring agent with comprehensive
metrics collection, alert management, and API integration
"""

import asyncio
import logging
import logging.config
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
import time

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_config import AgentConfig, MONITORING_CONFIG, LOGGING_CONFIG
from enhanced_collector import EnhancedMetricsCollector
from enhanced_sender import EnhancedMetricsSender
from monitoring_modules import (
    SystemMonitor, CPUMonitor, MemoryMonitor, DiskMonitor,
    NetworkMonitor, ProcessMonitor, ServiceMonitor,
    TemperatureMonitor, SecurityMonitor, AlertManager
)
from utils.helpers import safe_execute, format_time, get_hostname

# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('monitoring.agent')


class EnhancedMonitoringAgent:
    """Enhanced Raspberry Pi Monitoring Agent with comprehensive error handling"""

    def __init__(self):
        """Initialize the monitoring agent"""
        logger.info("Initializing Enhanced Raspberry Pi Monitor Agent...")

        # Load configuration
        self.config = AgentConfig()
        
        # Initialize monitoring modules
        self.system_monitor = SystemMonitor()
        self.cpu_monitor = CPUMonitor()
        self.memory_monitor = MemoryMonitor()
        self.disk_monitor = DiskMonitor()
        self.network_monitor = NetworkMonitor()
        self.process_monitor = ProcessMonitor()
        self.service_monitor = ServiceMonitor()
        self.temperature_monitor = TemperatureMonitor()
        self.security_monitor = SecurityMonitor()
        self.alert_manager = AlertManager()

        # Initialize communication components
        self.collector = EnhancedMetricsCollector(self.config, {
            'system': self.system_monitor,
            'cpu': self.cpu_monitor,
            'memory': self.memory_monitor,
            'disk': self.disk_monitor,
            'network': self.network_monitor,
            'process': self.process_monitor,
            'service': self.service_monitor,
            'temperature': self.temperature_monitor,
            'security': self.security_monitor
        })
        
        self.sender = EnhancedMetricsSender(self.config)
        
        # Runtime state
        self.running = False
        self.tasks = []
        self.last_heartbeat = None
        self.failure_count = 0
        self.max_failures = 10
        
        # Performance metrics
        self.metrics_sent = 0
        self.alerts_generated = 0
        self.start_time = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Agent initialized for device: {self.config.device_id}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()

    async def initialize(self) -> bool:
        """Initialize agent and all components"""
        try:
            logger.info("Starting agent initialization...")
            
            # Initialize monitoring modules
            if not await self._initialize_modules():
                logger.error("Failed to initialize monitoring modules")
                return False
            
            # Initialize communication
            if not await self.sender.initialize():
                logger.error("Failed to initialize API sender")
                return False
            
            # Register device with backend
            system_info = await self.collector.get_system_info()
            if not await self.sender.register_device(system_info):
                logger.error("Failed to register device with backend")
                return False
            
            logger.info("Agent initialization completed successfully")
            self.start_time = datetime.utcnow()
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {str(e)}")
            return False

    async def _initialize_modules(self) -> bool:
        """Initialize all monitoring modules"""
        modules = [
            ('System', self.system_monitor),
            ('CPU', self.cpu_monitor),
            ('Memory', self.memory_monitor),
            ('Disk', self.disk_monitor),
            ('Network', self.network_monitor),
            ('Process', self.process_monitor),
            ('Service', self.service_monitor),
            ('Temperature', self.temperature_monitor),
            ('Security', self.security_monitor),
            ('Alert Manager', self.alert_manager)
        ]

        failed_modules = []
        for name, module in modules:
            try:
                if hasattr(module, 'initialize'):
                    success = await module.initialize()
                    if success:
                        logger.debug(f"✅ {name} module initialized")
                    else:
                        logger.warning(f"⚠️ {name} module initialization failed")
                        failed_modules.append(name)
                else:
                    logger.debug(f"✅ {name} module (no initialization required)")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {name}: {str(e)}")
                failed_modules.append(name)
        
        if failed_modules:
            logger.warning(f"Some modules failed to initialize: {failed_modules}")
            # Continue with partial functionality
        
        return True  # Allow partial functionality

    async def start(self):
        """Start the monitoring agent"""
        logger.info(f"Starting Enhanced Raspberry Pi Monitor Agent v{self.config.agent_version}")
        logger.info(f"Device ID: {self.config.device_id}")
        logger.info(f"API Endpoint: {self.config.api_endpoint}")
        logger.info(f"Collection Interval: {self.config.collection_interval}s")
        
        # Initialize agent
        if not await self.initialize():
            logger.error("Agent initialization failed")
            return False
        
        self.running = True
        
        # Start background tasks
        self.tasks = [
            asyncio.create_task(self._metrics_collection_loop()),
            asyncio.create_task(self._alert_monitoring_loop()),
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._cleanup_loop())
        ]
        
        try:
            # Wait for all tasks to complete
            await asyncio.gather(*self.tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            await self.stop()
    
    async def _metrics_collection_loop(self):
        """Main metrics collection and sending loop"""
        logger.info("Starting metrics collection loop...")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Collect comprehensive metrics
                metrics = await self.collector.collect_all_metrics()
                
                if metrics:
                    # Send metrics to backend
                    success = await self.sender.send_metrics(metrics)
                    
                    if success:
                        self.metrics_sent += 1
                        self.failure_count = 0
                        
                        collection_time = time.time() - start_time
                        logger.debug(f"Metrics collected and sent in {collection_time:.2f}s")
                        
                        # Log summary every 100 metrics
                        if self.metrics_sent % 100 == 0:
                            uptime = datetime.utcnow() - self.start_time
                            logger.info(f"📊 Metrics sent: {self.metrics_sent}, "
                                      f"Alerts: {self.alerts_generated}, "
                                      f"Uptime: {format_time(uptime.total_seconds())}")
                    else:
                        self.failure_count += 1
                        logger.warning(f"Failed to send metrics (failure {self.failure_count}/{self.max_failures})")
                        
                        # Try to re-register after too many failures
                        if self.failure_count >= self.max_failures:
                            logger.warning("Max failures reached, attempting re-registration...")
                            system_info = await self.collector.get_system_info()
                            await self.sender.register_device(system_info)
                            self.failure_count = 0
                else:
                    logger.warning("No metrics collected")
                
                # Sleep until next collection
                await asyncio.sleep(self.config.collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(min(60, self.config.collection_interval))
        
        logger.info("Metrics collection loop stopped")
    
    async def _alert_monitoring_loop(self):
        """Monitor for alerts and send notifications"""
        logger.info("Starting alert monitoring loop...")
        
        while self.running:
            try:
                if MONITORING_CONFIG.enable_alerts:
                    # Check for system alerts
                    alerts = await self.alert_manager.check_all_alerts({
                        'system': self.system_monitor,
                        'cpu': self.cpu_monitor,
                        'memory': self.memory_monitor,
                        'disk': self.disk_monitor,
                        'network': self.network_monitor,
                        'temperature': self.temperature_monitor,
                        'security': self.security_monitor
                    })
                    
                    for alert in alerts:
                        # Send alert to backend
                        success = await self.sender.send_alert(alert)
                        if success:
                            self.alerts_generated += 1
                            logger.info(f"🚨 Alert sent: {alert['type']} - {alert['message']}")
                        else:
                            logger.error(f"Failed to send alert: {alert['type']}")
                
                # Sleep for alert check interval
                await asyncio.sleep(MONITORING_CONFIG.alert_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert monitoring loop: {e}")
                await asyncio.sleep(60)
        
        logger.info("Alert monitoring loop stopped")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat to backend"""
        logger.info("Starting heartbeat loop...")
        
        while self.running:
            try:
                # Send heartbeat
                heartbeat_data = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'agent_version': self.config.agent_version,
                    'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0,
                    'metrics_sent': self.metrics_sent,
                    'alerts_generated': self.alerts_generated,
                    'status': 'healthy'
                }
                
                success = await self.sender.send_heartbeat(heartbeat_data)
                if success:
                    self.last_heartbeat = datetime.utcnow()
                    logger.debug("💓 Heartbeat sent")
                else:
                    logger.warning("Failed to send heartbeat")
                
                # Sleep for heartbeat interval
                await asyncio.sleep(MONITORING_CONFIG.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(300)  # 5 minutes on error
        
        logger.info("Heartbeat loop stopped")
    
    async def _health_check_loop(self):
        """Perform periodic health checks"""
        logger.info("Starting health check loop...")
        
        while self.running:
            try:
                # Check system health
                health_status = await self._perform_health_check()
                
                if health_status['status'] == 'critical':
                    logger.critical(f"🚨 Critical health issue: {health_status['issues']}")
                    # Send critical alert
                    alert = {
                        'type': 'system_health',
                        'severity': 'critical',
                        'message': f"System health critical: {', '.join(health_status['issues'])}",
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    await self.sender.send_alert(alert)
                
                elif health_status['status'] == 'warning':
                    logger.warning(f"⚠️ Health warnings: {health_status['issues']}")
                
                # Sleep for health check interval
                await asyncio.sleep(MONITORING_CONFIG.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(300)
        
        logger.info("Health check loop stopped")
    
    async def _cleanup_loop(self):
        """Perform periodic cleanup tasks"""
        logger.info("Starting cleanup loop...")
        
        while self.running:
            try:
                if MONITORING_CONFIG.enable_auto_cleanup:
                    # Clean old log files
                    await self._cleanup_old_files()
                    
                    # Clean temporary files
                    await self._cleanup_temp_files()
                    
                    logger.debug("🧹 Cleanup completed")
                
                # Sleep for cleanup interval
                await asyncio.sleep(MONITORING_CONFIG.cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(3600)  # 1 hour on error
        
        logger.info("Cleanup loop stopped")
    
    @safe_execute
    async def _perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        issues = []
        
        try:
            # Check disk space
            disk_info = await self.disk_monitor.get_disk_usage()
            if disk_info and disk_info.get('/'):
                disk_usage = disk_info['/']['percent']
                if disk_usage > 95:
                    issues.append(f"Disk usage critical: {disk_usage}%")
                elif disk_usage > 85:
                    issues.append(f"Disk usage high: {disk_usage}%")
            
            # Check memory usage
            memory_info = await self.memory_monitor.get_memory_info()
            if memory_info:
                memory_usage = memory_info.get('percent', 0)
                if memory_usage > 95:
                    issues.append(f"Memory usage critical: {memory_usage}%")
                elif memory_usage > 85:
                    issues.append(f"Memory usage high: {memory_usage}%")
            
            # Check CPU temperature
            temp_info = await self.temperature_monitor.get_cpu_temperature()
            if temp_info:
                temp = temp_info.get('celsius', 0)
                if temp > 85:
                    issues.append(f"CPU temperature critical: {temp}°C")
                elif temp > 75:
                    issues.append(f"CPU temperature high: {temp}°C")
            
            # Check network connectivity
            network_status = await self.network_monitor.check_connectivity()
            if not network_status.get('internet_connected', True):
                issues.append("No internet connectivity")
            
            # Determine overall status
            if any('critical' in issue for issue in issues):
                status = 'critical'
            elif issues:
                status = 'warning'
            else:
                status = 'healthy'
            
            return {
                'status': status,
                'issues': issues,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            return {
                'status': 'unknown',
                'issues': [f"Health check failed: {str(e)}"],
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @safe_execute
    async def _cleanup_old_files(self):
        """Clean up old log and temporary files"""
        # Implementation for cleaning old files
        pass
    
    @safe_execute
    async def _cleanup_temp_files(self):
        """Clean up temporary files"""
        # Implementation for cleaning temp files
        pass
    
    async def stop(self):
        """Stop the monitoring agent gracefully"""
        logger.info("Stopping Enhanced Monitoring Agent...")
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close connections
        if hasattr(self.sender, 'close'):
            await self.sender.close()
        
        # Log final statistics
        if self.start_time:
            uptime = datetime.utcnow() - self.start_time
            logger.info(f"📊 Final stats - Uptime: {format_time(uptime.total_seconds())}, "
                       f"Metrics sent: {self.metrics_sent}, "
                       f"Alerts generated: {self.alerts_generated}")
        
        logger.info("Enhanced Monitoring Agent stopped")


async def main():
    """Main entry point"""
    agent = EnhancedMonitoringAgent()
    
    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("Agent terminated by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
    finally:
        if agent.running:
            await agent.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Agent terminated by user")
    except Exception as e:
        logger.error(f"Failed to run agent: {e}")
        sys.exit(1)