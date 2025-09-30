from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255))
    description = Column(String(500))
    status = Column(String(50), default="unknown")  # running, stopped, unknown
    enabled = Column(Boolean, default=True)  # Whether service is enabled on boot
    active = Column(Boolean, default=False)  # Whether service is currently active
    pid = Column(Integer, nullable=True)
    memory_usage_mb = Column(Integer, default=0)
    cpu_usage = Column(Integer, default=0)
    start_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    device = relationship("Device", back_populates="services")
    service_logs = relationship("ServiceLog", back_populates="service", cascade="all, delete-orphan")


class ServiceLog(Base):
    """Track service state changes and events"""
    __tablename__ = "service_logs"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    action = Column(String(50), nullable=False)  # start, stop, restart, status_change
    previous_status = Column(String(50))
    new_status = Column(String(50))
    initiated_by = Column(String(100))  # user, system, auto
    result = Column(String(50))  # success, failure
    error_message = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    service = relationship("Service", back_populates="service_logs")
    device = relationship("Device", back_populates="service_logs")


class ServiceDependency(Base):
    """Track service dependencies"""
    __tablename__ = "service_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    service_name = Column(String(255), nullable=False)
    depends_on = Column(String(255), nullable=False)
    dependency_type = Column(String(50))  # required, optional
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    device = relationship("Device", back_populates="service_dependencies")