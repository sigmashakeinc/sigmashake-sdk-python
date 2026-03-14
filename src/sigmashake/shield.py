"""Shield -- agent registration and operation scanning."""

from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

from .models import AgentSession, ScanResult

if TYPE_CHECKING:
    from .client import _HTTPTransport


class ShieldResource:
    """Shield agent security operations."""

    def __init__(self, transport: _HTTPTransport) -> None:
        self._t = transport

    def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        session_ttl_secs: int = 3600,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentSession:
        body = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "session_ttl_secs": session_ttl_secs,
            "metadata": metadata or {},
        }
        data = self._t.request("POST", "/v1/shield/register", json=body)
        return AgentSession.model_validate(data)

    async def async_register_agent(
        self,
        agent_id: str,
        agent_type: str,
        session_ttl_secs: int = 3600,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentSession:
        body = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "session_ttl_secs": session_ttl_secs,
            "metadata": metadata or {},
        }
        data = await self._t.async_request("POST", "/v1/shield/register", json=body)
        return AgentSession.model_validate(data)

    def scan(
        self,
        agent_id: str,
        session_id: str,
        operation: Dict[str, Any],
    ) -> ScanResult:
        body = {"agent_id": agent_id, "session_id": session_id, "operation": operation}
        data = self._t.request("POST", "/v1/shield/scan", json=body)
        return ScanResult.model_validate(data)

    async def async_scan(
        self,
        agent_id: str,
        session_id: str,
        operation: Dict[str, Any],
    ) -> ScanResult:
        body = {"agent_id": agent_id, "session_id": session_id, "operation": operation}
        data = await self._t.async_request("POST", "/v1/shield/scan", json=body)
        return ScanResult.model_validate(data)
