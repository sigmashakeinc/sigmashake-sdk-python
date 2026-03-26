"""Tests for ShieldResource — agent registration and operation scanning."""

from __future__ import annotations

import httpx
import pytest
import respx

from sigmashake import (
    SigmaShake,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ServerError,
)
from sigmashake.models import AgentSession, ScanResult


class TestShieldSyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_register_agent(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/shield/register").mock(
            return_value=httpx.Response(
                200,
                json={
                    "session_id": "sess-1",
                    "agent_id": "a1",
                    "agent_type": "coding",
                    "created_at": "2026-01-01T00:00:00Z",
                    "expires_at": "2026-01-01T01:00:00Z",
                },
            )
        )
        session = sync_client.shield.register_agent(
            agent_id="a1", agent_type="coding"
        )
        assert isinstance(session, AgentSession)
        assert session.session_id == "sess-1"
        assert session.agent_type == "coding"

    def test_register_agent_with_custom_ttl(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        import json

        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "session_id": "sess-2",
                    "agent_id": "a1",
                    "agent_type": "assistant",
                    "created_at": "2026-01-01T00:00:00Z",
                    "expires_at": "2026-01-01T02:00:00Z",
                },
            )

        mock_api.post("/v1/shield/register").mock(side_effect=capture)
        sync_client.shield.register_agent(
            agent_id="a1", agent_type="assistant", session_ttl_secs=7200
        )
        assert captured["body"]["session_ttl_secs"] == 7200

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
                    "session_id": "sess-3",
                    "agent_id": "a1",
                    "agent_type": "coding",
                    "created_at": "2026-01-01T00:00:00Z",
                    "expires_at": "2026-01-01T01:00:00Z",
                },
            )

        mock_api.post("/v1/shield/register").mock(side_effect=capture)
        sync_client.shield.register_agent(
            agent_id="a1",
            agent_type="coding",
            metadata={"model": "claude-4"},
        )
        assert captured["body"]["metadata"] == {"model": "claude-4"}

    def test_scan_allowed(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/shield/scan").mock(
            return_value=httpx.Response(
                200,
                json={"allowed": True, "risk_score": 0.05, "reasons": []},
            )
        )
        result = sync_client.shield.scan(
            agent_id="a1",
            session_id="sess-1",
            operation={"name": "Bash", "input": {"command": "ls"}},
        )
        assert isinstance(result, ScanResult)
        assert result.allowed is True
        assert result.risk_score == 0.05
        assert result.reasons == []

    def test_scan_blocked(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/shield/scan").mock(
            return_value=httpx.Response(
                200,
                json={
                    "allowed": False,
                    "risk_score": 0.95,
                    "reasons": ["Dangerous command detected"],
                },
            )
        )
        result = sync_client.shield.scan(
            agent_id="a1",
            session_id="sess-1",
            operation={"name": "Bash", "input": {"command": "rm -rf /"}},
        )
        assert result.allowed is False
        assert result.risk_score == 0.95
        assert "Dangerous command detected" in result.reasons

    def test_scan_sends_correct_body(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        import json

        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200, json={"allowed": True, "risk_score": 0.0, "reasons": []}
            )

        mock_api.post("/v1/shield/scan").mock(side_effect=capture)
        sync_client.shield.scan(
            agent_id="agent-x",
            session_id="sess-y",
            operation={"name": "Read", "input": {"path": "/tmp/file"}},
        )
        assert captured["body"]["agent_id"] == "agent-x"
        assert captured["body"]["session_id"] == "sess-y"
        assert captured["body"]["operation"]["name"] == "Read"


class TestShieldErrorHandling:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_401_on_register(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/shield/register").mock(
            return_value=httpx.Response(401, json={"message": "Invalid API key"})
        )
        with pytest.raises(AuthenticationError):
            sync_client.shield.register_agent(agent_id="a1", agent_type="coding")

    def test_403_on_scan(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/shield/scan").mock(
            return_value=httpx.Response(403, json={"message": "Forbidden"})
        )
        with pytest.raises(AuthorizationError):
            sync_client.shield.scan(
                agent_id="a1",
                session_id="s1",
                operation={"name": "Bash", "input": {}},
            )

    def test_429_on_scan(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/shield/scan").mock(
            return_value=httpx.Response(
                429, json={"message": "Rate limited", "retry_after": 2.0}
            )
        )
        with pytest.raises(RateLimitError) as exc_info:
            sync_client.shield.scan(
                agent_id="a1",
                session_id="s1",
                operation={"name": "Bash", "input": {}},
            )
        assert exc_info.value.retry_after == 2.0

    def test_500_on_register(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/shield/register").mock(
            return_value=httpx.Response(500, json={"message": "Internal error"})
        )
        with pytest.raises(ServerError):
            sync_client.shield.register_agent(agent_id="a1", agent_type="coding")


class TestShieldAsyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    @pytest.mark.asyncio
    async def test_async_register_agent(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/shield/register").mock(
            return_value=httpx.Response(
                200,
                json={
                    "session_id": "sess-async",
                    "agent_id": "a1",
                    "agent_type": "coding",
                    "created_at": "2026-01-01T00:00:00Z",
                    "expires_at": "2026-01-01T01:00:00Z",
                },
            )
        )
        session = await async_client.shield.async_register_agent(
            agent_id="a1", agent_type="coding"
        )
        assert session.session_id == "sess-async"
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_scan(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/shield/scan").mock(
            return_value=httpx.Response(
                200,
                json={"allowed": True, "risk_score": 0.0, "reasons": []},
            )
        )
        result = await async_client.shield.async_scan(
            agent_id="a1",
            session_id="s1",
            operation={"name": "Read", "input": {"path": "/tmp"}},
        )
        assert result.allowed is True
        await async_client.aclose()
