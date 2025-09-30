import os
import json
import socket
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    api_endpoint: str = field(default_factory=lambda: os.getenv('API_ENDPOINT', 'http://localhost:8000'))
    api_key: str = field(default_factory=lambda: os.getenv('API_KEY', ''))
    device_id: str = field(default_factory=lambda: os.getenv('DEVICE_ID', socket.gethostname()))
    
    collection_interval: int = field(default_factory=lambda: int(os.getenv('COLLECTION_INTERVAL', '30')))
    agent_version: str = '1.0.0'
    
    gpio_pins: List[int] = field(default_factory=lambda: [
        int(pin) for pin in os.getenv('GPIO_PINS', '').split(',') if pin.strip().isdigit()
    ])
    
    custom_scripts: Dict[str, str] = field(default_factory=dict)
    
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    
    max_retries: int = field(default_factory=lambda: int(os.getenv('MAX_RETRIES', '3')))
    retry_delay: int = field(default_factory=lambda: int(os.getenv('RETRY_DELAY', '5')))
    
    enable_ssl_verify: bool = field(default_factory=lambda: os.getenv('SSL_VERIFY', 'true').lower() == 'true')
    
    config_file: str = field(default_factory=lambda: os.getenv('CONFIG_FILE', '/etc/rpi-monitor/config.json'))
    
    def __post_init__(self):
        self.load_from_file()
        self.validate()
    
    def load_from_file(self):
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
                'enable_ssl_verify': self.enable_ssl_verify
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            print(f"Configuration saved to {self.config_file}")
        
        except Exception as e:
            print(f"Error saving config file: {e}")
    
    def add_custom_script(self, name: str, path: str):
        if os.path.exists(path) and os.access(path, os.X_OK):
            self.custom_scripts[name] = path
            print(f"Added custom script: {name} -> {path}")
        else:
            print(f"Error: Script {path} does not exist or is not executable")
    
    def remove_custom_script(self, name: str):
        if name in self.custom_scripts:
            del self.custom_scripts[name]
            print(f"Removed custom script: {name}")
        else:
            print(f"Script {name} not found")
    
    def update_gpio_pins(self, pins: List[int]):
        valid_pins = [pin for pin in pins if 0 <= pin <= 27]  # Valid GPIO pins for Raspberry Pi
        self.gpio_pins = valid_pins
        print(f"Updated GPIO pins: {valid_pins}")
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            'device_id': self.device_id,
            'api_endpoint': self.api_endpoint.replace(self.api_key, '*' * 8) if self.api_key in self.api_endpoint else self.api_endpoint,
            'collection_interval': self.collection_interval,
            'gpio_pins': self.gpio_pins,
            'custom_scripts': list(self.custom_scripts.keys()),
            'log_level': self.log_level,
            'agent_version': self.agent_version
        }