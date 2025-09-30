from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    report_type = Column(String(100), nullable=False, index=True)  # system, security, performance, custom
    title = Column(String(255), nullable=False)
    description = Column(Text)
    format = Column(String(20), nullable=False)  # pdf, html, json, csv, excel
    status = Column(String(50), default="pending")  # pending, generating, completed, failed
    file_path = Column(String(500))  # Path to generated report file
    file_size = Column(Integer)  # File size in bytes
    content = Column(Text)  # For small reports, store content directly
    parameters = Column(JSON)  # Report generation parameters
    metadata = Column(JSON)  # Additional metadata
    generated_by = Column(String(100))  # User or system that triggered report
    generation_time_seconds = Column(Integer)  # Time taken to generate
    error_message = Column(Text)  # If generation failed
    scheduled = Column(Boolean, default=False)  # Whether this was a scheduled report
    created_at = Column(DateTime, server_default=func.now())
    generated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Auto-delete old reports

    # Relationships
    device = relationship("Device", back_populates="reports")
    report_sections = relationship("ReportSection", back_populates="report", cascade="all, delete-orphan")


class ReportSection(Base):
    """Sections within a report for better organization"""
    __tablename__ = "report_sections"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    section_name = Column(String(255), nullable=False)
    section_order = Column(Integer, nullable=False)
    content_type = Column(String(50))  # text, table, chart, metrics
    content = Column(JSON)  # Section content data
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    report = relationship("Report", back_populates="report_sections")


class ReportTemplate(Base):
    """Templates for generating reports"""
    __tablename__ = "report_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    report_type = Column(String(100), nullable=False)
    description = Column(Text)
    template_config = Column(JSON, nullable=False)  # Template configuration
    sections = Column(JSON)  # Sections to include
    default_parameters = Column(JSON)  # Default parameters
    is_active = Column(Boolean, default=True)
    created_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ReportSchedule(Base):
    """Schedule for automatic report generation"""
    __tablename__ = "report_schedules"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("report_templates.id"), nullable=False)
    schedule_name = Column(String(255), nullable=False)
    cron_expression = Column(String(100))  # Cron format for scheduling
    enabled = Column(Boolean, default=True)
    parameters = Column(JSON)  # Report generation parameters
    recipients = Column(JSON)  # Email addresses or webhook URLs
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    device = relationship("Device", back_populates="report_schedules")
    template = relationship("ReportTemplate")