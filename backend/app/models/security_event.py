from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    event_type = Column(String(100), nullable=False, index=True)  # failed_login, port_scan, intrusion_attempt, etc.
    severity = Column(String(20), nullable=False, index=True)  # critical, high, medium, low, info
    source_ip = Column(String(45))  # IPv4 or IPv6
    source_port = Column(Integer)
    destination_ip = Column(String(45))
    destination_port = Column(Integer)
    username = Column(String(100))
    service = Column(String(100))
    description = Column(Text, nullable=False)
    raw_log = Column(Text)  # Original log entry
    resolved = Column(Boolean, default=False)
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text)
    metadata = Column(JSON)  # Additional structured data
    created_at = Column(DateTime, server_default=func.now(), index=True)

    # Relationships
    device = relationship("Device", back_populates="security_events")


class FailedLogin(Base):
    """Track failed login attempts"""
    __tablename__ = "failed_logins"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    username = Column(String(100), nullable=False, index=True)
    source_ip = Column(String(45), nullable=False, index=True)
    source_host = Column(String(255))
    service = Column(String(100))  # ssh, ftp, web, etc.
    attempt_count = Column(Integer, default=1)
    first_attempt = Column(DateTime, server_default=func.now())
    last_attempt = Column(DateTime, server_default=func.now())
    blocked = Column(Boolean, default=False)
    blocked_at = Column(DateTime, nullable=True)

    # Relationships
    device = relationship("Device", back_populates="failed_logins")


class OpenPort(Base):
    """Track open ports on devices"""
    __tablename__ = "open_ports"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    port = Column(Integer, nullable=False, index=True)
    protocol = Column(String(10), nullable=False)  # tcp, udp
    service_name = Column(String(100))
    state = Column(String(20))  # open, filtered, closed
    process_name = Column(String(255))
    process_pid = Column(Integer)
    risk_level = Column(String(20))  # critical, high, medium, low
    first_seen = Column(DateTime, server_default=func.now())
    last_seen = Column(DateTime, server_default=func.now())
    is_expected = Column(Boolean, default=False)  # Whether this port should be open

    # Relationships
    device = relationship("Device", back_populates="open_ports")


class SecurityAssessment(Base):
    """Store security assessment results"""
    __tablename__ = "security_assessments"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    assessment_type = Column(String(100), nullable=False)  # vulnerability_scan, compliance_check, etc.
    score = Column(Integer, default=0)  # Security score 0-100
    passed_checks = Column(Integer, default=0)
    failed_checks = Column(Integer, default=0)
    warnings = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)
    findings = Column(JSON)  # Detailed findings
    recommendations = Column(JSON)  # Security recommendations
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    device = relationship("Device", back_populates="security_assessments")