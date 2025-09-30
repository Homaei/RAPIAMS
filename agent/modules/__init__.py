"""
RAPIAMS Agent Monitoring Modules Package

This package contains comprehensive monitoring modules for Raspberry Pi systems.
All modules from the original Telegram bot have been migrated and enhanced.

Author: RAPIAMS Development Team
Description: Complete system monitoring solution for Raspberry Pi devices
License: For educational and personal use
"""

from .system_monitor import SystemMonitor
from .cpu_monitor import CPUMonitor
from .memory_monitor import MemoryMonitor
from .disk_monitor import DiskMonitor
from .network_monitor import NetworkMonitor
from .temperature_monitor import TemperatureMonitor
from .user_manager import UserManager
from .gpio_controller import GPIOController

# Import existing modules if they exist (for backward compatibility)
try:
    from .process_monitor import ProcessMonitor
except ImportError:
    ProcessMonitor = None

try:
    from .service_monitor import ServiceMonitor
except ImportError:
    ServiceMonitor = None

try:
    from .security_monitor import SecurityMonitor
except ImportError:
    SecurityMonitor = None

try:
    from .alert_manager import AlertManager
except ImportError:
    AlertManager = None

try:
    from .report_manager import ReportManager
except ImportError:
    ReportManager = None

__all__ = [
    # New comprehensive monitoring modules
    'SystemMonitor',
    'CPUMonitor',
    'MemoryMonitor',
    'DiskMonitor',
    'NetworkMonitor',
    'TemperatureMonitor',
    'UserManager',
    'GPIOController',

    # Legacy modules (if available)
    'ProcessMonitor',
    'ServiceMonitor',
    'SecurityMonitor',
    'AlertManager',
    'ReportManager'
]

# Available modules with their status
AVAILABLE_MODULES = {
    'SystemMonitor': True,
    'CPUMonitor': True,
    'MemoryMonitor': True,
    'DiskMonitor': True,
    'NetworkMonitor': True,
    'TemperatureMonitor': True,
    'UserManager': True,
    'GPIOController': True,
    'ProcessMonitor': ProcessMonitor is not None,
    'ServiceMonitor': ServiceMonitor is not None,
    'SecurityMonitor': SecurityMonitor is not None,
    'AlertManager': AlertManager is not None,
    'ReportManager': ReportManager is not None
}

# Module categories
MODULE_CATEGORIES = {
    'system': ['SystemMonitor', 'CPUMonitor', 'MemoryMonitor', 'DiskMonitor'],
    'network': ['NetworkMonitor'],
    'thermal': ['TemperatureMonitor'],
    'user_management': ['UserManager'],
    'gpio_control': ['GPIOController'],
    'process_management': ['ProcessMonitor'],
    'service_management': ['ServiceMonitor'],
    'security': ['SecurityMonitor'],
    'alerting': ['AlertManager'],
    'reporting': ['ReportManager']
}

__version__ = "2.0.0"
__author__ = "RAPIAMS Development Team"

def get_available_modules():
    """Get list of available monitoring modules"""
    return {name: status for name, status in AVAILABLE_MODULES.items() if status}

def get_module_by_name(module_name: str):
    """Get module class by name"""
    if module_name not in AVAILABLE_MODULES or not AVAILABLE_MODULES[module_name]:
        raise ImportError(f"Module '{module_name}' is not available")

    return globals().get(module_name)

def initialize_all_monitors():
    """Initialize all available monitoring modules"""
    monitors = {}

    for module_name, available in AVAILABLE_MODULES.items():
        if available:
            try:
                module_class = get_module_by_name(module_name)
                if module_class:
                    monitors[module_name] = module_class()
            except Exception as e:
                print(f"Warning: Failed to initialize {module_name}: {e}")

    return monitors

def get_modules_by_category(category: str):
    """Get modules by category"""
    if category not in MODULE_CATEGORIES:
        raise ValueError(f"Unknown category '{category}'. Available: {list(MODULE_CATEGORIES.keys())}")

    modules = {}
    for module_name in MODULE_CATEGORIES[category]:
        if AVAILABLE_MODULES.get(module_name, False):
            try:
                module_class = get_module_by_name(module_name)
                if module_class:
                    modules[module_name] = module_class()
            except Exception as e:
                print(f"Warning: Failed to initialize {module_name}: {e}")

    return modules