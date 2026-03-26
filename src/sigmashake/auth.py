"""Auth and Identity token management."""

from __future__ import annotations

from typing import Any, List, TYPE_CHECKING

from .models import (
    IdentityTokenResponse,
    TokenResponse,
)

if TYPE_CHECKING:
    from .client import _HTTPTransport


class AuthResource:
    """Token creation and validation."""

    def __init__(self, transport: _HTTPTransport) -> None:
        self._t = transport

    def create_token(self, agent_id: str, scopes: List[str] | None = None) -> TokenResponse:
        body = {"agent_id": agent_id, "scopes": scopes or []}
        data = self._t.request("POST", "/api/auth/token", json=body)
        return TokenResponse.model_validate(data)

    async def async_create_token(self, agent_id: str, scopes: List[str] | None = None) -> TokenResponse:
        body = {"agent_id": agent_id, "scopes": scopes or []}
        data = await self._t.async_request("POST", "/api/auth/token", json=body)
        return TokenResponse.model_validate(data)


class IdentityResource:
    """Agent identity issuance."""

    def __init__(self, transport: _HTTPTransport) -> None:
        self._t = transport

    def issue(
        self,
        agent_id: str,
        capabilities: List[str] | None = None,
        ttl_secs: int = 3600,
    ) -> IdentityTokenResponse:
        raise NotImplementedError("Not yet implemented")

    async def async_issue(
        self,
        agent_id: str,
        capabilities: List[str] | None = None,
        ttl_secs: int = 3600,
    ) -> IdentityTokenResponse:
        raise NotImplementedError("Not yet implemented")
