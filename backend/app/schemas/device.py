from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import UUID


class DeviceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    hostname: Optional[str] = None
    model: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    alert_thresholds: Optional[Dict[str, float]] = None
    webhook_url: Optional[str] = None
    notification_channels: List[str] = []


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    location: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    alert_thresholds: Optional[Dict[str, float]] = None
    webhook_url: Optional[str] = None
    notification_channels: Optional[List[str]] = None
    is_active: Optional[bool] = None


class DeviceRegister(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=100)
    hostname: str
    model: str
    os_version: str
    kernel_version: str
    agent_version: str
    cpu_cores: int
    ram_total_mb: int
    storage_total_gb: float
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    
    @validator('mac_address')
    def validate_mac(cls, v):
        if v:
            import re
            if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', v):
                raise ValueError('Invalid MAC address format')
        return v


class DeviceResponse(BaseModel):
    id: UUID
    device_id: str
    name: str
    hostname: Optional[str]
    model: Optional[str]
    location: Optional[str]
    description: Optional[str]
    tags: List[str]
    is_active: bool
    is_online: bool
    os_version: Optional[str]
    kernel_version: Optional[str]
    agent_version: Optional[str]
    cpu_cores: Optional[int]
    ram_total_mb: Optional[int]
    storage_total_gb: Optional[float]
    ip_address: Optional[str]
    mac_address: Optional[str]
    last_seen: Optional[datetime]
    last_boot: Optional[datetime]
    alert_thresholds: Dict[str, float]
    webhook_url: Optional[str]
    notification_channels: List[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DeviceApiKey(BaseModel):
    device_id: UUID
    api_key: str
    created_at: datetime


class AlertBase(BaseModel):
    alert_type: str
    severity: str = Field(..., pattern='^(low|medium|high|critical)$')
    message: str
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None


class AlertCreate(AlertBase):
    device_id: UUID


class AlertUpdate(BaseModel):
    is_resolved: Optional[bool] = None
    acknowledged: Optional[bool] = None


class AlertResponse(AlertBase):
    id: UUID
    device_id: UUID
    is_resolved: bool
    resolved_at: Optional[datetime]
    acknowledged: bool
    acknowledged_by: Optional[UUID]
    acknowledged_at: Optional[datetime]
    notification_sent: bool
    notification_channels: List[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True