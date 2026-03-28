"""Pydantic models for all SigmaShake API request and response types."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Tier(str, Enum):
    free = "free"
    pro = "pro"
    enterprise = "enterprise"


class MemberRole(str, Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class SubscriptionStatus(str, Enum):
    active = "active"
    trialing = "trialing"
    past_due = "past_due"
    canceled = "canceled"
    suspended = "suspended"


class DataClassification(str, Enum):
    public = "public"
    internal = "internal"
    confidential = "confidential"
    restricted = "restricted"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class TokenRequest(BaseModel):
    agent_id: str
    scopes: List[str] = Field(default_factory=list)


class TokenResponse(BaseModel):
    token: str
    expires_at: datetime
    scopes: List[str] = Field(default_factory=list)


class IssueIdentityRequest(BaseModel):
    agent_id: str
    capabilities: List[str] = Field(default_factory=list)
    ttl_secs: int = 3600


class AgentIdentityClaims(BaseModel):
    agent_id: str
    capabilities: List[str] = Field(default_factory=list)
    issued_at: datetime
    expires_at: datetime


class IdentityTokenResponse(BaseModel):
    token: str
    claims: AgentIdentityClaims


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

class CreateAccountBody(BaseModel):
    name: str
    tier: Tier = Tier.free


class Account(BaseModel):
    id: str
    name: str
    tier: Tier
    created_at: datetime


class Subscription(BaseModel):
    id: str
    account_id: str
    tier: Tier
    status: SubscriptionStatus
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None


class UpdateSubscriptionBody(BaseModel):
    tier: Optional[Tier] = None
    status: Optional[SubscriptionStatus] = None


class Seat(BaseModel):
    id: str
    account_id: str
    user_email: str
    role: MemberRole
    created_at: datetime


class AddSeatBody(BaseModel):
    user_email: str
    role: MemberRole = MemberRole.member


class TenantUsage(BaseModel):
    account_id: str
    period_start: datetime
    period_end: datetime
    api_calls: int = 0
    storage_bytes: int = 0
    compute_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Shield
# ---------------------------------------------------------------------------

class AgentRegistration(BaseModel):
    agent_id: str
    agent_type: str
    session_ttl_secs: int = 3600
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentSession(BaseModel):
    session_id: str
    agent_id: str
    agent_type: str
    created_at: datetime
    expires_at: datetime


class OperationContext(BaseModel):
    session_id: Optional[str] = None
    parent_operation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Operation(BaseModel):
    name: str
    input: Dict[str, Any] = Field(default_factory=dict)
    context: Optional[OperationContext] = None


class ScanRequest(BaseModel):
    agent_id: str
    session_id: str
    operation: Operation


class ScanResult(BaseModel):
    allowed: bool
    risk_score: float = 0.0
    reasons: List[str] = Field(default_factory=list)
    operation_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

class MutationRequest(BaseModel):
    resource: str
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class MutationResponse(BaseModel):
    id: str
    resource: str
    action: str
    created_at: datetime


class Document(BaseModel):
    id: str
    resource: str
    content: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None


class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    offset: int = 0
    filters: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    results: List[Document] = Field(default_factory=list)
    total: int = 0


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------

class MemoryEntry(BaseModel):
    key: str
    value: str
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StoreRequest(BaseModel):
    key: str
    value: str
    tags: List[str] = Field(default_factory=list)


class MemoryQuery(BaseModel):
    tags: List[str] = Field(default_factory=list)
    prefix: Optional[str] = None
    limit: int = 100


# ---------------------------------------------------------------------------
# SOC / Observability
# ---------------------------------------------------------------------------

class StoredIncident(BaseModel):
    id: str
    tenant_id: Optional[str] = None
    severity: str
    status: str
    title: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class Alert(BaseModel):
    id: str
    incident_id: Optional[str] = None
    severity: str
    message: str
    source: Optional[str] = None
    created_at: datetime


class MetricSummary(BaseModel):
    name: str
    value: float
    unit: Optional[str] = None
    timestamp: datetime


class AggregateHealth(BaseModel):
    status: str
    services: Dict[str, str] = Field(default_factory=dict)
    timestamp: datetime


class PlatformStatus(BaseModel):
    healthy: bool
    version: Optional[str] = None
    uptime_secs: Optional[float] = None
    components: Dict[str, str] = Field(default_factory=dict)


class LlmLogEntry(BaseModel):
    id: str
    session_id: Optional[str] = None
    model: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: Optional[float] = None
    timestamp: datetime


class IngestResponse(BaseModel):
    ingested: int
    errors: List[str] = Field(default_factory=list)


class ProxyTunnelEvent(BaseModel):
    id: str
    session_id: str
    direction: str
    payload_bytes: int = 0
    timestamp: datetime


class CorrelatedSession(BaseModel):
    session_id: str
    agent_id: Optional[str] = None
    events: int = 0
    start_time: datetime
    end_time: Optional[datetime] = None


class SessionTimeline(BaseModel):
    session_id: str
    events: List[Dict[str, Any]] = Field(default_factory=list)


class HostTrafficSummary(BaseModel):
    host: str
    tenant_id: Optional[str] = None
    request_count: int = 0
    bytes_in: int = 0
    bytes_out: int = 0


class SessionCostSummary(BaseModel):
    session_id: str
    total_cost_usd: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0


class ThreatHeatmapEntry(BaseModel):
    category: str
    count: int = 0
    severity: str
    last_seen: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Gateway
# ---------------------------------------------------------------------------

class ToolCall(BaseModel):
    name: str
    input: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    agent_id: Optional[str] = None


class ToolResult(BaseModel):
    output: Any = None
    error: Optional[str] = None


class InterceptResult(BaseModel):
    allowed: bool
    modified_input: Optional[Dict[str, Any]] = None
    reasons: List[str] = Field(default_factory=list)
    policy_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

class ColumnDef(BaseModel):
    name: str
    col_type: str


class ColumnData(BaseModel):
    name: str
    data: List[Any]


class CreateTableRequest(BaseModel):
    table_name: str
    columns: List[ColumnDef]


class InsertRequest(BaseModel):
    table_name: str
    columns: List[ColumnData]


class FilterClause(BaseModel):
    column: str
    op: str
    value: Any


class QueryRequest(BaseModel):
    table_name: str
    filters: List[FilterClause] = Field(default_factory=list)
    columns: Optional[List[str]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class QueryResponse(BaseModel):
    columns: List[str] = Field(default_factory=list)
    rows: List[List[Any]] = Field(default_factory=list)
    total: int = 0


class VectorSearchRequest(BaseModel):
    table_name: str
    column: str
    vector: List[float]
    top_k: int = 10
    filters: List[FilterClause] = Field(default_factory=list)


class ScrollQueryRequest(BaseModel):
    table_name: str
    filters: List[FilterClause] = Field(default_factory=list)
    columns: Optional[List[str]] = None
    batch_size: int = 100
    cursor: Optional[str] = None


class ScrollQueryResponse(BaseModel):
    columns: List[str] = Field(default_factory=list)
    rows: List[List[Any]] = Field(default_factory=list)
    next_cursor: Optional[str] = None
    has_more: bool = False


class ClusterInitRequest(BaseModel):
    cluster_name: str
    node_count: int = 1
    replication_factor: int = 1
    config: Dict[str, Any] = Field(default_factory=dict)


class ClusterStatusResponse(BaseModel):
    cluster_name: str
    status: str
    node_count: int = 0
    healthy_nodes: int = 0
    version: Optional[str] = None


# ---------------------------------------------------------------------------
# Fleet
# ---------------------------------------------------------------------------

class AgentStatus(str, Enum):
    active = "active"
    idle = "idle"
    busy = "busy"
    error = "error"
    disconnected = "disconnected"
    offline = "offline"


class CommandType(str, Enum):
    restart = "restart"
    update_config = "update_config"
    revoke_credentials = "revoke_credentials"
    inject_tool = "inject_tool"
    remove_tool = "remove_tool"
    pause = "pause"
    resume = "resume"
    collect_diagnostics = "collect_diagnostics"
    update_version = "update_version"


class FleetStatus(BaseModel):
    total: int = 0
    online: int = 0
    degraded: int = 0
    offline: int = 0


class FleetAgent(BaseModel):
    agent_id: str
    status: AgentStatus
    last_seen: Optional[datetime] = None
    version: Optional[str] = None
    cpu_pct: Optional[float] = None
    memory_mb: Optional[float] = None
    llm_cost_usd: Optional[float] = None
    shard_id: Optional[str] = None
    tenant_id: Optional[str] = None
    connected_at: Optional[datetime] = None


class FleetAgentDetail(BaseModel):
    agent_id: str
    status: AgentStatus
    last_seen: Optional[datetime] = None
    version: Optional[str] = None
    cpu_pct: Optional[float] = None
    memory_mb: Optional[float] = None
    llm_tokens_in: int = 0
    llm_tokens_out: int = 0
    llm_cost_usd: Optional[float] = None
    shard_id: Optional[str] = None
    tenant_id: Optional[str] = None
    connected_at: Optional[datetime] = None
    capabilities: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FleetAgentListResponse(BaseModel):
    agents: List[FleetAgent] = Field(default_factory=list)
    total: int = 0
    limit: int = 100
    offset: int = 0


class FleetCommand(BaseModel):
    command_type: CommandType
    payload: Dict[str, Any] = Field(default_factory=dict)


class FleetCommandResponse(BaseModel):
    command_id: str
    agent_id: Optional[str] = None
    command_type: CommandType
    status: str = "pending"
    issued_at: Optional[datetime] = None


class FleetBroadcastResponse(BaseModel):
    command_id: str
    command_type: CommandType
    target_count: int = 0
    issued_at: Optional[datetime] = None


class FleetMetricPoint(BaseModel):
    timestamp: datetime
    cpu_pct: Optional[float] = None
    memory_mb: Optional[float] = None
    llm_tokens_in: int = 0
    llm_tokens_out: int = 0
    llm_cost_usd: Optional[float] = None


class FleetMetricsResponse(BaseModel):
    agent_id: str
    metrics: List[FleetMetricPoint] = Field(default_factory=list)


class FleetCommandAuditEntry(BaseModel):
    id: str
    command_type: CommandType
    payload: Dict[str, Any] = Field(default_factory=dict)
    issued_at: datetime
    acked: bool = False
    ack_message: Optional[str] = None


class FleetCommandHistory(BaseModel):
    agent_id: str
    commands: List[FleetCommandAuditEntry] = Field(default_factory=list)
    total: int = 0


class FleetAlertThresholds(BaseModel):
    missed_heartbeats: int = 3
    error_rate_pct: float = 5.0


class FleetConfig(BaseModel):
    heartbeat_interval_secs: int = 60
    metrics_interval_secs: int = 60
    max_agents: int = 1000
    alert_thresholds: FleetAlertThresholds = Field(default_factory=FleetAlertThresholds)
    auto_scale_enabled: bool = False


class FleetEvent(BaseModel):
    event_type: str
    agent_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    data: Dict[str, Any] = Field(default_factory=dict)
