from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)  # Null for global rules
    name = Column(String(255), nullable=False)
    description = Column(Text)
    metric_type = Column(String(100), nullable=False, index=True)  # cpu, memory, disk, network, process, service, security
    condition_type = Column(String(50), nullable=False)  # threshold, rate_change, anomaly, pattern
    operator = Column(String(20))  # >, <, >=, <=, ==, !=
    threshold_value = Column(Float)
    threshold_unit = Column(String(50))  # percent, MB, GB, count, etc.
    time_window_seconds = Column(Integer, default=60)  # Time window for evaluation
    consecutive_checks = Column(Integer, default=1)  # How many consecutive violations before alert
    severity = Column(String(20), nullable=False)  # critical, high, medium, low, info
    enabled = Column(Boolean, default=True)
    cooldown_period_seconds = Column(Integer, default=300)  # Prevent alert spam
    escalation_rules = Column(JSON)  # Rules for escalating alerts
    notification_channels = Column(JSON)  # Where to send alerts (email, webhook, etc.)
    custom_message = Column(Text)  # Custom alert message template
    metadata = Column(JSON)  # Additional configuration
    created_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    device = relationship("Device", back_populates="alert_rules")
    alert_history = relationship("AlertHistory", back_populates="alert_rule", cascade="all, delete-orphan")
    alert_suppressions = relationship("AlertSuppression", back_populates="alert_rule", cascade="all, delete-orphan")


class AlertHistory(Base):
    """Track when alerts were triggered"""
    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, index=True)
    alert_rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    triggered_at = Column(DateTime, server_default=func.now(), index=True)
    resolved_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="active")  # active, acknowledged, resolved, suppressed
    severity = Column(String(20), nullable=False)
    metric_value = Column(Float)  # The actual value that triggered the alert
    threshold_value = Column(Float)  # The threshold that was exceeded
    alert_message = Column(Text)
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text)
    notifications_sent = Column(JSON)  # Track where notifications were sent
    metadata = Column(JSON)  # Additional context data

    # Relationships
    alert_rule = relationship("AlertRule", back_populates="alert_history")
    device = relationship("Device", back_populates="alert_history")


class AlertSuppression(Base):
    """Temporarily suppress alerts"""
    __tablename__ = "alert_suppressions"

    id = Column(Integer, primary_key=True, index=True)
    alert_rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=True)  # Null for device-wide suppression
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)  # Null for rule-wide suppression
    reason = Column(Text, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    created_by = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    alert_rule = relationship("AlertRule", back_populates="alert_suppressions")
    device = relationship("Device", back_populates="alert_suppressions")


class AlertTemplate(Base):
    """Pre-defined alert rule templates"""
    __tablename__ = "alert_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    category = Column(String(100), nullable=False)  # system, performance, security, custom
    description = Column(Text)
    metric_type = Column(String(100), nullable=False)
    default_condition_type = Column(String(50), nullable=False)
    default_operator = Column(String(20))
    default_threshold_value = Column(Float)
    default_threshold_unit = Column(String(50))
    default_severity = Column(String(20), nullable=False)
    default_cooldown_seconds = Column(Integer, default=300)
    template_config = Column(JSON)  # Full template configuration
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AlertEscalation(Base):
    """Define escalation paths for alerts"""
    __tablename__ = "alert_escalations"

    id = Column(Integer, primary_key=True, index=True)
    alert_rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=False)
    level = Column(Integer, nullable=False)  # Escalation level (1, 2, 3, etc.)
    after_minutes = Column(Integer, nullable=False)  # Escalate after X minutes
    notification_channels = Column(JSON, nullable=False)  # Where to send escalated alerts
    additional_recipients = Column(JSON)  # Additional email/contact list
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    alert_rule = relationship("AlertRule")