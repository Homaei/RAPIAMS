from sqlalchemy import Column, Float, DateTime, Integer, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Metrics(Base):
    __tablename__ = "metrics"
    __table_args__ = (
        Index('idx_metrics_device_timestamp', 'device_id', 'timestamp'),
        Index('idx_metrics_timestamp', 'timestamp'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    
    timestamp = Column(DateTime, nullable=False, index=True)
    
    cpu_percent = Column(Float)
    cpu_temperature = Column(Float)
    cpu_frequency = Column(Float)
    
    memory_used_mb = Column(Integer)
    memory_available_mb = Column(Integer)
    memory_percent = Column(Float)
    swap_used_mb = Column(Integer)
    swap_percent = Column(Float)
    
    disk_used_gb = Column(Float)
    disk_available_gb = Column(Float)
    disk_percent = Column(Float)
    disk_read_bytes = Column(Integer)
    disk_write_bytes = Column(Integer)
    
    network_sent_bytes = Column(Integer)
    network_recv_bytes = Column(Integer)
    network_packets_sent = Column(Integer)
    network_packets_recv = Column(Integer)
    network_error_in = Column(Integer)
    network_error_out = Column(Integer)
    
    processes_running = Column(Integer)
    processes_sleeping = Column(Integer)
    processes_total = Column(Integer)
    
    uptime_seconds = Column(Integer)
    load_avg_1 = Column(Float)
    load_avg_5 = Column(Float)
    load_avg_15 = Column(Float)
    
    gpio_states = Column(JSONB, default={})
    custom_metrics = Column(JSONB, default={})
    
    created_at = Column(DateTime, server_default=func.now())
    
    device = relationship("Device")


class MetricsAggregate(Base):
    __tablename__ = "metrics_aggregate"
    __table_args__ = (
        Index('idx_metrics_agg_device_interval', 'device_id', 'interval_type', 'timestamp'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    
    interval_type = Column(String(20), nullable=False)  # hour, day, week, month
    timestamp = Column(DateTime, nullable=False)
    
    cpu_percent_avg = Column(Float)
    cpu_percent_max = Column(Float)
    cpu_percent_min = Column(Float)
    
    memory_percent_avg = Column(Float)
    memory_percent_max = Column(Float)
    memory_percent_min = Column(Float)
    
    disk_percent_avg = Column(Float)
    disk_percent_max = Column(Float)
    disk_percent_min = Column(Float)
    
    temperature_avg = Column(Float)
    temperature_max = Column(Float)
    temperature_min = Column(Float)
    
    network_sent_total = Column(Integer)
    network_recv_total = Column(Integer)
    
    uptime_percent = Column(Float)
    
    data_points = Column(Integer)  # Number of metrics aggregated
    
    created_at = Column(DateTime, server_default=func.now())