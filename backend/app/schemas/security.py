from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SecuritySeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SecurityEventType(str, Enum):
    FAILED_LOGIN = "failed_login"
    PORT_SCAN = "port_scan"
    INTRUSION_ATTEMPT = "intrusion_attempt"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    MALWARE_DETECTED = "malware_detected"
    SUSPICIOUS_PROCESS = "suspicious_process"
    CONFIGURATION_CHANGE = "configuration_change"
    FIREWALL_BREACH = "firewall_breach"
    OTHER = "other"


class SecurityEventBase(BaseModel):
    event_type: SecurityEventType
    severity: SecuritySeverity
    description: str
    source_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_ip: Optional[str] = None
    destination_port: Optional[int] = None
    username: Optional[str] = None
    service: Optional[str] = None
    raw_log: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SecurityEventCreate(SecurityEventBase):
    device_id: int


class SecurityEventUpdate(BaseModel):
    resolved: Optional[bool] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


class SecurityEventResponse(SecurityEventBase):
    id: int
    device_id: int
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SecurityEventList(BaseModel):
    events: List[SecurityEventResponse]
    total: int
    page: int = 1
    per_page: int = 100
    unresolved_count: int
    critical_count: int
    high_count: int


class FailedLoginBase(BaseModel):
    username: str
    source_ip: str
    source_host: Optional[str] = None
    service: Optional[str] = None
    attempt_count: int = 1


class FailedLoginCreate(FailedLoginBase):
    device_id: int


class FailedLoginResponse(FailedLoginBase):
    id: int
    device_id: int
    first_attempt: datetime
    last_attempt: datetime
    blocked: bool = False
    blocked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OpenPortBase(BaseModel):
    port: int
    protocol: str = "tcp"
    service_name: Optional[str] = None
    state: Optional[str] = "open"
    process_name: Optional[str] = None
    process_pid: Optional[int] = None
    risk_level: Optional[str] = "medium"
    is_expected: bool = False


class OpenPortCreate(OpenPortBase):
    device_id: int


class OpenPortResponse(OpenPortBase):
    id: int
    device_id: int
    first_seen: datetime
    last_seen: datetime

    class Config:
        from_attributes = True


class OpenPortList(BaseModel):
    ports: List[OpenPortResponse]
    total: int
    unexpected_count: int
    high_risk_count: int


class SecurityAssessmentBase(BaseModel):
    assessment_type: str
    score: int = Field(ge=0, le=100)
    passed_checks: int = 0
    failed_checks: int = 0
    warnings: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    findings: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None


class SecurityAssessmentCreate(SecurityAssessmentBase):
    device_id: int


class SecurityAssessmentResponse(SecurityAssessmentBase):
    id: int
    device_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SecurityScan(BaseModel):
    scan_type: str = "full"  # full, quick, custom
    check_open_ports: bool = True
    check_failed_logins: bool = True
    check_running_processes: bool = True
    check_system_logs: bool = True
    check_file_integrity: bool = False
    check_firewall_rules: bool = True
    custom_checks: Optional[List[str]] = None


class SecurityScanResponse(BaseModel):
    success: bool
    scan_id: str
    duration_ms: int
    assessment: SecurityAssessmentResponse
    events_found: int
    critical_findings: List[Dict[str, Any]]
    recommendations: List[str]


class SecurityFilter(BaseModel):
    event_type: Optional[SecurityEventType] = None
    severity: Optional[SecuritySeverity] = None
    resolved: Optional[bool] = None
    source_ip: Optional[str] = None
    username: Optional[str] = None
    service: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class SecurityStatistics(BaseModel):
    total_events: int
    events_by_type: Dict[str, int]
    events_by_severity: Dict[str, int]
    resolved_events: int
    unresolved_events: int
    failed_login_attempts: int
    unique_source_ips: int
    open_ports: int
    high_risk_ports: int
    latest_assessment_score: Optional[int] = None
    trend: str  # improving, stable, deteriorating


class SecurityMonitoringConfig(BaseModel):
    enabled: bool = True
    scan_interval_minutes: int = 60
    track_failed_logins: bool = True
    max_failed_attempts: int = 5
    auto_block_failed_logins: bool = True
    block_duration_minutes: int = 30
    port_scan_detection: bool = True
    alert_on_high_severity: bool = True
    alert_on_new_ports: bool = True
    monitored_ports: Optional[List[int]] = None
    ignored_ips: Optional[List[str]] = None