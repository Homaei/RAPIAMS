"""
Enhanced Metrics Sender - Advanced API communication with retry logic
Adapted from Telegram monitoring system for API backend integration
"""

import aiohttp
import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

logger = logging.getLogger('monitoring.sender')


class EnhancedMetricsSender:
    """Enhanced metrics sender with advanced features and error handling"""

    def __init__(self, config):
        """
        Initialize the enhanced metrics sender
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.session = None
        self.registered = False
        self.last_successful_send = None
        self.consecutive_failures = 0
        self.logger = logger
        
        # API endpoints
        self.base_url = config.api_endpoint.rstrip('/')
        self.endpoints = {
            'register': f"{self.base_url}/api/v1/agent/register",
            'metrics': f"{self.base_url}/api/v1/metrics/submit",
            'heartbeat': f"{self.base_url}/api/v1/agent/heartbeat",
            'alert': f"{self.base_url}/api/v1/agent/alert",
            'status': f"{self.base_url}/api/v1/agent/status",
            'config': f"{self.base_url}/api/v1/agent/config",
            'error': f"{self.base_url}/api/v1/agent/error"
        }
        
        # Request statistics
        self.stats = {
            'requests_sent': 0,
            'requests_successful': 0,
            'requests_failed': 0,
            'bytes_sent': 0,
            'last_request_time': None,
            'avg_response_time': 0.0,
            'response_times': []
        }
    
    async def initialize(self) -> bool:
        """Initialize the HTTP session"""
        try:
            # Create session with custom settings
            timeout = aiohttp.ClientTimeout(
                total=self.config.timeout if hasattr(self.config, 'timeout') else 30,
                connect=10,
                sock_read=10
            )
            
            connector = aiohttp.TCPConnector(
                ssl=self.config.enable_ssl_verify,
                limit=10,
                limit_per_host=5,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )
            
            headers = {
                'User-Agent': f'RPI-Enhanced-Agent/{self.config.agent_version}',
                'Content-Type': 'application/json',
                'X-Agent-Version': self.config.agent_version,
                'X-Device-ID': self.config.device_id
            }
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers=headers
            )
            
            self.logger.info(f"HTTP session initialized for {self.base_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize HTTP session: {e}")
            return False
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.logger.info("HTTP session closed")
    
    async def register_device(self, system_info: Dict[str, Any]) -> bool:
        """Register device with the backend API"""
        try:
            payload = {
                'device_id': self.config.device_id,
                'agent_version': self.config.agent_version,
                'registration_time': datetime.utcnow().isoformat(),
                **system_info
            }
            
            self.logger.info(f"Registering device {self.config.device_id}...")
            
            success, response_data = await self._make_request(
                'POST',
                self.endpoints['register'],
                payload,
                use_api_key=True
            )
            
            if success:
                self.registered = True
                self.logger.info(f"✅ Device registered successfully: {response_data}")
                return True
            else:
                self.logger.error(f"❌ Device registration failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during device registration: {e}")
            return False
    
    async def send_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Send metrics to the backend API"""
        try:
            if not self.registered:
                self.logger.warning("Device not registered, cannot send metrics")
                return False
            
            # Add metadata
            payload = {
                **metrics,
                'agent_version': self.config.agent_version,
                'sent_at': datetime.utcnow().isoformat()
            }
            
            success, response_data = await self._make_request(
                'POST',
                self.endpoints['metrics'],
                payload,
                use_api_key=True
            )
            
            if success:
                self.last_successful_send = datetime.utcnow()
                self.consecutive_failures = 0
                self.logger.debug("📊 Metrics sent successfully")
                return True
            else:
                self.consecutive_failures += 1
                if self.consecutive_failures >= 5:
                    self.logger.warning(f"Multiple consecutive failures ({self.consecutive_failures}), may need re-registration")
                    self.registered = False
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending metrics: {e}")
            self.consecutive_failures += 1
            return False
    
    async def send_heartbeat(self, heartbeat_data: Dict[str, Any]) -> bool:
        """Send heartbeat to the backend API"""
        try:
            payload = {
                'device_id': self.config.device_id,
                'agent_version': self.config.agent_version,
                **heartbeat_data
            }
            
            success, response_data = await self._make_request(
                'POST',
                self.endpoints['heartbeat'],
                payload,
                use_api_key=True
            )
            
            if success:
                self.logger.debug("💓 Heartbeat sent successfully")
                return True
            else:
                self.logger.warning("Failed to send heartbeat")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending heartbeat: {e}")
            return False
    
    async def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send alert to the backend API"""
        try:
            payload = {
                'device_id': self.config.device_id,
                'agent_version': self.config.agent_version,
                'alert_time': datetime.utcnow().isoformat(),
                **alert_data
            }
            
            success, response_data = await self._make_request(
                'POST',
                self.endpoints['alert'],
                payload,
                use_api_key=True
            )
            
            if success:
                self.logger.info(f"🚨 Alert sent successfully: {alert_data.get('type', 'unknown')}")
                return True
            else:
                self.logger.error(f"Failed to send alert: {alert_data.get('type', 'unknown')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")
            return False
    
    async def send_status_update(self, status_data: Dict[str, Any]) -> bool:
        """Send status update to the backend API"""
        try:
            payload = {
                'device_id': self.config.device_id,
                'agent_version': self.config.agent_version,
                'status_time': datetime.utcnow().isoformat(),
                **status_data
            }
            
            success, response_data = await self._make_request(
                'POST',
                self.endpoints['status'],
                payload,
                use_api_key=True
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending status update: {e}")
            return False
    
    async def get_remote_config(self) -> Optional[Dict[str, Any]]:
        """Get configuration from the backend API"""
        try:
            success, response_data = await self._make_request(
                'GET',
                self.endpoints['config'],
                use_api_key=True
            )
            
            if success:
                self.logger.info("📋 Remote configuration retrieved")
                return response_data
            else:
                self.logger.warning("Failed to get remote configuration")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting remote config: {e}")
            return None
    
    async def report_error(self, error_data: Dict[str, Any]) -> bool:
        """Report error to the backend API"""
        try:
            payload = {
                'device_id': self.config.device_id,
                'agent_version': self.config.agent_version,
                'error_time': datetime.utcnow().isoformat(),
                **error_data
            }
            
            success, response_data = await self._make_request(
                'POST',
                self.endpoints['error'],
                payload,
                use_api_key=True
            )
            
            if success:
                self.logger.debug("📝 Error report sent successfully")
                return True
            else:
                self.logger.warning("Failed to send error report")
                return False
                
        except Exception as e:
            self.logger.error(f"Error reporting error: {e}")
            return False
    
    async def _make_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        use_api_key: bool = False,
        retries: int = None
    ) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Make HTTP request with retry logic and error handling"""
        
        if not self.session:
            await self.initialize()
        
        if retries is None:
            retries = self.config.max_retries
        
        headers = {}
        if use_api_key:
            headers['X-API-Key'] = self.config.api_key
        
        last_exception = None
        
        for attempt in range(retries + 1):
            try:
                start_time = time.time()
                
                # Prepare request
                kwargs = {
                    'headers': headers,
                    'ssl': self.config.enable_ssl_verify
                }
                
                if data is not None:
                    kwargs['json'] = data
                    self.stats['bytes_sent'] += len(json.dumps(data))
                
                # Make request
                async with self.session.request(method, url, **kwargs) as response:
                    
                    # Update statistics
                    response_time = time.time() - start_time
                    self.stats['requests_sent'] += 1
                    self.stats['last_request_time'] = datetime.utcnow()
                    self.stats['response_times'].append(response_time)
                    
                    # Keep only last 100 response times
                    if len(self.stats['response_times']) > 100:
                        self.stats['response_times'] = self.stats['response_times'][-100:]
                    
                    self.stats['avg_response_time'] = sum(self.stats['response_times']) / len(self.stats['response_times'])
                    
                    # Handle response
                    if response.status == 200 or response.status == 201:
                        self.stats['requests_successful'] += 1
                        
                        try:
                            response_data = await response.json()
                        except:
                            response_data = {'status': 'success'}
                        
                        self.logger.debug(f"✅ {method} {url} - {response.status} ({response_time:.3f}s)")
                        return True, response_data
                    
                    elif response.status == 401:
                        self.logger.error(f"❌ Authentication failed: Invalid API key")
                        self.registered = False
                        self.stats['requests_failed'] += 1
                        return False, None
                    
                    elif response.status == 404:
                        self.logger.warning(f"⚠️ Device not found, re-registration required")
                        self.registered = False
                        self.stats['requests_failed'] += 1
                        return False, None
                    
                    elif response.status == 429:
                        self.logger.warning(f"⚠️ Rate limited, backing off...")
                        await asyncio.sleep(min(60, (attempt + 1) * 5))
                        continue
                    
                    else:
                        error_text = await response.text()
                        self.logger.error(f"❌ {method} {url} - {response.status}: {error_text}")
                        
                        if attempt < retries:
                            await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                            continue
                        
                        self.stats['requests_failed'] += 1
                        return False, None
            
            except asyncio.TimeoutError as e:
                last_exception = e
                self.logger.warning(f"⏱️ Request timeout (attempt {attempt + 1}/{retries + 1})")
                
                if attempt < retries:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    continue
            
            except aiohttp.ClientError as e:
                last_exception = e
                self.logger.warning(f"🌐 Network error (attempt {attempt + 1}/{retries + 1}): {e}")
                
                if attempt < retries:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    continue
            
            except Exception as e:
                last_exception = e
                self.logger.error(f"💥 Unexpected error (attempt {attempt + 1}/{retries + 1}): {e}")
                
                if attempt < retries:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    continue
        
        # All retries exhausted
        self.stats['requests_failed'] += 1
        self.logger.error(f"❌ All {retries + 1} attempts failed for {method} {url}")
        
        if last_exception:
            self.logger.error(f"Last error: {last_exception}")
        
        return False, None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get sender statistics"""
        return {
            **self.stats,
            'registered': self.registered,
            'consecutive_failures': self.consecutive_failures,
            'last_successful_send': self.last_successful_send.isoformat() if self.last_successful_send else None,
            'success_rate': (self.stats['requests_successful'] / max(1, self.stats['requests_sent'])) * 100
        }
    
    async def test_connectivity(self) -> Dict[str, Any]:
        """Test connectivity to the backend API"""
        try:
            start_time = time.time()
            
            # Try to reach the health endpoint
            health_url = f"{self.base_url}/health"
            
            success, response_data = await self._make_request(
                'GET',
                health_url,
                retries=1
            )
            
            response_time = time.time() - start_time
            
            return {
                'connectivity': success,
                'response_time': response_time,
                'endpoint': health_url,
                'response_data': response_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'connectivity': False,
                'error': str(e),
                'endpoint': f"{self.base_url}/health",
                'timestamp': datetime.utcnow().isoformat()
            }