from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertMetricType(str, Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    PROCESS = "process"
    SERVICE = "service"
    SECURITY = "security"
    CUSTOM = "custom"


class AlertConditionType(str, Enum):
    THRESHOLD = "threshold"
    RATE_CHANGE = "rate_change"
    ANOMALY = "anomaly"
    PATTERN = "pattern"
    ABSENCE = "absence"


class AlertOperator(str, Enum):
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    EXPIRED = "expired"


class AlertRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    metric_type: AlertMetricType
    condition_type: AlertConditionType
    operator: Optional[AlertOperator] = None
    threshold_value: Optional[float] = None
    threshold_unit: Optional[str] = None
    time_window_seconds: int = 60
    consecutive_checks: int = 1
    severity: AlertSeverity
    enabled: bool = True
    cooldown_period_seconds: int = 300
    escalation_rules: Optional[List[Dict[str, Any]]] = None
    notification_channels: Optional[List[Dict[str, str]]] = None
    custom_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AlertRuleCreate(AlertRuleBase):
    device_id: Optional[int] = None  # None for global rules
    created_by: Optional[str] = None


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    operator: Optional[AlertOperator] = None
    threshold_value: Optional[float] = None
    threshold_unit: Optional[str] = None
    time_window_seconds: Optional[int] = None
    consecutive_checks: Optional[int] = None
    severity: Optional[AlertSeverity] = None
    enabled: Optional[bool] = None
    cooldown_period_seconds: Optional[int] = None
    escalation_rules: Optional[List[Dict[str, Any]]] = None
    notification_channels: Optional[List[Dict[str, str]]] = None
    custom_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AlertRuleResponse(AlertRuleBase):
    id: int
    device_id: Optional[int] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertRuleList(BaseModel):
    rules: List[AlertRuleResponse]
    total: int
    page: int = 1
    per_page: int = 100
    enabled_count: int
    disabled_count: int


class AlertHistoryBase(BaseModel):
    alert_rule_id: int
    device_id: int
    severity: AlertSeverity
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    alert_message: str
    metadata: Optional[Dict[str, Any]] = None


class AlertHistoryResponse(AlertHistoryBase):
    id: int
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    status: AlertStatus
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    notifications_sent: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True


class AlertHistoryList(BaseModel):
    alerts: List[AlertHistoryResponse]
    total: int
    page: int = 1
    per_page: int = 100
    active_count: int
    acknowledged_count: int
    resolved_count: int


class AlertSuppressionBase(BaseModel):
    reason: str
    start_time: datetime
    end_time: datetime


class AlertSuppressionCreate(AlertSuppressionBase):
    alert_rule_id: Optional[int] = None
    device_id: Optional[int] = None
    created_by: str


class AlertSuppressionResponse(AlertSuppressionBase):
    id: int
    alert_rule_id: Optional[int] = None
    device_id: Optional[int] = None
    created_by: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AlertTemplateBase(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    metric_type: AlertMetricType
    default_condition_type: AlertConditionType
    default_operator: Optional[AlertOperator] = None
    default_threshold_value: Optional[float] = None
    default_threshold_unit: Optional[str] = None
    default_severity: AlertSeverity
    default_cooldown_seconds: int = 300
    template_config: Dict[str, Any]
    is_active: bool = True


class AlertTemplateResponse(AlertTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertEscalationBase(BaseModel):
    level: int
    after_minutes: int
    notification_channels: List[Dict[str, str]]
    additional_recipients: Optional[List[Dict[str, str]]] = None


class AlertEscalationResponse(AlertEscalationBase):
    id: int
    alert_rule_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AlertAcknowledge(BaseModel):
    acknowledged_by: str
    notes: Optional[str] = None


class AlertResolve(BaseModel):
    resolution_notes: str
    resolved_by: Optional[str] = None


class AlertFilter(BaseModel):
    device_id: Optional[int] = None
    metric_type: Optional[AlertMetricType] = None
    severity: Optional[AlertSeverity] = None
    status: Optional[AlertStatus] = None
    rule_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class AlertStatistics(BaseModel):
    total_rules: int
    enabled_rules: int
    total_alerts: int
    active_alerts: int
    alerts_by_severity: Dict[str, int]
    alerts_by_metric_type: Dict[str, int]
    alerts_by_status: Dict[str, int]
    average_resolution_time_minutes: Optional[float] = None
    most_triggered_rules: List[Dict[str, Any]]


class AlertTestRequest(BaseModel):
    rule_id: int
    test_value: float
    simulate_trigger: bool = True


class AlertTestResponse(BaseModel):
    would_trigger: bool
    severity: AlertSeverity
    message: str
    threshold_value: float
    test_value: float
    notifications_would_send: List[Dict[str, str]]