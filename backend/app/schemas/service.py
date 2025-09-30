from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ServiceStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ServiceAction(str, Enum):
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    RELOAD = "reload"
    ENABLE = "enable"
    DISABLE = "disable"
    STATUS = "status"


class ServiceBase(BaseModel):
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    status: ServiceStatus = ServiceStatus.UNKNOWN
    enabled: bool = True
    active: bool = False
    pid: Optional[int] = None
    memory_usage_mb: int = 0
    cpu_usage: int = 0
    start_time: Optional[datetime] = None


class ServiceCreate(ServiceBase):
    device_id: int


class ServiceUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ServiceStatus] = None
    enabled: Optional[bool] = None
    active: Optional[bool] = None
    pid: Optional[int] = None
    memory_usage_mb: Optional[int] = None
    cpu_usage: Optional[int] = None
    start_time: Optional[datetime] = None


class ServiceResponse(ServiceBase):
    id: int
    device_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ServiceList(BaseModel):
    services: List[ServiceResponse]
    total: int
    page: int = 1
    per_page: int = 100


class ServiceControl(BaseModel):
    service_name: str
    action: ServiceAction
    force: bool = False
    wait_timeout: int = 30  # Seconds to wait for action to complete


class ServiceControlResponse(BaseModel):
    success: bool
    message: str
    service_name: str
    action: ServiceAction
    new_status: ServiceStatus
    execution_time_ms: Optional[int] = None


class ServiceLogBase(BaseModel):
    action: str
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    initiated_by: Optional[str] = None
    result: Optional[str] = None
    error_message: Optional[str] = None


class ServiceLogResponse(ServiceLogBase):
    id: int
    service_id: int
    device_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ServiceDependencyBase(BaseModel):
    service_name: str
    depends_on: str
    dependency_type: Optional[str] = "required"


class ServiceDependencyResponse(ServiceDependencyBase):
    id: int
    device_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ServiceFilter(BaseModel):
    name: Optional[str] = None
    status: Optional[ServiceStatus] = None
    enabled: Optional[bool] = None
    active: Optional[bool] = None


class ServiceStatistics(BaseModel):
    total_services: int
    running_services: int
    stopped_services: int
    failed_services: int
    enabled_services: int
    disabled_services: int
    services_by_status: Dict[str, int]


class ServiceBulkControl(BaseModel):
    service_names: List[str]
    action: ServiceAction
    force: bool = False
    parallel: bool = False  # Execute actions in parallel


class ServiceBulkControlResponse(BaseModel):
    success: bool
    total_services: int
    successful_actions: int
    failed_actions: int
    results: List[ServiceControlResponse]


class ServiceMonitoringConfig(BaseModel):
    enabled: bool = True
    interval_seconds: int = 60
    track_logs: bool = True
    log_retention_days: int = 30
    alert_on_failure: bool = True
    alert_on_restart: bool = True
    auto_restart_failed: bool = False
    max_restart_attempts: int = 3
    restart_delay_seconds: int = 60
    monitored_services: Optional[List[str]] = None  # Specific services to monitor