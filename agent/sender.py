import aiohttp
import asyncio
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MetricsSender:
    def __init__(self, config):
        self.config = config
        self.session = None
        self.registered = False
    
    async def __aenter__(self):
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()
    
    async def start_session(self):
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(
            ssl=False if self.config.api_endpoint.startswith('http://') else True,
            limit=10
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                'User-Agent': f'RPI-Monitor-Agent/{self.config.agent_version}',
                'Content-Type': 'application/json'
            }
        )
    
    async def close_session(self):
        if self.session:
            await self.session.close()
    
    async def register_device(self, system_info: Dict[str, Any]) -> bool:
        if not self.session:
            await self.start_session()
        
        try:
            url = f"{self.config.api_endpoint}/api/v1/agent/register"
            
            payload = {
                'device_id': self.config.device_id,
                **system_info
            }
            
            logger.info(f"Registering device with endpoint: {url}")
            
            async with self.session.post(
                url,
                json=payload,
                headers={'X-API-Key': self.config.api_key}
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Device registered successfully: {result}")
                    self.registered = True
                    return True
                
                elif response.status == 409:
                    logger.info("Device already registered")
                    self.registered = True
                    return True
                
                else:
                    error_text = await response.text()
                    logger.error(f"Registration failed: {response.status} - {error_text}")
                    return False
        
        except asyncio.TimeoutError:
            logger.error("Registration timeout")
            return False
        
        except aiohttp.ClientError as e:
            logger.error(f"Registration network error: {e}")
            return False
        
        except Exception as e:
            logger.error(f"Registration unexpected error: {e}")
            return False
    
    async def send_metrics(self, metrics: Dict[str, Any]) -> bool:
        if not self.session:
            await self.start_session()
        
        if not self.registered:
            logger.warning("Device not registered, skipping metrics send")
            return False
        
        try:
            url = f"{self.config.api_endpoint}/api/v1/metrics/submit"
            
            async with self.session.post(
                url,
                json=metrics,
                headers={'X-API-Key': self.config.api_key}
            ) as response:
                
                if response.status == 200:
                    return True
                
                elif response.status == 401:
                    logger.error("Authentication failed - invalid API key")
                    self.registered = False
                    return False
                
                elif response.status == 404:
                    logger.warning("Device not found, re-registration required")
                    self.registered = False
                    return False
                
                else:
                    error_text = await response.text()
                    logger.error(f"Metrics send failed: {response.status} - {error_text}")
                    return False
        
        except asyncio.TimeoutError:
            logger.warning("Metrics send timeout")
            return False
        
        except aiohttp.ClientError as e:
            logger.error(f"Metrics send network error: {e}")
            return False
        
        except Exception as e:
            logger.error(f"Metrics send unexpected error: {e}")
            return False
    
    async def send_heartbeat(self) -> bool:
        if not self.session:
            await self.start_session()
        
        try:
            url = f"{self.config.api_endpoint}/api/v1/agent/heartbeat"
            
            payload = {
                'device_id': self.config.device_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            async with self.session.post(
                url,
                json=payload,
                headers={'X-API-Key': self.config.api_key}
            ) as response:
                
                return response.status == 200
        
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            return False
    
    async def get_device_config(self) -> Optional[Dict[str, Any]]:
        if not self.session:
            await self.start_session()
        
        try:
            url = f"{self.config.api_endpoint}/api/v1/agent/config"
            
            async with self.session.get(
                url,
                headers={'X-API-Key': self.config.api_key}
            ) as response:
                
                if response.status == 200:
                    return await response.json()
                
                return None
        
        except Exception as e:
            logger.error(f"Config fetch error: {e}")
            return None
    
    async def report_error(self, error_type: str, error_message: str) -> bool:
        if not self.session:
            await self.start_session()
        
        try:
            url = f"{self.config.api_endpoint}/api/v1/agent/error"
            
            payload = {
                'device_id': self.config.device_id,
                'error_type': error_type,
                'error_message': error_message,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            async with self.session.post(
                url,
                json=payload,
                headers={'X-API-Key': self.config.api_key}
            ) as response:
                
                return response.status == 200
        
        except Exception as e:
            logger.error(f"Error report failed: {e}")
            return False