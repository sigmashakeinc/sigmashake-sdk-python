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

    # -- Triggers -------------------------------------------------------------

    def create_trigger(self, agent_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._t.request("POST", f"/v1/agents/{agent_id}/triggers", json=body)

    def list_triggers(self, agent_id: str) -> List[Dict[str, Any]]:
        data = self._t.request("GET", f"/v1/agents/{agent_id}/triggers")
        return data.get("triggers", []) if isinstance(data, dict) else data

    def execute_trigger(self, agent_id: str, trigger_id: str) -> Dict[str, Any]:
        return self._t.request("POST", f"/v1/agents/{agent_id}/triggers/{trigger_id}/execute")

    def get_trigger_status(self, agent_id: str, trigger_id: str) -> Dict[str, Any]:
        return self._t.request("GET", f"/v1/agents/{agent_id}/triggers/{trigger_id}/status")

    def delete_trigger(self, agent_id: str, trigger_id: str) -> Dict[str, Any]:
        return self._t.request("DELETE", f"/v1/agents/{agent_id}/triggers/{trigger_id}")

    # -- Context --------------------------------------------------------------

    def store_context(self, agent_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._t.request("PUT", f"/v1/agents/{agent_id}/context", json=body)

    def get_context(self, agent_id: str) -> Dict[str, Any]:
        return self._t.request("GET", f"/v1/agents/{agent_id}/context")

    def delete_context(self, agent_id: str) -> Dict[str, Any]:
        return self._t.request("DELETE", f"/v1/agents/{agent_id}/context")

    # -- Tools ----------------------------------------------------------------

    def register_tools(self, agent_id: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self._t.request("POST", f"/v1/agents/{agent_id}/tools", json={"tools": tools})

    def list_tools(self, agent_id: str) -> List[Dict[str, Any]]:
        data = self._t.request("GET", f"/v1/agents/{agent_id}/tools")
        return data.get("tools", []) if isinstance(data, dict) else data

    def unregister_tool(self, agent_id: str, tool_name: str) -> Dict[str, Any]:
        return self._t.request("DELETE", f"/v1/agents/{agent_id}/tools/{tool_name}")

    # -- Usage ----------------------------------------------------------------

    def get_usage(
        self,
        agent_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if from_date is not None:
            params["from_date"] = from_date
        if to_date is not None:
            params["to_date"] = to_date
        return self._t.request("GET", f"/v1/agents/{agent_id}/usage", params=params or None)
