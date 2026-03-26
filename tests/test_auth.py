"""Tests for AuthResource — token creation and validation."""

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
from sigmashake.models import TokenResponse


class TestAuthSyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_create_token_success(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/auth/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "token": "tok-abc",
                    "expires_at": "2026-12-31T23:59:59Z",
                    "scopes": ["read"],
                },
            )
        )
        token = sync_client.auth.create_token(agent_id="a1", scopes=["read"])
        assert isinstance(token, TokenResponse)
        assert token.token == "tok-abc"
        assert token.scopes == ["read"]
        assert token.expires_at.year == 2026

    def test_create_token_multiple_scopes(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/auth/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "token": "tok-multi",
                    "expires_at": "2026-12-31T23:59:59Z",
                    "scopes": ["read", "write", "admin"],
                },
            )
        )
        token = sync_client.auth.create_token(
            agent_id="a1", scopes=["read", "write", "admin"]
        )
        assert token.scopes == ["read", "write", "admin"]

    def test_create_token_no_scopes_defaults_empty(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/auth/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "token": "tok-noscope",
                    "expires_at": "2026-12-31T23:59:59Z",
                    "scopes": [],
                },
            )
        )
        token = sync_client.auth.create_token(agent_id="a1")
        assert token.scopes == []

    def test_create_token_sends_correct_body(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        import json

        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "token": "tok-x",
                    "expires_at": "2026-12-31T23:59:59Z",
                    "scopes": ["read"],
                },
            )

        mock_api.post("/v1/auth/token").mock(side_effect=capture)
        sync_client.auth.create_token(agent_id="agent-42", scopes=["read"])
        assert captured["body"]["agent_id"] == "agent-42"
        assert captured["body"]["scopes"] == ["read"]


class TestAuthErrorHandling:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_401_raises_authentication_error(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/auth/token").mock(
            return_value=httpx.Response(401, json={"message": "Invalid API key"})
        )
        with pytest.raises(AuthenticationError) as exc_info:
            sync_client.auth.create_token(agent_id="a1", scopes=["read"])
        assert exc_info.value.status_code == 401

    def test_403_raises_authorization_error(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/auth/token").mock(
            return_value=httpx.Response(403, json={"message": "Forbidden"})
        )
        with pytest.raises(AuthorizationError):
            sync_client.auth.create_token(agent_id="a1")

    def test_429_raises_rate_limit_error_with_retry_after(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/auth/token").mock(
            return_value=httpx.Response(
                429, json={"message": "Too many requests", "retry_after": 2.5}
            )
        )
        with pytest.raises(RateLimitError) as exc_info:
            sync_client.auth.create_token(agent_id="a1")
        assert exc_info.value.retry_after == 2.5

    def test_500_raises_server_error(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/auth/token").mock(
            return_value=httpx.Response(500, json={"message": "Internal error"})
        )
        with pytest.raises(ServerError) as exc_info:
            sync_client.auth.create_token(agent_id="a1")
        assert exc_info.value.status_code == 500


class TestAuthAsyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    @pytest.mark.asyncio
    async def test_async_create_token(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/auth/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "token": "tok-async",
                    "expires_at": "2026-12-31T23:59:59Z",
                    "scopes": ["write"],
                },
            )
        )
        token = await async_client.auth.async_create_token(
            agent_id="a1", scopes=["write"]
        )
        assert token.token == "tok-async"
        assert token.scopes == ["write"]
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_create_token_error(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/auth/token").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )
        with pytest.raises(AuthenticationError):
            await async_client.auth.async_create_token(agent_id="a1")
        await async_client.aclose()
