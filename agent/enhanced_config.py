"""
Enhanced Agent Configuration - Adapted from Telegram monitoring system
"""

import os
import json
import socket
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import logging

# Base paths
BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"
METRICS_DIR = DATA_DIR / "metrics"
BACKUP_DIR = DATA_DIR / "backups"

# Ensure all directories exist
for directory in [CONFIG_DIR, DATA_DIR, LOGS_DIR, METRICS_DIR, BACKUP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# System Monitoring Thresholds
@dataclass
class Thresholds:
    """System monitoring thresholds configuration"""

    cpu_temp: Dict[str, float] = field(default_factory=lambda: {
        "info": 40.0,
        "warning": 60.0,
        "critical": 75.0,
        "danger": 85.0
    })

    cpu_usage: Dict[str, float] = field(default_factory=lambda: {
        "info": 30.0,
        "warning": 70.0,
        "critical": 85.0,
        "danger": 95.0
    })

    memory_usage: Dict[str, float] = field(default_factory=lambda: {
        "info": 50.0,
        "warning": 75.0,
        "critical": 85.0,
        "danger": 95.0
    })

    disk_usage: Dict[str, float] = field(default_factory=lambda: {
        "info": 60.0,
        "warning": 75.0,
        "critical": 85.0,
        "danger": 95.0
    })

    swap_usage: Dict[str, float] = field(default_factory=lambda: {
        "info": 30.0,
        "warning": 50.0,
        "critical": 70.0,
        "danger": 90.0
    })

    network_latency: Dict[str, float] = field(default_factory=lambda: {
        "excellent": 20.0,
        "good": 50.0,
        "fair": 100.0,
        "poor": 200.0
    })

# Create global thresholds instance
THRESHOLDS = Thresholds()

# Enhanced Monitoring Configuration
@dataclass
class MonitoringConfig:
    """Enhanced monitoring system configuration"""

    # Collection intervals (in seconds)
    collection_interval: int = field(default_factory=lambda: int(os.getenv('COLLECTION_INTERVAL', '30')))
    quick_check_interval: int = 5
    normal_check_interval: int = 60
    detailed_check_interval: int = 300
    cleanup_interval: int = 86400  # 24 hours
    heartbeat_interval: int = 300  # 5 minutes
    alert_check_interval: int = 60  # 1 minute
    health_check_interval: int = 600  # 10 minutes

    # Data retention (in days)
    metrics_retention: int = 30
    logs_retention: int = 90
    reports_retention: int = 365

    # Alert settings
    alert_cooldown: int = 300  # 5 minutes between same alerts
    max_alerts_per_hour: int = 20
    enable_alerts: bool = True

    # Performance settings
    max_history_records: int = 1000
    batch_size: int = 100
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5

    # Feature flags
    enable_auto_cleanup: bool = True
    enable_metrics: bool = True
    enable_reports: bool = True
    enable_webhooks: bool = False
    enable_gpio_monitoring: bool = True
    enable_process_monitoring: bool = True
    enable_service_monitoring: bool = True
    enable_security_monitoring: bool = True

    # Security settings
    max_login_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes
    session_timeout: int = 3600  # 1 hour

    # Network settings
    public_ip_check_interval: int = 3600  # 1 hour
    network_scan_enabled: bool = False
    ping_timeout: int = 2
    enable_ssl_verify: bool = field(default_factory=lambda: os.getenv('SSL_VERIFY', 'true').lower() == 'true')

    # System settings
    allow_reboot: bool = False
    allow_service_control: bool = True
    allow_process_kill: bool = False
    safe_mode: bool = True

# Create global config instance
MONITORING_CONFIG = MonitoringConfig()

# Services to monitor
MONITORED_SERVICES = [
    "ssh",
    "nginx",
    "apache2",
    "mysql",
    "postgresql",
    "docker",
    "cron",
    "systemd-resolved",
    "NetworkManager",
]

# Critical system files to monitor
CRITICAL_FILES = [
    "/etc/passwd",
    "/etc/shadow",
    "/etc/sudoers",
    "/etc/ssh/sshd_config",
    "/boot/config.txt",
    "/boot/cmdline.txt",
]

# Network test endpoints
NETWORK_TEST_ENDPOINTS = {
    "dns": ["8.8.8.8", "1.1.1.1", "9.9.9.9"],
    "http": ["http://www.google.com", "http://www.cloudflare.com"],
    "ping": ["google.com", "cloudflare.com", "1.1.1.1"],
}

# External service URLs
EXTERNAL_SERVICES = {
    "public_ip": [
        "https://api.ipify.org?format=json",
        "https://ipapi.co/json/",
        "https://api.myip.com",
    ],
}

# Enhanced Agent Configuration
@dataclass
class AgentConfig:
    """Enhanced agent configuration"""
    
    api_endpoint: str = field(default_factory=lambda: os.getenv('API_ENDPOINT', 'http://localhost:8000'))
    api_key: str = field(default_factory=lambda: os.getenv('API_KEY', ''))
    device_id: str = field(default_factory=lambda: os.getenv('DEVICE_ID', socket.gethostname()))
    
    collection_interval: int = field(default_factory=lambda: int(os.getenv('COLLECTION_INTERVAL', '30')))
    agent_version: str = '2.0.0-enhanced'
    
    # GPIO monitoring
    gpio_pins: List[int] = field(default_factory=lambda: [
        int(pin) for pin in os.getenv('GPIO_PINS', '').split(',') if pin.strip().isdigit()
    ])
    
    # Custom scripts
    custom_scripts: Dict[str, str] = field(default_factory=dict)
    
    # Logging
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    
    # Network settings
    max_retries: int = field(default_factory=lambda: int(os.getenv('MAX_RETRIES', '3')))
    retry_delay: int = field(default_factory=lambda: int(os.getenv('RETRY_DELAY', '5')))
    enable_ssl_verify: bool = field(default_factory=lambda: os.getenv('SSL_VERIFY', 'true').lower() == 'true')
    
    # Configuration file
    config_file: str = field(default_factory=lambda: os.getenv('CONFIG_FILE', str(CONFIG_DIR / 'agent_config.json')))
    
    # Monitoring features
    enable_detailed_monitoring: bool = True
    enable_process_monitoring: bool = True
    enable_service_monitoring: bool = True
    enable_security_monitoring: bool = True
    enable_network_monitoring: bool = True
    enable_gpio_monitoring: bool = True
    
    # Alert settings
    alert_thresholds: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        'cpu_percent': THRESHOLDS.cpu_usage,
        'memory_percent': THRESHOLDS.memory_usage,
        'disk_percent': THRESHOLDS.disk_usage,
        'temperature_celsius': THRESHOLDS.cpu_temp,
        'swap_percent': THRESHOLDS.swap_usage
    })
    
    def __post_init__(self):
        self.load_from_file()
        self.validate()
    
    def load_from_file(self):
        """Load configuration from JSON file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                for key, value in config_data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
                
                print(f"Configuration loaded from {self.config_file}")
            
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_file}: {e}")
    
    def validate(self):
        """Validate configuration"""
        if not self.api_key:
            raise ValueError("API_KEY environment variable or config is required")
        
        if not self.api_endpoint:
            raise ValueError("API_ENDPOINT environment variable or config is required")
        
        if self.collection_interval < 10:
            print("Warning: Collection interval is very low, setting minimum to 10 seconds")
            self.collection_interval = 10
        
        if self.collection_interval > 3600:
            print("Warning: Collection interval is very high, setting maximum to 1 hour")
            self.collection_interval = 3600
    
    def save_to_file(self):
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            config_data = {
                'api_endpoint': self.api_endpoint,
                'api_key': self.api_key,
                'device_id': self.device_id,
                'collection_interval': self.collection_interval,
                'gpio_pins': self.gpio_pins,
                'custom_scripts': self.custom_scripts,
                'log_level': self.log_level,
                'max_retries': self.max_retries,
                'retry_delay': self.retry_delay,
                'enable_ssl_verify': self.enable_ssl_verify,
                'enable_detailed_monitoring': self.enable_detailed_monitoring,
                'enable_process_monitoring': self.enable_process_monitoring,
                'enable_service_monitoring': self.enable_service_monitoring,
                'enable_security_monitoring': self.enable_security_monitoring,
                'enable_network_monitoring': self.enable_network_monitoring,
                'enable_gpio_monitoring': self.enable_gpio_monitoring,
                'alert_thresholds': self.alert_thresholds
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            print(f"Configuration saved to {self.config_file}")
        
        except Exception as e:
            print(f"Error saving config file: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            'device_id': self.device_id,
            'api_endpoint': self.api_endpoint.replace(self.api_key, '*' * 8) if self.api_key in self.api_endpoint else self.api_endpoint,
            'collection_interval': self.collection_interval,
            'gpio_pins': self.gpio_pins,
            'custom_scripts': list(self.custom_scripts.keys()),
            'log_level': self.log_level,
            'agent_version': self.agent_version,
            'features': {
                'detailed_monitoring': self.enable_detailed_monitoring,
                'process_monitoring': self.enable_process_monitoring,
                'service_monitoring': self.enable_service_monitoring,
                'security_monitoring': self.enable_security_monitoring,
                'network_monitoring': self.enable_network_monitoring,
                'gpio_monitoring': self.enable_gpio_monitoring
            }
        }

# Logging Configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'json': {
            'format': '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': str(LOGS_DIR / 'agent.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': str(LOGS_DIR / 'agent_errors.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO'
        },
        'monitoring': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}