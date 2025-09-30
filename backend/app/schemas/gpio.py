"""
GPIO Control Schemas
Data validation and serialization for GPIO operations
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class SafetyFeatures(BaseModel):
    """Safety features configuration for GPIO devices"""
    cooldown_time: int = Field(
        default=0,
        ge=0,
        description="Cooldown time in seconds between operations"
    )
    max_cycles_per_hour: int = Field(
        default=0,
        ge=0,
        description="Maximum number of on/off cycles per hour (0 = unlimited)"
    )


class GPIODeviceConfig(BaseModel):
    """Configuration for a GPIO device"""
    pin: int = Field(
        ...,
        ge=0,
        le=27,
        description="GPIO pin number (BCM numbering)"
    )
    mode: str = Field(
        default="OUTPUT",
        description="GPIO mode (OUTPUT or INPUT)"
    )
    active_state: str = Field(
        default="HIGH",
        description="Active state (HIGH or LOW)"
    )
    initial_state: str = Field(
        default="LOW",
        description="Initial state (HIGH or LOW)"
    )
    description: str = Field(
        default="",
        max_length=200,
        description="Device description"
    )
    max_runtime: int = Field(
        default=300,
        ge=1,
        le=3600,
        description="Maximum continuous runtime in seconds"
    )
    device_type: str = Field(
        default="generic",
        description="Device type (buzzer, relay, motor, led, etc.)"
    )
    safety_features: Optional[SafetyFeatures] = Field(
        default_factory=SafetyFeatures,
        description="Safety features configuration"
    )

    @validator('mode')
    def validate_mode(cls, v):
        if v.upper() not in ['OUTPUT', 'INPUT']:
            raise ValueError('Mode must be OUTPUT or INPUT')
        return v.upper()

    @validator('active_state', 'initial_state')
    def validate_state(cls, v):
        if v.upper() not in ['HIGH', 'LOW']:
            raise ValueError('State must be HIGH or LOW')
        return v.upper()

    @validator('device_type')
    def validate_device_type(cls, v):
        allowed_types = ['buzzer', 'relay', 'motor', 'led', 'generic', 'pump', 'valve', 'sensor']
        if v.lower() not in allowed_types:
            raise ValueError(f'Device type must be one of: {", ".join(allowed_types)}')
        return v.lower()


class GPIODeviceRegister(BaseModel):
    """Request to register a new GPIO device"""
    device_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique device name"
    )
    config: GPIODeviceConfig = Field(
        ...,
        description="Device configuration"
    )

    @validator('device_name')
    def validate_device_name(cls, v):
        # Only alphanumeric, underscore, and hyphen allowed
        if not all(c.isalnum() or c in ['_', '-'] for c in v):
            raise ValueError('Device name can only contain letters, numbers, underscores, and hyphens')
        return v


class GPIODeviceInfo(BaseModel):
    """GPIO device information"""
    name: str
    pin: int
    device_type: str
    description: str
    active_state: str
    max_runtime: int
    cooldown_time: int
    max_cycles_per_hour: int
    is_on: bool


class GPIODeviceStatus(BaseModel):
    """Current status of a GPIO device"""
    device_name: str
    is_on: bool
    pin: int
    device_type: str
    timestamp: str
    current_runtime: Optional[float] = None
    time_remaining: Optional[float] = None
    last_turned_on: Optional[str] = None
    last_turned_off: Optional[str] = None
    cooldown_remaining: Optional[float] = None


class GPIODeviceStatistics(BaseModel):
    """Usage statistics for a GPIO device"""
    device_name: str
    total_runtime: float
    total_cycles: int
    cycles_last_hour: int
    current_session_runtime: float
    is_on: bool
    timestamp: str


class GPIODevicesList(BaseModel):
    """List of registered GPIO devices"""
    success: bool
    device_count: int
    devices: List[Dict[str, Any]]
    gpio_available: bool
    timestamp: str


class GPIOTurnOnDuration(BaseModel):
    """Request to turn on device for specific duration"""
    duration: float = Field(
        ...,
        gt=0,
        le=3600,
        description="Duration in seconds"
    )


class GPIOCommandResponse(BaseModel):
    """Response from GPIO command"""
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: str
    error: Optional[str] = None


# Quick action schemas

class BuzzerBeep(BaseModel):
    """Quick buzzer beep request"""
    duration: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Beep duration in seconds"
    )


class PumpControl(BaseModel):
    """Pump control request"""
    duration: Optional[float] = Field(
        default=None,
        ge=1,
        le=300,
        description="Run duration in seconds (optional for manual control)"
    )


# Example responses for documentation

class GPIOExamples:
    """Example payloads for API documentation"""

    register_buzzer = {
        "device_name": "buzzer",
        "config": {
            "pin": 17,
            "mode": "OUTPUT",
            "active_state": "HIGH",
            "initial_state": "LOW",
            "description": "Test buzzer",
            "max_runtime": 60,
            "device_type": "buzzer",
            "safety_features": {
                "cooldown_time": 0,
                "max_cycles_per_hour": 0
            }
        }
    }

    register_pump_relay = {
        "device_name": "pump_relay",
        "config": {
            "pin": 27,
            "mode": "OUTPUT",
            "active_state": "LOW",
            "initial_state": "HIGH",
            "description": "Water pump relay (JQC3F-05VDC-C)",
            "max_runtime": 300,
            "device_type": "relay",
            "safety_features": {
                "cooldown_time": 60,
                "max_cycles_per_hour": 10
            }
        }
    }

    turn_on_duration = {
        "duration": 10.0
    }

    device_status_response = {
        "success": True,
        "data": {
            "device_name": "buzzer",
            "is_on": True,
            "pin": 17,
            "device_type": "buzzer",
            "timestamp": "2025-09-30T10:00:00",
            "current_runtime": 5.2,
            "time_remaining": 54.8,
            "last_turned_on": "2025-09-30T09:59:55"
        },
        "timestamp": "2025-09-30T10:00:00"
    }

    device_statistics_response = {
        "success": True,
        "data": {
            "device_name": "pump_relay",
            "total_runtime": 1234.5,
            "total_cycles": 45,
            "cycles_last_hour": 3,
            "current_session_runtime": 0,
            "is_on": False,
            "timestamp": "2025-09-30T10:00:00"
        },
        "timestamp": "2025-09-30T10:00:00"
    }