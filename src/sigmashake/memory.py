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
        key: str,
        value: str,
        tags: Optional[List[str]] = None,
    ) -> MemoryEntry:
        body = {"key": key, "value": value, "tags": tags or []}
        data = self._t.request("POST", "/v1/memory", json=body)
        return MemoryEntry.model_validate(data)

    async def async_store(
        self,
        key: str,
        value: str,
        tags: Optional[List[str]] = None,
    ) -> MemoryEntry:
        body = {"key": key, "value": value, "tags": tags or []}
        data = await self._t.async_request("POST", "/v1/memory", json=body)
        return MemoryEntry.model_validate(data)

    def get(self, key: str) -> MemoryEntry:
        data = self._t.request("GET", f"/v1/memory/{key}")
        return MemoryEntry.model_validate(data)

    async def async_get(self, key: str) -> MemoryEntry:
        data = await self._t.async_request("GET", f"/v1/memory/{key}")
        return MemoryEntry.model_validate(data)

    def recall(
        self,
        tags: Optional[List[str]] = None,
        prefix: Optional[str] = None,
        limit: int = 100,
    ) -> List[MemoryEntry]:
        body: dict[str, Any] = {"limit": limit}
        if tags:
            body["tags"] = tags
        if prefix:
            body["prefix"] = prefix
        data = self._t.request("POST", "/v1/memory/recall", json=body)
        items = data.get("entries", data) if isinstance(data, dict) else data
        return [MemoryEntry.model_validate(e) for e in items]

    async def async_recall(
        self,
        tags: Optional[List[str]] = None,
        prefix: Optional[str] = None,
        limit: int = 100,
    ) -> List[MemoryEntry]:
        body: dict[str, Any] = {"limit": limit}
        if tags:
            body["tags"] = tags
        if prefix:
            body["prefix"] = prefix
        data = await self._t.async_request("POST", "/v1/memory/recall", json=body)
        items = data.get("entries", data) if isinstance(data, dict) else data
        return [MemoryEntry.model_validate(e) for e in items]

    def delete(self, key: str) -> None:
        self._t.request("DELETE", f"/v1/memory/{key}")

    async def async_delete(self, key: str) -> None:
        await self._t.async_request("DELETE", f"/v1/memory/{key}")
