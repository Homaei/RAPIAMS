from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    hostname = Column(String(255))
    model = Column(String(100))

    api_key_hash = Column(String(255), nullable=False)

    ip_address = Column(String(45))
    mac_address = Column(String(17))
    location = Column(String(255))
    description = Column(Text)
    tags = Column(JSONB, default=[])

    is_active = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)

    os_version = Column(String(255))
    kernel_version = Column(String(255))
    agent_version = Column(String(50))

    cpu_cores = Column(Integer)
    ram_total_mb = Column(Integer)
    storage_total_gb = Column(Float)

    last_seen = Column(DateTime, nullable=True)
    last_boot = Column(DateTime, nullable=True)

    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    owner = relationship("User", backref="devices")

    alert_thresholds = Column(JSONB, default={
        "cpu_percent": 80,
        "memory_percent": 85,
        "disk_percent": 90,
        "temperature_celsius": 75,
        "offline_minutes": 10
    })

    webhook_url = Column(String(500), nullable=True)
    notification_channels = Column(JSONB, default=[])

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    metrics = relationship("Metrics")
    alerts = relationship("Alert")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)

    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)

    message = Column(Text, nullable=False)
    metric_value = Column(Float)
    threshold_value = Column(Float)

    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)

    notification_sent = Column(Boolean, default=False)
    notification_channels = Column(JSONB, default=[])

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    device = relationship("Device")