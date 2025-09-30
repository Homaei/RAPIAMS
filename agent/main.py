#!/usr/bin/env python3

import asyncio
import logging
import signal
import sys
from datetime import datetime
import os

from collector import MetricsCollector
from sender import MetricsSender
from config import AgentConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MonitoringAgent:
    def __init__(self):
        self.config = AgentConfig()
        self.collector = MetricsCollector(self.config)
        self.sender = MetricsSender(self.config)
        self.running = False
        self.tasks = []
    
    async def start(self):
        logger.info(f"Starting Raspberry Pi Monitoring Agent v{self.config.agent_version}")
        logger.info(f"Device ID: {self.config.device_id}")
        logger.info(f"API Endpoint: {self.config.api_endpoint}")
        logger.info(f"Collection Interval: {self.config.collection_interval}s")
        
        await self.sender.register_device(self.collector.get_system_info())
        
        self.running = True
        
        collection_task = asyncio.create_task(self.collection_loop())
        health_task = asyncio.create_task(self.health_check_loop())
        
        self.tasks = [collection_task, health_task]
        
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            logger.info("Agent tasks cancelled")
    
    async def collection_loop(self):
        failures = 0
        max_failures = 10
        
        while self.running:
            try:
                metrics = await self.collector.collect_metrics()
                
                success = await self.sender.send_metrics(metrics)
                
                if success:
                    failures = 0
                    logger.debug(f"Metrics sent successfully at {datetime.now()}")
                else:
                    failures += 1
                    logger.warning(f"Failed to send metrics (attempt {failures}/{max_failures})")
                    
                    if failures >= max_failures:
                        logger.error("Max failures reached, attempting to re-register device")
                        await self.sender.register_device(self.collector.get_system_info())
                        failures = 0
                
                await asyncio.sleep(self.config.collection_interval)
            
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                await asyncio.sleep(self.config.collection_interval)
    
    async def health_check_loop(self):
        while self.running:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                disk_usage = self.collector.get_disk_usage()
                if disk_usage and disk_usage.get('percent', 0) > 95:
                    logger.critical(f"Disk usage critical: {disk_usage['percent']}%")
                
                temp = self.collector.get_cpu_temperature()
                if temp and temp > 80:
                    logger.critical(f"CPU temperature critical: {temp}°C")
                
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
    
    async def stop(self):
        logger.info("Stopping agent...")
        self.running = False
        
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info("Agent stopped")


def signal_handler(agent):
    def handler(signum, frame):
        logger.info(f"Received signal {signum}")
        asyncio.create_task(agent.stop())
        sys.exit(0)
    return handler


async def main():
    agent = MonitoringAgent()
    
    signal.signal(signal.SIGINT, signal_handler(agent))
    signal.signal(signal.SIGTERM, signal_handler(agent))
    
    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await agent.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Agent terminated by user")
    except Exception as e:
        logger.error(f"Failed to run agent: {e}")
        sys.exit(1)