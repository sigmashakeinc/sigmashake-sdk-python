"""Tests for Pydantic model serialization and deserialization."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from sigmashake.models import (
    Account,
    AgentSession,
    ClusterStatusResponse,
    CreateTableRequest,
    ColumnDef,
    DataClassification,
    FilterClause,
    HostTrafficSummary,
    InsertRequest,
    ColumnData,
    InterceptResult,
    MemberRole,
    MemoryEntry,
    MutationResponse,
    Operation,
    OperationContext,
    QueryRequest,
    QueryResponse,
    ScanRequest,
    ScanResult,
    ScrollQueryResponse,
    SearchResponse,
    SessionTimeline,
    StoredIncident,
    Subscription,
    SubscriptionStatus,
    Tier,
    TokenRequest,
    TokenResponse,
    IssueIdentityRequest,
    IdentityTokenResponse,
    AgentIdentityClaims,
    TenantUsage,
    ThreatHeatmapEntry,
    ToolCall,
    VectorSearchRequest,
)


class TestEnums:
    def test_tier_values(self) -> None:
        assert Tier.free.value == "free"
        assert Tier.pro.value == "pro"
        assert Tier.enterprise.value == "enterprise"

    def test_member_role_values(self) -> None:
        assert MemberRole.owner.value == "owner"
        assert MemberRole.admin.value == "admin"
        assert MemberRole.member.value == "member"

    def test_subscription_status(self) -> None:
        assert SubscriptionStatus.active.value == "active"
        assert SubscriptionStatus.canceled.value == "canceled"

    def test_data_classification(self) -> None:
        assert DataClassification.restricted.value == "restricted"


class TestAuthModels:
    def test_token_request_serialize(self) -> None:
        req = TokenRequest(agent_id="a1", scopes=["read", "write"])
        data = req.model_dump()
        assert data["agent_id"] == "a1"
        assert data["scopes"] == ["read", "write"]

    def test_token_response_deserialize(self) -> None:
        resp = TokenResponse.model_validate({
            "token": "tok-abc",
            "expires_at": "2026-12-31T23:59:59Z",
            "scopes": ["read"],
        })
        assert resp.token == "tok-abc"
        assert resp.expires_at.year == 2026

    def test_identity_roundtrip(self) -> None:
        req = IssueIdentityRequest(agent_id="a1", capabilities=["tool_use"], ttl_secs=7200)
        assert req.ttl_secs == 7200

        resp = IdentityTokenResponse.model_validate({
            "token": "id-tok",
            "claims": {
                "agent_id": "a1",
                "capabilities": ["tool_use"],
                "issued_at": "2026-01-01T00:00:00Z",
                "expires_at": "2026-01-01T02:00:00Z",
            },
        })
        assert resp.claims.agent_id == "a1"
        assert resp.claims.capabilities == ["tool_use"]


class TestAccountModels:
    def test_account_deserialize(self) -> None:
        acct = Account.model_validate({
            "id": "acc-1",
            "name": "Test Org",
            "tier": "pro",
            "created_at": "2026-01-01T00:00:00Z",
        })
        assert acct.tier == Tier.pro
        assert acct.name == "Test Org"

    def test_subscription_deserialize(self) -> None:
        sub = Subscription.model_validate({
            "id": "sub-1",
            "account_id": "acc-1",
            "tier": "enterprise",
            "status": "active",
        })
        assert sub.status == SubscriptionStatus.active

    def test_tenant_usage(self) -> None:
        usage = TenantUsage.model_validate({
            "account_id": "acc-1",
            "period_start": "2026-01-01T00:00:00Z",
            "period_end": "2026-02-01T00:00:00Z",
            "api_calls": 1000,
            "storage_bytes": 500000,
            "compute_seconds": 123.45,
        })
        assert usage.api_calls == 1000


class TestShieldModels:
    def test_agent_session_deserialize(self) -> None:
        session = AgentSession.model_validate({
            "session_id": "sess-1",
            "agent_id": "a1",
            "agent_type": "coding",
            "created_at": "2026-01-01T00:00:00Z",
            "expires_at": "2026-01-01T01:00:00Z",
        })
        assert session.session_id == "sess-1"

    def test_scan_result_defaults(self) -> None:
        result = ScanResult(allowed=True)
        assert result.risk_score == 0.0
        assert result.reasons == []

    def test_operation_with_context(self) -> None:
        op = Operation(
            name="Bash",
            input={"command": "ls"},
            context=OperationContext(session_id="s1", metadata={"key": "val"}),
        )
        assert op.context.session_id == "s1"

    def test_scan_request_serialize(self) -> None:
        req = ScanRequest(
            agent_id="a1",
            session_id="s1",
            operation=Operation(name="Read", input={"path": "/etc/passwd"}),
        )
        data = req.model_dump()
        assert data["operation"]["name"] == "Read"


class TestDocumentModels:
    def test_mutation_response(self) -> None:
        resp = MutationResponse.model_validate({
            "id": "doc-1",
            "resource": "docs",
            "action": "create",
            "created_at": "2026-01-01T00:00:00Z",
        })
        assert resp.resource == "docs"

    def test_search_response_empty(self) -> None:
        resp = SearchResponse(results=[], total=0)
        assert len(resp.results) == 0


class TestMemoryModels:
    def test_memory_entry_roundtrip(self) -> None:
        entry = MemoryEntry(key="ctx", value="important", tags=["s1", "s2"])
        data = entry.model_dump()
        restored = MemoryEntry.model_validate(data)
        assert restored.key == "ctx"
        assert restored.tags == ["s1", "s2"]


class TestSOCModels:
    def test_stored_incident(self) -> None:
        incident = StoredIncident.model_validate({
            "id": "inc-1",
            "severity": "critical",
            "status": "open",
            "title": "Breach",
            "created_at": "2026-01-01T00:00:00Z",
        })
        assert incident.severity == "critical"

    def test_session_timeline(self) -> None:
        tl = SessionTimeline(session_id="s1", events=[{"type": "tool_call", "ts": 123}])
        assert len(tl.events) == 1

    def test_host_traffic_summary(self) -> None:
        h = HostTrafficSummary(host="api.example.com", request_count=500)
        assert h.bytes_in == 0

    def test_threat_heatmap_entry(self) -> None:
        entry = ThreatHeatmapEntry(category="injection", count=42, severity="high")
        assert entry.count == 42


class TestGatewayModels:
    def test_intercept_result(self) -> None:
        result = InterceptResult(allowed=False, reasons=["blocked by policy"], policy_id="p-1")
        assert not result.allowed
        assert result.policy_id == "p-1"

    def test_tool_call(self) -> None:
        tc = ToolCall(name="Bash", input={"command": "ls"}, session_id="s1", agent_id="a1")
        assert tc.name == "Bash"


class TestDBModels:
    def test_create_table_request(self) -> None:
        req = CreateTableRequest(
            table_name="events",
            columns=[ColumnDef(name="id", col_type="uint64"), ColumnDef(name="data", col_type="string")],
        )
        assert len(req.columns) == 2

    def test_insert_request(self) -> None:
        req = InsertRequest(
            table_name="events",
            columns=[
                ColumnData(name="id", data=[1, 2, 3]),
                ColumnData(name="data", data=["a", "b", "c"]),
            ],
        )
        assert req.columns[0].data == [1, 2, 3]

    def test_query_response(self) -> None:
        resp = QueryResponse.model_validate({
            "columns": ["id", "data"],
            "rows": [[1, "a"], [2, "b"]],
            "total": 2,
        })
        assert resp.total == 2

    def test_filter_clause(self) -> None:
        f = FilterClause(column="id", op="gt", value=5)
        assert f.op == "gt"

    def test_scroll_query_response(self) -> None:
        resp = ScrollQueryResponse.model_validate({
            "columns": ["id"],
            "rows": [[1], [2]],
            "next_cursor": "abc123",
            "has_more": True,
        })
        assert resp.has_more is True
        assert resp.next_cursor == "abc123"

    def test_vector_search_request(self) -> None:
        req = VectorSearchRequest(
            table_name="embeddings",
            column="vec",
            vector=[0.1, 0.2, 0.3],
            top_k=5,
        )
        assert len(req.vector) == 3

    def test_cluster_status(self) -> None:
        status = ClusterStatusResponse.model_validate({
            "cluster_name": "prod",
            "status": "healthy",
            "node_count": 3,
            "healthy_nodes": 3,
        })
        assert status.healthy_nodes == 3

    def test_query_request_serialize(self) -> None:
        req = QueryRequest(
            table_name="events",
            filters=[FilterClause(column="id", op="eq", value=1)],
            limit=10,
        )
        data = req.model_dump()
        assert data["table_name"] == "events"
        assert data["limit"] == 10
