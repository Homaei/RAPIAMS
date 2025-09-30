from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class MetricsBase(BaseModel):
    cpu_percent: Optional[float] = Field(None, ge=0, le=100)
    cpu_temperature: Optional[float] = None
    cpu_frequency: Optional[float] = None
    
    memory_used_mb: Optional[int] = Field(None, ge=0)
    memory_available_mb: Optional[int] = Field(None, ge=0)
    memory_percent: Optional[float] = Field(None, ge=0, le=100)
    swap_used_mb: Optional[int] = Field(None, ge=0)
    swap_percent: Optional[float] = Field(None, ge=0, le=100)
    
    disk_used_gb: Optional[float] = Field(None, ge=0)
    disk_available_gb: Optional[float] = Field(None, ge=0)
    disk_percent: Optional[float] = Field(None, ge=0, le=100)
    disk_read_bytes: Optional[int] = Field(None, ge=0)
    disk_write_bytes: Optional[int] = Field(None, ge=0)
    
    network_sent_bytes: Optional[int] = Field(None, ge=0)
    network_recv_bytes: Optional[int] = Field(None, ge=0)
    network_packets_sent: Optional[int] = Field(None, ge=0)
    network_packets_recv: Optional[int] = Field(None, ge=0)
    network_error_in: Optional[int] = Field(None, ge=0)
    network_error_out: Optional[int] = Field(None, ge=0)
    
    processes_running: Optional[int] = Field(None, ge=0)
    processes_sleeping: Optional[int] = Field(None, ge=0)
    processes_total: Optional[int] = Field(None, ge=0)
    
    uptime_seconds: Optional[int] = Field(None, ge=0)
    load_avg_1: Optional[float] = Field(None, ge=0)
    load_avg_5: Optional[float] = Field(None, ge=0)
    load_avg_15: Optional[float] = Field(None, ge=0)
    
    gpio_states: Optional[Dict[str, Any]] = None
    custom_metrics: Optional[Dict[str, Any]] = None


class MetricsCreate(MetricsBase):
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MetricsResponse(MetricsBase):
    id: UUID
    device_id: UUID
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class MetricsQuery(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    interval: Optional[str] = Field(None, pattern='^(1m|5m|15m|30m|1h|6h|12h|1d|1w)$')
    metrics: Optional[list[str]] = None


class MetricsAggregateResponse(BaseModel):
    device_id: UUID
    interval_type: str
    timestamp: datetime
    
    cpu_percent_avg: Optional[float]
    cpu_percent_max: Optional[float]
    cpu_percent_min: Optional[float]
    
    memory_percent_avg: Optional[float]
    memory_percent_max: Optional[float]
    memory_percent_min: Optional[float]
    
    disk_percent_avg: Optional[float]
    disk_percent_max: Optional[float]
    disk_percent_min: Optional[float]
    
    temperature_avg: Optional[float]
    temperature_max: Optional[float]
    temperature_min: Optional[float]
    
    network_sent_total: Optional[int]
    network_recv_total: Optional[int]
    
    uptime_percent: Optional[float]
    data_points: int
    
    class Config:
        from_attributes = True


class SystemStatus(BaseModel):
    device_id: UUID
    device_name: str
    is_online: bool
    last_seen: Optional[datetime]
    current_metrics: Optional[MetricsBase]
    alerts_count: int
    uptime_percent_24h: float
    

class MetricsSummary(BaseModel):
    total_devices: int
    online_devices: int
    offline_devices: int
    total_alerts: int
    critical_alerts: int
    avg_cpu_usage: float
    avg_memory_usage: float
    avg_disk_usage: float