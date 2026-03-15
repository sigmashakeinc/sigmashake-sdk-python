"""Fleet protocol operations — monitoring and management of deployed AI agents."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .models import (
    FleetAgentDetail,
    FleetAgentListResponse,
    FleetBroadcastResponse,
    FleetCommand,
    FleetCommandHistory,
    FleetCommandResponse,
    FleetConfig,
    FleetMetricsResponse,
    FleetStatus,
)

if TYPE_CHECKING:
    from .client import _HTTPTransport


class FleetResource:
    """Agent fleet monitoring and management."""

    def __init__(self, transport: _HTTPTransport) -> None:
        self._t = transport

    # -- Fleet status ---------------------------------------------------------

    def status(self) -> FleetStatus:
        data = self._t.request("GET", "/v1/fleet/status")
        return FleetStatus.model_validate(data)

    async def async_status(self) -> FleetStatus:
        data = await self._t.async_request("GET", "/v1/fleet/status")
        return FleetStatus.model_validate(data)

    # -- Agent list -----------------------------------------------------------

    def list_agents(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> FleetAgentListResponse:
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        data = self._t.request("GET", "/v1/fleet/agents", params=params)
        return FleetAgentListResponse.model_validate(data)

    async def async_list_agents(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> FleetAgentListResponse:
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        data = await self._t.async_request("GET", "/v1/fleet/agents", params=params)
        return FleetAgentListResponse.model_validate(data)

    # -- Agent detail ---------------------------------------------------------

    def get_agent(self, agent_id: str) -> FleetAgentDetail:
        data = self._t.request("GET", f"/v1/fleet/agents/{agent_id}")
        return FleetAgentDetail.model_validate(data)

    async def async_get_agent(self, agent_id: str) -> FleetAgentDetail:
        data = await self._t.async_request("GET", f"/v1/fleet/agents/{agent_id}")
        return FleetAgentDetail.model_validate(data)

    # -- Send command ---------------------------------------------------------

    def send_command(
        self,
        agent_id: str,
        command: FleetCommand,
    ) -> FleetCommandResponse:
        data = self._t.request(
            "POST",
            f"/v1/fleet/agents/{agent_id}/command",
            json=command.model_dump(),
        )
        return FleetCommandResponse.model_validate(data)

    async def async_send_command(
        self,
        agent_id: str,
        command: FleetCommand,
    ) -> FleetCommandResponse:
        data = await self._t.async_request(
            "POST",
            f"/v1/fleet/agents/{agent_id}/command",
            json=command.model_dump(),
        )
        return FleetCommandResponse.model_validate(data)

    # -- Broadcast command ----------------------------------------------------

    def broadcast(self, command: FleetCommand) -> FleetBroadcastResponse:
        data = self._t.request(
            "POST",
            "/v1/fleet/broadcast",
            json=command.model_dump(),
        )
        return FleetBroadcastResponse.model_validate(data)

    async def async_broadcast(self, command: FleetCommand) -> FleetBroadcastResponse:
        data = await self._t.async_request(
            "POST",
            "/v1/fleet/broadcast",
            json=command.model_dump(),
        )
        return FleetBroadcastResponse.model_validate(data)

    # -- Agent metrics --------------------------------------------------------

    def get_metrics(
        self,
        agent_id: str,
        *,
        period: Optional[str] = None,
    ) -> FleetMetricsResponse:
        params: Dict[str, Any] = {}
        if period:
            params["period"] = period
        data = self._t.request(
            "GET", f"/v1/fleet/agents/{agent_id}/metrics", params=params or None
        )
        return FleetMetricsResponse.model_validate(data)

    async def async_get_metrics(
        self,
        agent_id: str,
        *,
        period: Optional[str] = None,
    ) -> FleetMetricsResponse:
        params: Dict[str, Any] = {}
        if period:
            params["period"] = period
        data = await self._t.async_request(
            "GET", f"/v1/fleet/agents/{agent_id}/metrics", params=params or None
        )
        return FleetMetricsResponse.model_validate(data)

    # -- Command history ------------------------------------------------------

    def get_command_history(
        self,
        agent_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> FleetCommandHistory:
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        data = self._t.request(
            "GET", f"/v1/fleet/agents/{agent_id}/commands", params=params
        )
        return FleetCommandHistory.model_validate(data)

    async def async_get_command_history(
        self,
        agent_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> FleetCommandHistory:
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        data = await self._t.async_request(
            "GET", f"/v1/fleet/agents/{agent_id}/commands", params=params
        )
        return FleetCommandHistory.model_validate(data)

    # -- Fleet config ---------------------------------------------------------

    def get_config(self) -> FleetConfig:
        data = self._t.request("GET", "/v1/fleet/config")
        return FleetConfig.model_validate(data)

    async def async_get_config(self) -> FleetConfig:
        data = await self._t.async_request("GET", "/v1/fleet/config")
        return FleetConfig.model_validate(data)

    def update_config(self, config: FleetConfig) -> FleetConfig:
        data = self._t.request(
            "PUT", "/v1/fleet/config", json=config.model_dump()
        )
        return FleetConfig.model_validate(data)

    async def async_update_config(self, config: FleetConfig) -> FleetConfig:
        data = await self._t.async_request(
            "PUT", "/v1/fleet/config", json=config.model_dump()
        )
        return FleetConfig.model_validate(data)
