"""Tests for IdentityResource — agent identity issuance."""

from __future__ import annotations

import httpx
import pytest
import respx

from sigmashake import (
    SigmaShake,
    AuthenticationError,
    NotFoundError,
    ServerError,
)
from sigmashake.models import IdentityTokenResponse


class TestIdentitySyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_issue_identity_success(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/identity/issue").mock(
            return_value=httpx.Response(
                200,
                json={
                    "token": "id-tok-abc",
                    "claims": {
                        "agent_id": "a1",
                        "capabilities": ["tool_use"],
                        "issued_at": "2026-01-01T00:00:00Z",
                        "expires_at": "2026-01-01T01:00:00Z",
                    },
                },
            )
        )
        identity = sync_client.identity.issue(
            agent_id="a1", capabilities=["tool_use"], ttl_secs=3600
        )
        assert isinstance(identity, IdentityTokenResponse)
        assert identity.token == "id-tok-abc"
        assert identity.claims.agent_id == "a1"
        assert identity.claims.capabilities == ["tool_use"]

    def test_issue_identity_multiple_capabilities(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/identity/issue").mock(
            return_value=httpx.Response(
                200,
                json={
                    "token": "id-tok-multi",
                    "claims": {
                        "agent_id": "a2",
                        "capabilities": ["tool_use", "code_gen", "file_access"],
                        "issued_at": "2026-01-01T00:00:00Z",
                        "expires_at": "2026-01-01T02:00:00Z",
                    },
                },
            )
        )
        identity = sync_client.identity.issue(
            agent_id="a2",
            capabilities=["tool_use", "code_gen", "file_access"],
            ttl_secs=7200,
        )
        assert identity.claims.capabilities == ["tool_use", "code_gen", "file_access"]

    def test_issue_identity_default_ttl(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        import json

        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "token": "id-tok-default",
                    "claims": {
                        "agent_id": "a1",
                        "capabilities": [],
                        "issued_at": "2026-01-01T00:00:00Z",
                        "expires_at": "2026-01-01T01:00:00Z",
                    },
                },
            )

        mock_api.post("/v1/identity/issue").mock(side_effect=capture)
        sync_client.identity.issue(agent_id="a1")
        assert captured["body"]["ttl_secs"] == 3600

    def test_issue_identity_sends_correct_body(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        import json

        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "token": "id-tok-x",
                    "claims": {
                        "agent_id": "agent-99",
                        "capabilities": ["read"],
                        "issued_at": "2026-01-01T00:00:00Z",
                        "expires_at": "2026-01-01T01:00:00Z",
                    },
                },
            )

        mock_api.post("/v1/identity/issue").mock(side_effect=capture)
        sync_client.identity.issue(
            agent_id="agent-99", capabilities=["read"], ttl_secs=1800
        )
        assert captured["body"]["agent_id"] == "agent-99"
        assert captured["body"]["capabilities"] == ["read"]
        assert captured["body"]["ttl_secs"] == 1800


class TestIdentityErrorHandling:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_401_raises_authentication_error(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/identity/issue").mock(
            return_value=httpx.Response(401, json={"message": "Invalid API key"})
        )
        with pytest.raises(AuthenticationError):
            sync_client.identity.issue(agent_id="a1")

    def test_404_raises_not_found_error(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/identity/issue").mock(
            return_value=httpx.Response(404, json={"message": "Agent not found"})
        )
        with pytest.raises(NotFoundError):
            sync_client.identity.issue(agent_id="nonexistent")

    def test_500_raises_server_error(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/identity/issue").mock(
            return_value=httpx.Response(500, json={"message": "Internal error"})
        )
        with pytest.raises(ServerError):
            sync_client.identity.issue(agent_id="a1")


class TestIdentityAsyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    @pytest.mark.asyncio
    async def test_async_issue_identity(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/identity/issue").mock(
            return_value=httpx.Response(
                200,
                json={
                    "token": "id-tok-async",
                    "claims": {
                        "agent_id": "a1",
                        "capabilities": ["tool_use"],
                        "issued_at": "2026-01-01T00:00:00Z",
                        "expires_at": "2026-01-01T01:00:00Z",
                    },
                },
            )
        )
        identity = await async_client.identity.async_issue(
            agent_id="a1", capabilities=["tool_use"]
        )
        assert identity.token == "id-tok-async"
        assert identity.claims.agent_id == "a1"
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_issue_identity_error(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/identity/issue").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )
        with pytest.raises(AuthenticationError):
            await async_client.identity.async_issue(agent_id="a1")
        await async_client.aclose()
