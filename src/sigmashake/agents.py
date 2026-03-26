"""Agent lifecycle operations."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import _HTTPTransport


class AgentsResource:
    """Agent registration and management."""

    def __init__(self, transport: _HTTPTransport) -> None:
        self._t = transport

    def register(
        self,
        agent_id: str,
        agent_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        body = {"agent_id": agent_id, "agent_type": agent_type, "metadata": metadata or {}}
        return self._t.request("POST", "/v1/agents", json=body)

    async def async_register(
        self,
        agent_id: str,
        agent_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        body = {"agent_id": agent_id, "agent_type": agent_type, "metadata": metadata or {}}
        return await self._t.async_request("POST", "/v1/agents", json=body)

    def get(self, agent_id: str) -> Dict[str, Any]:
        return self._t.request("GET", f"/v1/agents/{agent_id}")

    async def async_get(self, agent_id: str) -> Dict[str, Any]:
        return await self._t.async_request("GET", f"/v1/agents/{agent_id}")

    def update(self, agent_id: str, **kwargs: Any) -> Dict[str, Any]:
        return self._t.request("PATCH", f"/v1/agents/{agent_id}", json=kwargs)

    async def async_update(self, agent_id: str, **kwargs: Any) -> Dict[str, Any]:
        return await self._t.async_request("PATCH", f"/v1/agents/{agent_id}", json=kwargs)

    def list(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        data = self._t.request("GET", "/v1/agents", params={"limit": limit, "offset": offset})
        return data.get("agents", []) if isinstance(data, dict) else data

    async def async_list(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        data = await self._t.async_request("GET", "/v1/agents", params={"limit": limit, "offset": offset})
        return data.get("agents", []) if isinstance(data, dict) else data
