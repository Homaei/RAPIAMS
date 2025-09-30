from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class CommandType(str, Enum):
    PROCESS_KILL = "process_kill"
    SERVICE_RESTART = "service_restart"
    SERVICE_START = "service_start"
    SERVICE_STOP = "service_stop"
    SYSTEM_REBOOT = "system_reboot"
    SYSTEM_SHUTDOWN = "system_shutdown"
    FILE_OPERATION = "file_operation"
    NETWORK_CONFIG = "network_config"
    SECURITY_ACTION = "security_action"
    CUSTOM = "custom"


class CommandStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class CommandPriority(int, Enum):
    LOWEST = 1
    LOW = 3
    NORMAL = 5
    HIGH = 7
    CRITICAL = 10


class CommandBase(BaseModel):
    command_type: CommandType
    command: str
    parameters: Optional[Dict[str, Any]] = None
    priority: CommandPriority = CommandPriority.NORMAL
    timeout_seconds: int = 30
    requires_confirmation: bool = False


class CommandCreate(CommandBase):
    device_id: int
    executed_by: Optional[str] = None


class CommandUpdate(BaseModel):
    status: Optional[CommandStatus] = None
    result: Optional[str] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None
    execution_start: Optional[datetime] = None
    execution_end: Optional[datetime] = None
    execution_duration_ms: Optional[int] = None


class CommandConfirm(BaseModel):
    confirmed: bool
    confirmed_by: str
    confirmation_note: Optional[str] = None


class CommandResponse(CommandBase):
    id: int
    device_id: int
    status: CommandStatus
    result: Optional[str] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None
    executed_by: Optional[str] = None
    execution_start: Optional[datetime] = None
    execution_end: Optional[datetime] = None
    execution_duration_ms: Optional[int] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommandList(BaseModel):
    commands: List[CommandResponse]
    total: int
    page: int = 1
    per_page: int = 100
    pending_count: int
    executing_count: int
    failed_count: int


class CommandLogBase(BaseModel):
    log_type: str
    message: str


class CommandLogResponse(CommandLogBase):
    id: int
    command_id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class CommandExecuteRequest(BaseModel):
    command_type: CommandType
    command: str
    parameters: Optional[Dict[str, Any]] = None
    priority: CommandPriority = CommandPriority.NORMAL
    timeout_seconds: int = Field(default=30, le=600)  # Max 10 minutes
    wait_for_completion: bool = False
    requires_confirmation: bool = False


class CommandExecuteResponse(BaseModel):
    success: bool
    command_id: int
    status: CommandStatus
    message: str
    result: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time_ms: Optional[int] = None


class CommandQueueBase(BaseModel):
    position: int


class CommandQueueResponse(CommandQueueBase):
    id: int
    device_id: int
    command_id: int
    command: CommandResponse
    added_at: datetime
    processing_started_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CommandTemplateBase(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    command_template: str
    parameters_schema: Optional[Dict[str, Any]] = None
    requires_confirmation: bool = False
    minimum_permission_level: str = "USER"
    is_dangerous: bool = False
    is_active: bool = True


class CommandTemplateResponse(CommandTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommandBulkExecute(BaseModel):
    commands: List[CommandExecuteRequest]
    device_ids: List[int]
    parallel: bool = False
    stop_on_error: bool = True


class CommandBulkResponse(BaseModel):
    success: bool
    total_commands: int
    successful: int
    failed: int
    results: List[CommandExecuteResponse]


class CommandFilter(BaseModel):
    command_type: Optional[CommandType] = None
    status: Optional[CommandStatus] = None
    priority: Optional[CommandPriority] = None
    executed_by: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class CommandStatistics(BaseModel):
    total_commands: int
    commands_by_type: Dict[str, int]
    commands_by_status: Dict[str, int]
    average_execution_time_ms: float
    success_rate: float
    pending_commands: int
    executing_commands: int
    queue_length: int


class CommandPermission(BaseModel):
    command_type: CommandType
    allowed_roles: List[str]
    requires_confirmation: bool
    allowed_parameters: Optional[Dict[str, Any]] = None
    denied_parameters: Optional[Dict[str, Any]] = None


class CommandValidation(BaseModel):
    is_valid: bool
    is_dangerous: bool
    requires_confirmation: bool
    permission_level_required: str
    validation_errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None