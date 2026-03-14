"""SOC / observability operations."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .models import (
    HostTrafficSummary,
    SessionTimeline,
    StoredIncident,
)

if TYPE_CHECKING:
    from .client import _HTTPTransport


class SOCResource:
    """Security Operations Center queries."""

    def __init__(self, transport: _HTTPTransport) -> None:
        self._t = transport

    def list_incidents(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[StoredIncident]:
        params: Dict[str, Any] = {"limit": limit}
        if status:
            params["status"] = status
        if severity:
            params["severity"] = severity
        data = self._t.request("GET", "/v1/soc/incidents", params=params)
        items = data.get("incidents", data) if isinstance(data, dict) else data
        return [StoredIncident.model_validate(i) for i in items]

    async def async_list_incidents(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[StoredIncident]:
        params: Dict[str, Any] = {"limit": limit}
        if status:
            params["status"] = status
        if severity:
            params["severity"] = severity
        data = await self._t.async_request("GET", "/v1/soc/incidents", params=params)
        items = data.get("incidents", data) if isinstance(data, dict) else data
        return [StoredIncident.model_validate(i) for i in items]

    def get_timeline(self, session_id: str) -> SessionTimeline:
        data = self._t.request("GET", f"/v1/soc/sessions/{session_id}/timeline")
        return SessionTimeline.model_validate(data)

    async def async_get_timeline(self, session_id: str) -> SessionTimeline:
        data = await self._t.async_request("GET", f"/v1/soc/sessions/{session_id}/timeline")
        return SessionTimeline.model_validate(data)

    def top_hosts(
        self,
        tenant_id: str,
        limit: int = 10,
    ) -> List[HostTrafficSummary]:
        params = {"tenant_id": tenant_id, "limit": limit}
        data = self._t.request("GET", "/v1/soc/analytics/top-hosts", params=params)
        items = data.get("hosts", data) if isinstance(data, dict) else data
        return [HostTrafficSummary.model_validate(h) for h in items]

    async def async_top_hosts(
        self,
        tenant_id: str,
        limit: int = 10,
    ) -> List[HostTrafficSummary]:
        params = {"tenant_id": tenant_id, "limit": limit}
        data = await self._t.async_request("GET", "/v1/soc/analytics/top-hosts", params=params)
        items = data.get("hosts", data) if isinstance(data, dict) else data
        return [HostTrafficSummary.model_validate(h) for h in items]
