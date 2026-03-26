"""Tests for AgentsResource — agent registration, get, list."""

from __future__ import annotations

import httpx
import pytest
import respx

from sigmashake import (
    SigmaShake,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)


class TestAgentsSyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_register_agent(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/agents").mock(
            return_value=httpx.Response(
                200,
                json={
                    "agent_id": "agent-1",
                    "agent_type": "coding",
                    "status": "active",
                    "created_at": "2026-01-01T00:00:00Z",
                },
            )
        )
        result = sync_client.agents.register(agent_id="agent-1", agent_type="coding")
        assert result["agent_id"] == "agent-1"
        assert result["agent_type"] == "coding"

    def test_register_agent_with_metadata(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        import json

        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "agent_id": "agent-2",
                    "agent_type": "assistant",
                    "metadata": {"region": "us-east-1"},
                },
            )

        mock_api.post("/v1/agents").mock(side_effect=capture)
        result = sync_client.agents.register(
            agent_id="agent-2",
            agent_type="assistant",
            metadata={"region": "us-east-1"},
        )
        assert captured["body"]["metadata"] == {"region": "us-east-1"}
        assert result["metadata"]["region"] == "us-east-1"

    def test_get_agent(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/agents/agent-1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "agent_id": "agent-1",
                    "agent_type": "coding",
                    "status": "active",
                },
            )
        )
        result = sync_client.agents.get("agent-1")
        assert result["agent_id"] == "agent-1"

    def test_list_agents(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/agents").mock(
            return_value=httpx.Response(
                200,
                json={
                    "agents": [
                        {"agent_id": "a1", "agent_type": "coding"},
                        {"agent_id": "a2", "agent_type": "assistant"},
                    ]
                },
            )
        )
        agents = sync_client.agents.list()
        assert len(agents) == 2
        assert agents[0]["agent_id"] == "a1"

    def test_list_agents_with_pagination(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["params"] = dict(request.url.params)
            return httpx.Response(
                200,
                json={"agents": [{"agent_id": "a3", "agent_type": "coding"}]},
            )

        mock_api.get("/v1/agents").mock(side_effect=capture)
        agents = sync_client.agents.list(limit=10, offset=20)
        assert captured["params"]["limit"] == "10"
        assert captured["params"]["offset"] == "20"
        assert len(agents) == 1

    def test_list_agents_empty(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/agents").mock(
            return_value=httpx.Response(200, json={"agents": []})
        )
        agents = sync_client.agents.list()
        assert agents == []


class TestAgentsErrorHandling:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_401_on_register(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/agents").mock(
            return_value=httpx.Response(401, json={"message": "Invalid API key"})
        )
        with pytest.raises(AuthenticationError):
            sync_client.agents.register(agent_id="a1", agent_type="coding")

    def test_404_on_get_agent(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/agents/nonexistent").mock(
            return_value=httpx.Response(404, json={"message": "Not found"})
        )
        with pytest.raises(NotFoundError):
            sync_client.agents.get("nonexistent")

    def test_422_on_register_invalid(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/agents").mock(
            return_value=httpx.Response(
                422, json={"message": "Invalid agent_type"}
            )
        )
        with pytest.raises(ValidationError):
            sync_client.agents.register(agent_id="a1", agent_type="")

    def test_429_on_list(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/agents").mock(
            return_value=httpx.Response(
                429, json={"message": "Rate limited", "retry_after": 1.0}
            )
        )
        with pytest.raises(RateLimitError) as exc_info:
            sync_client.agents.list()
        assert exc_info.value.retry_after == 1.0

    def test_500_on_get_agent(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/agents/a1").mock(
            return_value=httpx.Response(500, json={"message": "Internal error"})
        )
        with pytest.raises(ServerError):
            sync_client.agents.get("a1")


class TestAgentsAsyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    @pytest.mark.asyncio
    async def test_async_register(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/agents").mock(
            return_value=httpx.Response(
                200,
                json={
                    "agent_id": "agent-async",
                    "agent_type": "assistant",
                    "status": "active",
                },
            )
        )
        result = await async_client.agents.async_register(
            agent_id="agent-async", agent_type="assistant"
        )
        assert result["agent_id"] == "agent-async"
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_get(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/agents/agent-1").mock(
            return_value=httpx.Response(
                200,
                json={"agent_id": "agent-1", "agent_type": "coding"},
            )
        )
        result = await async_client.agents.async_get("agent-1")
        assert result["agent_id"] == "agent-1"
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_list(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/agents").mock(
            return_value=httpx.Response(
                200,
                json={"agents": [{"agent_id": "a1", "agent_type": "coding"}]},
            )
        )
        agents = await async_client.agents.async_list()
        assert len(agents) == 1
        await async_client.aclose()
