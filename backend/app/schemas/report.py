from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ReportType(str, Enum):
    SYSTEM = "system"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    INVENTORY = "inventory"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    MARKDOWN = "markdown"


class ReportStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReportBase(BaseModel):
    report_type: ReportType
    title: str
    description: Optional[str] = None
    format: ReportFormat = ReportFormat.PDF
    parameters: Optional[Dict[str, Any]] = None
    scheduled: bool = False


class ReportCreate(ReportBase):
    device_id: int
    generated_by: Optional[str] = None


class ReportUpdate(BaseModel):
    status: Optional[ReportStatus] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    content: Optional[str] = None
    generation_time_seconds: Optional[int] = None
    error_message: Optional[str] = None
    generated_at: Optional[datetime] = None


class ReportResponse(ReportBase):
    id: int
    device_id: int
    status: ReportStatus
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    generated_by: Optional[str] = None
    generation_time_seconds: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    generated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportList(BaseModel):
    reports: List[ReportResponse]
    total: int
    page: int = 1
    per_page: int = 50


class ReportSectionBase(BaseModel):
    section_name: str
    section_order: int
    content_type: Optional[str] = "text"
    content: Dict[str, Any]


class ReportSectionResponse(ReportSectionBase):
    id: int
    report_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReportTemplateBase(BaseModel):
    name: str
    report_type: ReportType
    description: Optional[str] = None
    template_config: Dict[str, Any]
    sections: Optional[List[Dict[str, Any]]] = None
    default_parameters: Optional[Dict[str, Any]] = None
    is_active: bool = True


class ReportTemplateCreate(ReportTemplateBase):
    created_by: Optional[str] = None


class ReportTemplateResponse(ReportTemplateBase):
    id: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportScheduleBase(BaseModel):
    schedule_name: str
    template_id: int
    cron_expression: str
    enabled: bool = True
    parameters: Optional[Dict[str, Any]] = None
    recipients: Optional[List[Dict[str, str]]] = None  # [{"type": "email", "value": "user@example.com"}]


class ReportScheduleCreate(ReportScheduleBase):
    device_id: int


class ReportScheduleUpdate(BaseModel):
    schedule_name: Optional[str] = None
    cron_expression: Optional[str] = None
    enabled: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None
    recipients: Optional[List[Dict[str, str]]] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None


class ReportScheduleResponse(ReportScheduleBase):
    id: int
    device_id: int
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportGenerationRequest(BaseModel):
    report_type: ReportType
    format: ReportFormat = ReportFormat.PDF
    title: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    include_sections: Optional[List[str]] = None
    exclude_sections: Optional[List[str]] = None
    send_to: Optional[List[Dict[str, str]]] = None  # Recipients


class ReportGenerationResponse(BaseModel):
    success: bool
    report_id: int
    message: str
    estimated_time_seconds: Optional[int] = None


class ReportFilter(BaseModel):
    report_type: Optional[ReportType] = None
    format: Optional[ReportFormat] = None
    status: Optional[ReportStatus] = None
    scheduled: Optional[bool] = None
    generated_by: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class ReportStatistics(BaseModel):
    total_reports: int
    reports_by_type: Dict[str, int]
    reports_by_format: Dict[str, int]
    reports_by_status: Dict[str, int]
    scheduled_reports: int
    average_generation_time_seconds: float
    total_storage_mb: float


class ReportConfig(BaseModel):
    enabled: bool = True
    storage_path: str = "/var/reports"
    max_storage_gb: int = 10
    retention_days: int = 90
    auto_cleanup: bool = True
    allowed_formats: List[ReportFormat] = [ReportFormat.PDF, ReportFormat.HTML, ReportFormat.JSON]
    max_generation_time_seconds: int = 300
    enable_scheduling: bool = True