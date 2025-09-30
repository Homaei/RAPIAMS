from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Command(Base):
    __tablename__ = "commands"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    command_type = Column(String(100), nullable=False, index=True)  # process_kill, service_restart, system_reboot, custom
    command = Column(Text, nullable=False)  # Actual command to execute
    parameters = Column(JSON)  # Command parameters
    priority = Column(Integer, default=5)  # 1-10, higher = more priority
    status = Column(String(50), default="pending", index=True)  # pending, queued, executing, completed, failed, cancelled
    result = Column(Text)  # Command output/result
    exit_code = Column(Integer)  # Command exit code
    error_message = Column(Text)  # Error message if failed
    executed_by = Column(String(100))  # User who initiated command
    execution_start = Column(DateTime, nullable=True)
    execution_end = Column(DateTime, nullable=True)
    execution_duration_ms = Column(Integer)  # Duration in milliseconds
    timeout_seconds = Column(Integer, default=30)  # Command timeout
    requires_confirmation = Column(Boolean, default=False)  # Dangerous commands
    confirmed_by = Column(String(100))
    confirmed_at = Column(DateTime, nullable=True)
    metadata = Column(JSON)  # Additional metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    device = relationship("Device", back_populates="commands")
    command_logs = relationship("CommandLog", back_populates="command", cascade="all, delete-orphan")


class CommandLog(Base):
    """Track command execution stages and output"""
    __tablename__ = "command_logs"

    id = Column(Integer, primary_key=True, index=True)
    command_id = Column(Integer, ForeignKey("commands.id"), nullable=False)
    log_type = Column(String(50), nullable=False)  # stdout, stderr, status_change, error
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())

    # Relationships
    command = relationship("Command", back_populates="command_logs")


class CommandQueue(Base):
    """Queue for managing command execution"""
    __tablename__ = "command_queue"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    command_id = Column(Integer, ForeignKey("commands.id"), nullable=False)
    position = Column(Integer, nullable=False)  # Position in queue
    added_at = Column(DateTime, server_default=func.now())
    processing_started_at = Column(DateTime, nullable=True)

    # Relationships
    device = relationship("Device")
    command = relationship("Command")


class CommandTemplate(Base):
    """Pre-defined command templates for common operations"""
    __tablename__ = "command_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    category = Column(String(100), nullable=False)  # process, service, system, security, custom
    description = Column(Text)
    command_template = Column(Text, nullable=False)  # Template with placeholders
    parameters_schema = Column(JSON)  # Expected parameters and their types
    requires_confirmation = Column(Boolean, default=False)
    minimum_permission_level = Column(String(50), default="USER")  # ADMIN, POWER_USER, USER
    is_dangerous = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class CommandHistory(Base):
    """Historical record of all commands for audit purposes"""
    __tablename__ = "command_history"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    command_type = Column(String(100), nullable=False)
    command = Column(Text, nullable=False)
    parameters = Column(JSON)
    status = Column(String(50), nullable=False)
    result = Column(Text)
    exit_code = Column(Integer)
    executed_by = Column(String(100))
    execution_time = Column(DateTime, nullable=False)
    execution_duration_ms = Column(Integer)

    # Relationships
    device = relationship("Device")