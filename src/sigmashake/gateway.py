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

    def wrap(self, fn, *, agent_id: str = "default", session_id: Optional[str] = None):
        """Wrap a callable so every call is intercepted by the SigmaShake gateway.

        The wrapped function behaves identically to the original — gateway
        interception is transparent and non-fatal (if the gateway is unreachable,
        the function still executes normally).

        Usage (3 commands to first event)::

            import sigmashake
            client = sigmashake.SigmaShake(api_key="sk-...")
            monitored_fn = client.gateway.wrap(my_agent_tool)
        """
        import functools
        import uuid

        sid = session_id or str(uuid.uuid4())

        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            name = getattr(fn, "__name__", "unknown_tool")
            input_data: Dict[str, Any] = {"args": list(args), "kwargs": kwargs}
            try:
                self.intercept_pre(
                    name=name,
                    input=input_data,
                    session_id=sid,
                    agent_id=agent_id,
                )
            except Exception:
                pass  # gateway unreachable — continue anyway
            result = fn(*args, **kwargs)
            try:
                self.intercept_post(
                    name=name,
                    input=input_data,
                    output=result if isinstance(result, (dict, list, str, int, float, bool, type(None))) else str(result),
                    session_id=sid,
                    agent_id=agent_id,
                )
            except Exception:
                pass
            return result

        return wrapped

    def async_wrap(self, fn, *, agent_id: str = "default", session_id: Optional[str] = None):
        """Async version of wrap() for async agent tools."""
        import functools
        import uuid

        sid = session_id or str(uuid.uuid4())

        @functools.wraps(fn)
        async def wrapped(*args, **kwargs):
            name = getattr(fn, "__name__", "unknown_tool")
            input_data: Dict[str, Any] = {"args": list(args), "kwargs": kwargs}
            try:
                await self.async_intercept_pre(
                    name=name,
                    input=input_data,
                    session_id=sid,
                    agent_id=agent_id,
                )
            except Exception:
                pass
            result = await fn(*args, **kwargs)
            try:
                await self.async_intercept_post(
                    name=name,
                    input=input_data,
                    output=result if isinstance(result, (dict, list, str, int, float, bool, type(None))) else str(result),
                    session_id=sid,
                    agent_id=agent_id,
                )
            except Exception:
                pass
            return result

        return wrapped
