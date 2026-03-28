"""Tests for the Claude Agent SDK integration module."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from sigmashake.client import SigmaShake


@pytest.fixture
def mock_client():
    """Create a mock SigmaShake client with all resources stubbed."""
    client = MagicMock(spec=SigmaShake)
    return client


class TestCreateTools:
    def test_returns_expected_tool_count(self, mock_client):
        from sigmashake.claude import create_tools

        tools = create_tools(mock_client)
        assert len(tools) == 49

    def test_tool_names(self, mock_client):
        from sigmashake.claude import create_tools

        tools = create_tools(mock_client)
        names = [t.name for t in tools]
        # Documents
        assert "sigmashake_search_documents" in names
        # DB
        assert "sigmashake_query_db" in names
        assert "sigmashake_vector_search" in names
        assert "sigmashake_db_scroll" in names
        assert "sigmashake_db_insert" in names
        # Memory
        assert "sigmashake_store_memory" in names
        assert "sigmashake_recall_memory" in names
        assert "sigmashake_get_memory" in names
        assert "sigmashake_delete_memory" in names
        # SOC
        assert "sigmashake_list_alerts" in names
        assert "sigmashake_get_timeline" in names
        # Shield
        assert "sigmashake_shield_scan" in names
        assert "sigmashake_shield_register" in names
        # Pulse
        assert "sigmashake_pipeline_status" in names
        assert "sigmashake_pipeline_metrics" in names
        assert "sigmashake_bottlenecks" in names
        assert "sigmashake_ai_brief" in names
        assert "sigmashake_get_pipeline_runs" in names
        assert "sigmashake_get_pipeline_run" in names
        assert "sigmashake_trigger_pipeline" in names
        assert "sigmashake_push_events" in names
        # Agents
        assert "sigmashake_list_agents" in names
        assert "sigmashake_register_agent" in names
        assert "sigmashake_get_agent" in names
        assert "sigmashake_update_agent" in names
        # Fleet
        assert "sigmashake_fleet_status" in names
        assert "sigmashake_fleet_list_agents" in names
        assert "sigmashake_fleet_get_agent" in names
        assert "sigmashake_fleet_send_command" in names
        assert "sigmashake_fleet_broadcast" in names
        assert "sigmashake_fleet_agent_metrics" in names
        assert "sigmashake_fleet_command_history" in names
        # Gateway
        assert "sigmashake_gateway_intercept_pre" in names
        assert "sigmashake_gateway_intercept_post" in names
        # Accounts
        assert "sigmashake_get_account" in names
        assert "sigmashake_get_account_usage" in names
        assert "sigmashake_get_subscription" in names
        # Auth
        assert "sigmashake_create_token" in names
        # Triggers
        assert "sigmashake_create_trigger" in names
        assert "sigmashake_list_triggers" in names
        assert "sigmashake_execute_trigger" in names
        assert "sigmashake_get_trigger_status" in names
        assert "sigmashake_delete_trigger" in names
        # Context
        assert "sigmashake_store_context" in names
        assert "sigmashake_get_context" in names
        assert "sigmashake_delete_context" in names
        # Agent Tools
        assert "sigmashake_register_tools" in names
        assert "sigmashake_list_agent_tools" in names
        assert "sigmashake_unregister_tool" in names
        # Agent Usage
        assert "sigmashake_get_agent_usage" in names


class TestJsonResult:
    def test_dict_result(self):
        from sigmashake.claude import _json_result

        result = _json_result({"status": "ok"})
        assert result["content"][0]["type"] == "text"
        parsed = json.loads(result["content"][0]["text"])
        assert parsed["status"] == "ok"

    def test_list_result(self):
        from sigmashake.claude import _json_result

        result = _json_result([{"a": 1}, {"b": 2}])
        parsed = json.loads(result["content"][0]["text"])
        assert len(parsed) == 2

    def test_pydantic_model_result(self):
        from sigmashake.claude import _json_result
        from sigmashake.models import ScanResult

        scan = ScanResult(allowed=True, risk_score=0.1, reasons=["safe"])
        result = _json_result(scan)
        parsed = json.loads(result["content"][0]["text"])
        assert parsed["allowed"] is True
        assert parsed["risk_score"] == 0.1

    def test_pydantic_list_result(self):
        from sigmashake.claude import _json_result
        from sigmashake.models import MemoryEntry

        entries = [
            MemoryEntry(key="k1", value="v1"),
            MemoryEntry(key="k2", value="v2"),
        ]
        result = _json_result(entries)
        parsed = json.loads(result["content"][0]["text"])
        assert len(parsed) == 2
        assert parsed[0]["key"] == "k1"

    def test_string_result(self):
        from sigmashake.claude import _json_result

        result = _json_result("hello")
        assert result["content"][0]["text"] == "hello"


class TestCreateMcpServer:
    def test_returns_server_dict(self, mock_client):
        from sigmashake.claude import create_mcp_server

        server = create_mcp_server(mock_client)
        assert server is not None

    def test_custom_name(self, mock_client):
        from sigmashake.claude import create_mcp_server

        server = create_mcp_server(mock_client, name="custom-ss")
        assert server is not None


class TestToolExecution:
    @pytest.mark.asyncio
    async def test_search_documents(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import SearchResponse

        mock_client.documents.search.return_value = SearchResponse(results=[], total=0)
        tools = create_tools(mock_client)
        search_tool = next(t for t in tools if t.name == "sigmashake_search_documents")
        result = await search_tool({"query": "test", "limit": 5, "offset": 0})
        mock_client.documents.search.assert_called_once_with(query="test", limit=5, offset=0)
        parsed = json.loads(result["content"][0]["text"])
        assert parsed["total"] == 0

    @pytest.mark.asyncio
    async def test_query_db(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import QueryResponse

        mock_client.db.query.return_value = QueryResponse(columns=["id"], rows=[[1]], total=1)
        tools = create_tools(mock_client)
        query_tool = next(t for t in tools if t.name == "sigmashake_query_db")
        result = await query_tool({"table_name": "users"})
        mock_client.db.query.assert_called_once_with(
            table_name="users", filters=None, columns=None, limit=None
        )
        parsed = json.loads(result["content"][0]["text"])
        assert parsed["total"] == 1

    @pytest.mark.asyncio
    async def test_store_memory(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import MemoryEntry

        mock_client.memory.store.return_value = MemoryEntry(key="k", value="v")
        tools = create_tools(mock_client)
        store_tool = next(t for t in tools if t.name == "sigmashake_store_memory")
        result = await store_tool({"agent_id": "a1", "key": "k", "value": "v"})
        mock_client.memory.store.assert_called_once_with(
            agent_id="a1", key="k", value="v", tags=None
        )

    @pytest.mark.asyncio
    async def test_recall_memory(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.memory.recall.return_value = []
        tools = create_tools(mock_client)
        recall_tool = next(t for t in tools if t.name == "sigmashake_recall_memory")
        result = await recall_tool({"agent_id": "a1", "query": "search term"})
        mock_client.memory.recall.assert_called_once_with(agent_id="a1", query="search term")

    @pytest.mark.asyncio
    async def test_delete_memory(self, mock_client):
        from sigmashake.claude import create_tools

        tools = create_tools(mock_client)
        delete_tool = next(t for t in tools if t.name == "sigmashake_delete_memory")
        result = await delete_tool({"agent_id": "a1", "key": "k"})
        mock_client.memory.delete.assert_called_once_with(agent_id="a1", key="k")
        assert result["content"][0]["text"] == "deleted"

    @pytest.mark.asyncio
    async def test_list_alerts(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.soc.list_alerts.return_value = []
        tools = create_tools(mock_client)
        alerts_tool = next(t for t in tools if t.name == "sigmashake_list_alerts")
        result = await alerts_tool({"severity": "critical", "limit": 10})
        mock_client.soc.list_alerts.assert_called_once_with(
            status=None, severity="critical", limit=10
        )

    @pytest.mark.asyncio
    async def test_shield_scan(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import ScanResult

        mock_client.shield.scan.return_value = ScanResult(allowed=True, risk_score=0.0)
        tools = create_tools(mock_client)
        scan_tool = next(t for t in tools if t.name == "sigmashake_shield_scan")
        op = {"name": "read_file", "input": {"path": "/etc/passwd"}}
        result = await scan_tool({"agent_id": "a1", "session_id": "s1", "operation": op})
        mock_client.shield.scan.assert_called_once_with(
            agent_id="a1", session_id="s1", operation=op
        )

    @pytest.mark.asyncio
    async def test_pipeline_status(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.pulse.get_status.return_value = {"status": "healthy"}
        tools = create_tools(mock_client)
        status_tool = next(t for t in tools if t.name == "sigmashake_pipeline_status")
        result = await status_tool({})
        mock_client.pulse.get_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_bottlenecks(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.pulse.get_bottlenecks.return_value = {"bottlenecks": [], "total": 0}
        tools = create_tools(mock_client)
        bn_tool = next(t for t in tools if t.name == "sigmashake_bottlenecks")
        result = await bn_tool({"min_score": 0.5, "limit": 5})
        mock_client.pulse.get_bottlenecks.assert_called_once_with(min_score=0.5, limit=5)

    @pytest.mark.asyncio
    async def test_list_agents(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.agents.list.return_value = []
        tools = create_tools(mock_client)
        agents_tool = next(t for t in tools if t.name == "sigmashake_list_agents")
        result = await agents_tool({"limit": 50})
        mock_client.agents.list.assert_called_once_with(limit=50, offset=0)

    @pytest.mark.asyncio
    async def test_register_agent(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.agents.register.return_value = {"agent_id": "a1", "status": "registered"}
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_register_agent")
        result = await tool_fn({"agent_id": "a1", "agent_type": "worker"})
        mock_client.agents.register.assert_called_once_with(
            agent_id="a1", agent_type="worker", metadata=None
        )

    @pytest.mark.asyncio
    async def test_get_agent(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.agents.get.return_value = {"agent_id": "a1"}
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_get_agent")
        result = await tool_fn({"agent_id": "a1"})
        mock_client.agents.get.assert_called_once_with(agent_id="a1")

    @pytest.mark.asyncio
    async def test_update_agent(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.agents.update.return_value = {"agent_id": "a1"}
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_update_agent")
        result = await tool_fn({"agent_id": "a1", "metadata": {"name": "new"}})
        mock_client.agents.update.assert_called_once_with(agent_id="a1", name="new")

    @pytest.mark.asyncio
    async def test_shield_register(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import AgentSession
        from datetime import datetime

        mock_client.shield.register_agent.return_value = AgentSession(
            session_id="s1", agent_id="a1", agent_type="worker",
            created_at=datetime.now(), expires_at=datetime.now(),
        )
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_shield_register")
        result = await tool_fn({"agent_id": "a1", "agent_type": "worker"})
        mock_client.shield.register_agent.assert_called_once_with(
            agent_id="a1", agent_type="worker", session_ttl_secs=3600, metadata=None
        )

    @pytest.mark.asyncio
    async def test_get_pipeline_runs(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.pulse.get_runs.return_value = {"items": [], "total": 0}
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_get_pipeline_runs")
        result = await tool_fn({"page": 2, "per_page": 10})
        mock_client.pulse.get_runs.assert_called_once_with(
            page=2, per_page=10, from_ts=None, to_ts=None
        )

    @pytest.mark.asyncio
    async def test_get_pipeline_run(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.pulse.get_run.return_value = {"run_id": "r1"}
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_get_pipeline_run")
        result = await tool_fn({"run_id": "r1"})
        mock_client.pulse.get_run.assert_called_once_with(run_id="r1")

    @pytest.mark.asyncio
    async def test_trigger_pipeline(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.pulse.trigger_run.return_value = {"run_id": "r1"}
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_trigger_pipeline")
        result = await tool_fn({"trigger_type": "manual"})
        mock_client.pulse.trigger_run.assert_called_once_with(
            trigger_type="manual", config=None
        )

    @pytest.mark.asyncio
    async def test_push_events(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.pulse.push_event.return_value = {"accepted": 1}
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_push_events")
        events = [{"event_type": "deploy", "timestamp": "2026-03-27T00:00:00Z"}]
        result = await tool_fn({"events": events})
        mock_client.pulse.push_event.assert_called_once_with(events=events)

    @pytest.mark.asyncio
    async def test_fleet_status(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import FleetStatus

        mock_client.fleet.status.return_value = FleetStatus(total=10, online=8, degraded=1, offline=1)
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_fleet_status")
        result = await tool_fn({})
        mock_client.fleet.status.assert_called_once()
        parsed = json.loads(result["content"][0]["text"])
        assert parsed["total"] == 10

    @pytest.mark.asyncio
    async def test_fleet_list_agents(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import FleetAgentListResponse

        mock_client.fleet.list_agents.return_value = FleetAgentListResponse(agents=[], total=0)
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_fleet_list_agents")
        result = await tool_fn({"status": "active"})
        mock_client.fleet.list_agents.assert_called_once_with(status="active", limit=100, offset=0)

    @pytest.mark.asyncio
    async def test_fleet_get_agent(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import FleetAgentDetail

        mock_client.fleet.get_agent.return_value = FleetAgentDetail(agent_id="a1", status="active")
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_fleet_get_agent")
        result = await tool_fn({"agent_id": "a1"})
        mock_client.fleet.get_agent.assert_called_once_with(agent_id="a1")

    @pytest.mark.asyncio
    async def test_fleet_send_command(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import FleetCommandResponse

        mock_client.fleet.send_command.return_value = FleetCommandResponse(
            command_id="c1", command_type="restart"
        )
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_fleet_send_command")
        result = await tool_fn({"agent_id": "a1", "command_type": "restart"})
        mock_client.fleet.send_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_fleet_broadcast(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import FleetBroadcastResponse

        mock_client.fleet.broadcast.return_value = FleetBroadcastResponse(
            command_id="c1", command_type="pause", target_count=5
        )
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_fleet_broadcast")
        result = await tool_fn({"command_type": "pause"})
        mock_client.fleet.broadcast.assert_called_once()

    @pytest.mark.asyncio
    async def test_fleet_agent_metrics(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import FleetMetricsResponse

        mock_client.fleet.get_metrics.return_value = FleetMetricsResponse(agent_id="a1", metrics=[])
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_fleet_agent_metrics")
        result = await tool_fn({"agent_id": "a1", "period": "1h"})
        mock_client.fleet.get_metrics.assert_called_once_with(agent_id="a1", period="1h")

    @pytest.mark.asyncio
    async def test_fleet_command_history(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import FleetCommandHistory

        mock_client.fleet.get_command_history.return_value = FleetCommandHistory(
            agent_id="a1", commands=[], total=0
        )
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_fleet_command_history")
        result = await tool_fn({"agent_id": "a1"})
        mock_client.fleet.get_command_history.assert_called_once_with(
            agent_id="a1", limit=100, offset=0
        )

    @pytest.mark.asyncio
    async def test_gateway_intercept_pre(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import InterceptResult

        mock_client.gateway.intercept_pre.return_value = InterceptResult(allowed=True)
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_gateway_intercept_pre")
        result = await tool_fn({
            "name": "read_file", "input": {"path": "/tmp/x"},
            "session_id": "s1", "agent_id": "a1",
        })
        mock_client.gateway.intercept_pre.assert_called_once()

    @pytest.mark.asyncio
    async def test_gateway_intercept_post(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import InterceptResult

        mock_client.gateway.intercept_post.return_value = InterceptResult(allowed=True)
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_gateway_intercept_post")
        result = await tool_fn({
            "name": "read_file", "input": {"path": "/tmp/x"},
            "output": {"content": "data"}, "session_id": "s1", "agent_id": "a1",
        })
        mock_client.gateway.intercept_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_account(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import Account
        from datetime import datetime

        mock_client.accounts.get.return_value = Account(
            id="acc1", name="Test", tier="pro", created_at=datetime.now()
        )
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_get_account")
        result = await tool_fn({"account_id": "acc1"})
        mock_client.accounts.get.assert_called_once_with(account_id="acc1")

    @pytest.mark.asyncio
    async def test_get_account_usage(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import TenantUsage
        from datetime import datetime

        mock_client.accounts.get_usage.return_value = TenantUsage(
            account_id="acc1", period_start=datetime.now(), period_end=datetime.now(),
            api_calls=100, storage_bytes=1024,
        )
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_get_account_usage")
        result = await tool_fn({"account_id": "acc1"})
        mock_client.accounts.get_usage.assert_called_once_with(account_id="acc1")

    @pytest.mark.asyncio
    async def test_get_subscription(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import Subscription

        mock_client.accounts.get_subscription.return_value = Subscription(
            id="sub1", account_id="acc1", tier="pro", status="active"
        )
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_get_subscription")
        result = await tool_fn({"account_id": "acc1"})
        mock_client.accounts.get_subscription.assert_called_once_with(account_id="acc1")

    @pytest.mark.asyncio
    async def test_create_token(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import TokenResponse
        from datetime import datetime

        mock_client.auth.create_token.return_value = TokenResponse(
            token="tok_xxx", expires_at=datetime.now(), scopes=["read"]
        )
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_create_token")
        result = await tool_fn({"agent_id": "a1", "scopes": ["read"]})
        mock_client.auth.create_token.assert_called_once_with(
            agent_id="a1", scopes=["read"]
        )

    @pytest.mark.asyncio
    async def test_create_trigger(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.agents.create_trigger.return_value = {"trigger_id": "t1"}
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_create_trigger")
        result = await tool_fn({
            "agent_id": "a1", "name": "daily-check", "prompt": "Check status",
        })
        mock_client.agents.create_trigger.assert_called_once()
        call_args = mock_client.agents.create_trigger.call_args
        assert call_args[0][0] == "a1"
        assert call_args[0][1]["name"] == "daily-check"
        assert call_args[0][1]["max_turns"] == 10

    @pytest.mark.asyncio
    async def test_list_triggers(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.agents.list_triggers.return_value = []
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_list_triggers")
        result = await tool_fn({"agent_id": "a1"})
        mock_client.agents.list_triggers.assert_called_once_with("a1")

    @pytest.mark.asyncio
    async def test_execute_trigger(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.agents.execute_trigger.return_value = {"status": "running"}
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_execute_trigger")
        result = await tool_fn({"agent_id": "a1", "trigger_id": "t1"})
        mock_client.agents.execute_trigger.assert_called_once_with("a1", "t1")

    @pytest.mark.asyncio
    async def test_get_trigger_status(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.agents.get_trigger_status.return_value = {"status": "completed"}
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_get_trigger_status")
        result = await tool_fn({"agent_id": "a1", "trigger_id": "t1"})
        mock_client.agents.get_trigger_status.assert_called_once_with("a1", "t1")

    @pytest.mark.asyncio
    async def test_delete_trigger(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.agents.delete_trigger.return_value = {"deleted": True}
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_delete_trigger")
        result = await tool_fn({"agent_id": "a1", "trigger_id": "t1"})
        mock_client.agents.delete_trigger.assert_called_once_with("a1", "t1")

    @pytest.mark.asyncio
    async def test_store_context(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.agents.store_context.return_value = {"stored": True}
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_store_context")
        result = await tool_fn({
            "agent_id": "a1",
            "conversation_context": {"messages": []},
            "system_prompt": "You are helpful",
        })
        mock_client.agents.store_context.assert_called_once()
        call_args = mock_client.agents.store_context.call_args
        assert call_args[0][0] == "a1"
        assert call_args[0][1]["system_prompt"] == "You are helpful"

    @pytest.mark.asyncio
    async def test_get_context(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.agents.get_context.return_value = {"conversation_context": {}}
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_get_context")
        result = await tool_fn({"agent_id": "a1"})
        mock_client.agents.get_context.assert_called_once_with("a1")

    @pytest.mark.asyncio
    async def test_delete_context(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.agents.delete_context.return_value = {"deleted": True}
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_delete_context")
        result = await tool_fn({"agent_id": "a1"})
        mock_client.agents.delete_context.assert_called_once_with("a1")

    @pytest.mark.asyncio
    async def test_register_tools(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.agents.register_tools.return_value = {"registered": 2}
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_register_tools")
        tool_defs = [
            {"name": "read_file", "description": "Read a file", "input_schema": {}},
        ]
        result = await tool_fn({"agent_id": "a1", "tools": tool_defs})
        mock_client.agents.register_tools.assert_called_once_with("a1", tool_defs)

    @pytest.mark.asyncio
    async def test_list_agent_tools(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.agents.list_tools.return_value = []
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_list_agent_tools")
        result = await tool_fn({"agent_id": "a1"})
        mock_client.agents.list_tools.assert_called_once_with("a1")

    @pytest.mark.asyncio
    async def test_unregister_tool(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.agents.unregister_tool.return_value = {"deleted": True}
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_unregister_tool")
        result = await tool_fn({"agent_id": "a1", "tool_name": "read_file"})
        mock_client.agents.unregister_tool.assert_called_once_with("a1", "read_file")

    @pytest.mark.asyncio
    async def test_get_agent_usage(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.agents.get_usage.return_value = {"api_calls": 50}
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_get_agent_usage")
        result = await tool_fn({
            "agent_id": "a1", "from_date": "2026-03-01", "to_date": "2026-03-27",
        })
        mock_client.agents.get_usage.assert_called_once_with(
            "a1", from_date="2026-03-01", to_date="2026-03-27"
        )

    @pytest.mark.asyncio
    async def test_db_scroll(self, mock_client):
        from sigmashake.claude import create_tools
        from sigmashake.models import ScrollQueryResponse

        mock_client.db.scroll.return_value = ScrollQueryResponse(
            columns=["id"], rows=[[1]], has_more=False
        )
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_db_scroll")
        result = await tool_fn({"table_name": "logs", "batch_size": 50})
        mock_client.db.scroll.assert_called_once_with(
            table_name="logs", batch_size=50, cursor=None, filters=None
        )

    @pytest.mark.asyncio
    async def test_db_insert(self, mock_client):
        from sigmashake.claude import create_tools

        mock_client.db.insert.return_value = {"inserted": 1}
        tools = create_tools(mock_client)
        tool_fn = next(t for t in tools if t.name == "sigmashake_db_insert")
        cols = [{"name": "id", "data": [1]}]
        result = await tool_fn({"table_name": "events", "columns": cols})
        mock_client.db.insert.assert_called_once_with(table_name="events", columns=cols)
