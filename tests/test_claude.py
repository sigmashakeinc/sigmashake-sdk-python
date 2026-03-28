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
        assert len(tools) == 15

    def test_tool_names(self, mock_client):
        from sigmashake.claude import create_tools

        tools = create_tools(mock_client)
        names = [t.name for t in tools]
        assert "sigmashake_search_documents" in names
        assert "sigmashake_query_db" in names
        assert "sigmashake_vector_search" in names
        assert "sigmashake_store_memory" in names
        assert "sigmashake_recall_memory" in names
        assert "sigmashake_get_memory" in names
        assert "sigmashake_delete_memory" in names
        assert "sigmashake_list_alerts" in names
        assert "sigmashake_get_timeline" in names
        assert "sigmashake_shield_scan" in names
        assert "sigmashake_pipeline_status" in names
        assert "sigmashake_pipeline_metrics" in names
        assert "sigmashake_bottlenecks" in names
        assert "sigmashake_ai_brief" in names
        assert "sigmashake_list_agents" in names


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
