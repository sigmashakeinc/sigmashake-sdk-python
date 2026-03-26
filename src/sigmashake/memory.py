"""Agent memory operations."""

from __future__ import annotations

from typing import Any, List, Optional, TYPE_CHECKING

from .models import MemoryEntry

if TYPE_CHECKING:
    from .client import _HTTPTransport


class MemoryResource:
    """Key-value memory store for agents."""

    def __init__(self, transport: _HTTPTransport) -> None:
        self._t = transport

    def store(
        self,
        agent_id: str,
        key: str,
        value: str,
        tags: Optional[List[str]] = None,
    ) -> MemoryEntry:
        body = {"key": key, "value": value, "tags": tags or []}
        data = self._t.request("PUT", f"/api/v1/agents/{agent_id}/memory/{key}", json=body)
        return MemoryEntry.model_validate(data)

    async def async_store(
        self,
        agent_id: str,
        key: str,
        value: str,
        tags: Optional[List[str]] = None,
    ) -> MemoryEntry:
        body = {"key": key, "value": value, "tags": tags or []}
        data = await self._t.async_request("PUT", f"/api/v1/agents/{agent_id}/memory/{key}", json=body)
        return MemoryEntry.model_validate(data)

    def get(self, agent_id: str, key: str) -> MemoryEntry:
        data = self._t.request("GET", f"/api/v1/agents/{agent_id}/memory/{key}")
        return MemoryEntry.model_validate(data)

    async def async_get(self, agent_id: str, key: str) -> MemoryEntry:
        data = await self._t.async_request("GET", f"/api/v1/agents/{agent_id}/memory/{key}")
        return MemoryEntry.model_validate(data)

    def recall(
        self,
        agent_id: str,
        query: str,
    ) -> List[MemoryEntry]:
        body: dict[str, Any] = {"query": query}
        data = self._t.request("POST", f"/api/v1/agents/{agent_id}/memory/search", json=body)
        items = data.get("entries", data) if isinstance(data, dict) else data
        return [MemoryEntry.model_validate(e) for e in items]

    async def async_recall(
        self,
        agent_id: str,
        query: str,
    ) -> List[MemoryEntry]:
        body: dict[str, Any] = {"query": query}
        data = await self._t.async_request("POST", f"/api/v1/agents/{agent_id}/memory/search", json=body)
        items = data.get("entries", data) if isinstance(data, dict) else data
        return [MemoryEntry.model_validate(e) for e in items]

    def delete(self, agent_id: str, key: str) -> None:
        self._t.request("DELETE", f"/api/v1/agents/{agent_id}/memory/{key}")

    async def async_delete(self, agent_id: str, key: str) -> None:
        await self._t.async_request("DELETE", f"/api/v1/agents/{agent_id}/memory/{key}")
