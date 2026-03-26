"""Tests for GatewayResource — pre/post intercept operations."""

from __future__ import annotations

import httpx
import pytest
import respx

from sigmashake import (
    SigmaShake,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ServerError,
)
from sigmashake.models import InterceptResult


class TestGatewaySyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_intercept_pre_allowed(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/gateway/intercept/pre").mock(
            return_value=httpx.Response(
                200,
                json={"allowed": True, "reasons": [], "modified_input": None},
            )
        )
        result = sync_client.gateway.intercept_pre(
            name="Bash",
            input={"command": "ls"},
            session_id="s1",
            agent_id="a1",
        )
        assert isinstance(result, InterceptResult)
        assert result.allowed is True
        assert result.reasons == []

    def test_intercept_pre_blocked(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/gateway/intercept/pre").mock(
            return_value=httpx.Response(
                200,
                json={
                    "allowed": False,
                    "reasons": ["blocked by policy"],
                    "modified_input": None,
                    "policy_id": "policy-1",
                },
            )
        )
        result = sync_client.gateway.intercept_pre(
            name="Bash",
            input={"command": "rm -rf /"},
            session_id="s1",
            agent_id="a1",
        )
        assert result.allowed is False
        assert "blocked by policy" in result.reasons
        assert result.policy_id == "policy-1"

    def test_intercept_pre_with_modified_input(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/gateway/intercept/pre").mock(
            return_value=httpx.Response(
                200,
                json={
                    "allowed": True,
                    "reasons": [],
                    "modified_input": {"command": "ls -la"},
                },
            )
        )
        result = sync_client.gateway.intercept_pre(
            name="Bash",
            input={"command": "ls"},
            session_id="s1",
            agent_id="a1",
        )
        assert result.modified_input == {"command": "ls -la"}

    def test_intercept_pre_sends_correct_body(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        import json

        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200, json={"allowed": True, "reasons": [], "modified_input": None}
            )

        mock_api.post("/v1/gateway/intercept/pre").mock(side_effect=capture)
        sync_client.gateway.intercept_pre(
            name="Read",
            input={"path": "/tmp/file"},
            session_id="sess-x",
            agent_id="agent-y",
        )
        assert captured["body"]["name"] == "Read"
        assert captured["body"]["input"]["path"] == "/tmp/file"
        assert captured["body"]["session_id"] == "sess-x"
        assert captured["body"]["agent_id"] == "agent-y"

    def test_intercept_post_allowed(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/gateway/intercept/post").mock(
            return_value=httpx.Response(
                200,
                json={"allowed": True, "reasons": [], "modified_input": None},
            )
        )
        result = sync_client.gateway.intercept_post(
            name="Bash",
            input={"command": "ls"},
            output="file1.txt\nfile2.txt",
            session_id="s1",
            agent_id="a1",
        )
        assert result.allowed is True

    def test_intercept_post_sends_output(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        import json

        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200, json={"allowed": True, "reasons": [], "modified_input": None}
            )

        mock_api.post("/v1/gateway/intercept/post").mock(side_effect=capture)
        sync_client.gateway.intercept_post(
            name="Bash",
            input={"command": "cat /etc/passwd"},
            output="root:x:0:0...",
            session_id="s1",
            agent_id="a1",
        )
        assert captured["body"]["output"] == "root:x:0:0..."
        assert captured["body"]["name"] == "Bash"

    def test_intercept_post_blocked(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/gateway/intercept/post").mock(
            return_value=httpx.Response(
                200,
                json={
                    "allowed": False,
                    "reasons": ["sensitive data in output"],
                    "policy_id": "p-2",
                },
            )
        )
        result = sync_client.gateway.intercept_post(
            name="Bash",
            input={"command": "cat /etc/shadow"},
            output="sensitive content",
            session_id="s1",
            agent_id="a1",
        )
        assert result.allowed is False
        assert result.policy_id == "p-2"


class TestGatewayErrorHandling:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_401_on_intercept_pre(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/gateway/intercept/pre").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )
        with pytest.raises(AuthenticationError):
            sync_client.gateway.intercept_pre(
                name="Bash", input={}, session_id="s1", agent_id="a1"
            )

    def test_403_on_intercept_post(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/gateway/intercept/post").mock(
            return_value=httpx.Response(403, json={"message": "Forbidden"})
        )
        with pytest.raises(AuthorizationError):
            sync_client.gateway.intercept_post(
                name="Bash", input={}, output="", session_id="s1", agent_id="a1"
            )

    def test_429_on_intercept_pre(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/gateway/intercept/pre").mock(
            return_value=httpx.Response(
                429, json={"message": "Rate limited", "retry_after": 1.0}
            )
        )
        with pytest.raises(RateLimitError) as exc_info:
            sync_client.gateway.intercept_pre(
                name="Bash", input={}, session_id="s1", agent_id="a1"
            )
        assert exc_info.value.retry_after == 1.0

    def test_500_on_intercept_pre(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/gateway/intercept/pre").mock(
            return_value=httpx.Response(500, json={"message": "Internal error"})
        )
        with pytest.raises(ServerError):
            sync_client.gateway.intercept_pre(
                name="Bash", input={}, session_id="s1", agent_id="a1"
            )


class TestGatewayAsyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    @pytest.mark.asyncio
    async def test_async_intercept_pre(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/gateway/intercept/pre").mock(
            return_value=httpx.Response(
                200,
                json={"allowed": True, "reasons": [], "modified_input": None},
            )
        )
        result = await async_client.gateway.async_intercept_pre(
            name="Bash",
            input={"command": "ls"},
            session_id="s1",
            agent_id="a1",
        )
        assert result.allowed is True
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_intercept_post(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/gateway/intercept/post").mock(
            return_value=httpx.Response(
                200,
                json={"allowed": True, "reasons": []},
            )
        )
        result = await async_client.gateway.async_intercept_post(
            name="Read",
            input={"path": "/tmp"},
            output="file content",
            session_id="s1",
            agent_id="a1",
        )
        assert result.allowed is True
        await async_client.aclose()
