"""Main SigmaShake client -- sync and async HTTP transport."""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from .auth import AuthResource, IdentityResource
from .accounts import AccountsResource
from .agents import AgentsResource
from .db import DBResource
from .exceptions import raise_for_status
from .gateway import GatewayResource
from .memory import MemoryResource
from .shield import ShieldResource
from .soc import SOCResource


_DEFAULT_BASE_URL = "https://api.sigmashake.com"
_DEFAULT_TIMEOUT = 30.0


class _HTTPTransport:
    """Thin wrapper around httpx providing sync and async request methods."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout: float,
        async_mode: bool,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._async_mode = async_mode
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "sigmashake-python/0.1.0",
        }
        if async_mode:
            self._async_client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=headers,
                timeout=timeout,
            )
            self._sync_client = None
        else:
            self._sync_client = httpx.Client(
                base_url=self._base_url,
                headers=headers,
                timeout=timeout,
            )
            self._async_client = None

    # -- sync -----------------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        assert self._sync_client is not None, "Use async_request in async_mode"
        resp = self._sync_client.request(method, path, json=json, params=params)
        body = resp.json() if resp.content else {}
        raise_for_status(resp.status_code, body)
        return body

    # -- async ----------------------------------------------------------------

    async def async_request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        assert self._async_client is not None, "Use request in sync mode"
        resp = await self._async_client.request(method, path, json=json, params=params)
        body = resp.json() if resp.content else {}
        raise_for_status(resp.status_code, body)
        return body

    # -- lifecycle ------------------------------------------------------------

    def close(self) -> None:
        if self._sync_client is not None:
            self._sync_client.close()

    async def aclose(self) -> None:
        if self._async_client is not None:
            await self._async_client.aclose()


class SigmaShake:
    """Top-level SigmaShake client.

    Usage (sync)::

        client = SigmaShake(api_key="sk-...")
        token = client.auth.create_token(agent_id="a1", scopes=["read"])

    Usage (async)::

        async with SigmaShake(api_key="sk-...", async_mode=True) as client:
            token = await client.auth.create_token(agent_id="a1", scopes=["read"])
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
        async_mode: bool = False,
    ) -> None:
        self._transport = _HTTPTransport(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            async_mode=async_mode,
        )
        self._async_mode = async_mode

        # Resource namespaces
        self.auth = AuthResource(self._transport)
        self.identity = IdentityResource(self._transport)
        self.accounts = AccountsResource(self._transport)
        self.agents = AgentsResource(self._transport)
        self.shield = ShieldResource(self._transport)
        self.documents = AgentsResource(self._transport)  # alias kept for back-compat
        self.soc = SOCResource(self._transport)
        self.gateway = GatewayResource(self._transport)
        self.db = DBResource(self._transport)
        self.memory = MemoryResource(self._transport)
        # documents uses its own resource
        self.documents = _DocumentsResource(self._transport)

    # -- context managers -----------------------------------------------------

    def __enter__(self) -> "SigmaShake":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    async def __aenter__(self) -> "SigmaShake":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()

    def close(self) -> None:
        self._transport.close()

    async def aclose(self) -> None:
        await self._transport.aclose()


class _DocumentsResource:
    """Document mutation and search operations."""

    def __init__(self, transport: _HTTPTransport) -> None:
        self._t = transport

    def create(
        self,
        resource: str,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Any:
        from .models import MutationResponse
        body = {"resource": resource, "action": action, "payload": payload or {}}
        data = self._t.request("POST", "/v1/documents", json=body)
        return MutationResponse.model_validate(data)

    async def async_create(
        self,
        resource: str,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Any:
        from .models import MutationResponse
        body = {"resource": resource, "action": action, "payload": payload or {}}
        data = await self._t.async_request("POST", "/v1/documents", json=body)
        return MutationResponse.model_validate(data)

    def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Any:
        from .models import SearchResponse
        body = {"query": query, "limit": limit, "offset": offset, "filters": filters or {}}
        data = self._t.request("POST", "/v1/documents/search", json=body)
        return SearchResponse.model_validate(data)

    async def async_search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Any:
        from .models import SearchResponse
        body = {"query": query, "limit": limit, "offset": offset, "filters": filters or {}}
        data = await self._t.async_request("POST", "/v1/documents/search", json=body)
        return SearchResponse.model_validate(data)
