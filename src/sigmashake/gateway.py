"""Gateway intercept operations."""

from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

from .models import InterceptResult

if TYPE_CHECKING:
    from .client import _HTTPTransport


class GatewayResource:
    """Gateway pre/post intercept for tool calls."""

    def __init__(self, transport: _HTTPTransport) -> None:
        self._t = transport

    def intercept_pre(
        self,
        name: str,
        input: Dict[str, Any],
        session_id: str,
        agent_id: str,
    ) -> InterceptResult:
        body = {
            "name": name,
            "input": input,
            "session_id": session_id,
            "agent_id": agent_id,
        }
        data = self._t.request("POST", "/v1/gateway/intercept/pre", json=body)
        return InterceptResult.model_validate(data)

    async def async_intercept_pre(
        self,
        name: str,
        input: Dict[str, Any],
        session_id: str,
        agent_id: str,
    ) -> InterceptResult:
        body = {
            "name": name,
            "input": input,
            "session_id": session_id,
            "agent_id": agent_id,
        }
        data = await self._t.async_request("POST", "/v1/gateway/intercept/pre", json=body)
        return InterceptResult.model_validate(data)

    def intercept_post(
        self,
        name: str,
        input: Dict[str, Any],
        output: Any,
        session_id: str,
        agent_id: str,
    ) -> InterceptResult:
        body = {
            "name": name,
            "input": input,
            "output": output,
            "session_id": session_id,
            "agent_id": agent_id,
        }
        data = self._t.request("POST", "/v1/gateway/intercept/post", json=body)
        return InterceptResult.model_validate(data)

    async def async_intercept_post(
        self,
        name: str,
        input: Dict[str, Any],
        output: Any,
        session_id: str,
        agent_id: str,
    ) -> InterceptResult:
        body = {
            "name": name,
            "input": input,
            "output": output,
            "session_id": session_id,
            "agent_id": agent_id,
        }
        data = await self._t.async_request("POST", "/v1/gateway/intercept/post", json=body)
        return InterceptResult.model_validate(data)
