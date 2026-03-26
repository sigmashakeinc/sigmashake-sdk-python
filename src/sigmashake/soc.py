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

    def list_alerts(
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
        data = self._t.request("GET", "/api/v1/soc/alerts", params=params)
        items = data.get("incidents", data) if isinstance(data, dict) else data
        return [StoredIncident.model_validate(i) for i in items]

    async def async_list_alerts(
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
        data = await self._t.async_request("GET", "/api/v1/soc/alerts", params=params)
        items = data.get("incidents", data) if isinstance(data, dict) else data
        return [StoredIncident.model_validate(i) for i in items]

    def list_incidents(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[StoredIncident]:
        """Deprecated: use list_alerts() instead."""
        return self.list_alerts(status=status, severity=severity, limit=limit)

    async def async_list_incidents(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[StoredIncident]:
        """Deprecated: use async_list_alerts() instead."""
        return await self.async_list_alerts(status=status, severity=severity, limit=limit)

    def get_timeline(self, session_id: str) -> SessionTimeline:
        data = self._t.request("GET", f"/api/v1/soc/timeline/{session_id}")
        return SessionTimeline.model_validate(data)

    async def async_get_timeline(self, session_id: str) -> SessionTimeline:
        data = await self._t.async_request("GET", f"/api/v1/soc/timeline/{session_id}")
        return SessionTimeline.model_validate(data)

    def top_hosts(
        self,
        tenant_id: str,
        limit: int = 10,
    ) -> List[HostTrafficSummary]:
        raise NotImplementedError("Not yet implemented")

    async def async_top_hosts(
        self,
        tenant_id: str,
        limit: int = 10,
    ) -> List[HostTrafficSummary]:
        raise NotImplementedError("Not yet implemented")
