"""Pulse — pipeline observability and event ingestion."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import _HTTPTransport


class PulseResource:
    """Pulse pipeline observability operations."""

    def __init__(self, transport: _HTTPTransport) -> None:
        self._t = transport

    # -- events ---------------------------------------------------------------

    def push_event(
        self,
        events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Ingest one or more external events for correlation with pipeline data.

        Args:
            events: List of event dicts. Each event should include at minimum
                ``event_type`` (str) and ``timestamp`` (ISO 8601 str).
                Optional fields: ``source``, ``metadata``, ``phase``.

        Returns:
            Acceptance response with ``accepted`` count and ``run_id``.
        """
        return self._t.request("POST", "/v1/pulse/events", json={"events": events})

    async def async_push_event(
        self,
        events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Async variant of :meth:`push_event`."""
        return await self._t.async_request(
            "POST", "/v1/pulse/events", json={"events": events}
        )

    # -- runs -----------------------------------------------------------------

    def get_runs(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        from_ts: Optional[str] = None,
        to_ts: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List recent pipeline runs.

        Args:
            page: Page number (1-based).
            per_page: Results per page (max 100).
            from_ts: ISO 8601 start timestamp filter.
            to_ts: ISO 8601 end timestamp filter.

        Returns:
            Paginated list with ``items`` (list of run dicts) and ``total``.
        """
        params: Dict[str, Any] = {"page": page, "per_page": per_page}
        if from_ts is not None:
            params["from"] = from_ts
        if to_ts is not None:
            params["to"] = to_ts
        return self._t.request("GET", "/v1/pulse/history", params=params)

    async def async_get_runs(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        from_ts: Optional[str] = None,
        to_ts: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Async variant of :meth:`get_runs`."""
        params: Dict[str, Any] = {"page": page, "per_page": per_page}
        if from_ts is not None:
            params["from"] = from_ts
        if to_ts is not None:
            params["to"] = to_ts
        return await self._t.async_request("GET", "/v1/pulse/history", params=params)

    def get_run(self, run_id: str) -> Dict[str, Any]:
        """Get full detail for a specific pipeline run.

        Args:
            run_id: UUID of the pipeline run.

        Returns:
            Run detail including all phases and spans.
        """
        return self._t.request("GET", f"/v1/pulse/runs/{run_id}")

    async def async_get_run(self, run_id: str) -> Dict[str, Any]:
        """Async variant of :meth:`get_run`."""
        return await self._t.async_request("GET", f"/v1/pulse/runs/{run_id}")

    def trigger_run(
        self,
        trigger_type: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Trigger a new pipeline run.

        Args:
            trigger_type: One of ``"manual"``, ``"scheduled"``, ``"webhook"``.
            config: Optional run configuration overrides.

        Returns:
            The created :class:`PulseRun` dict.
        """
        body: Dict[str, Any] = {"trigger_type": trigger_type}
        if config is not None:
            body["config"] = config
        return self._t.request("POST", "/v1/pulse/trigger", json=body)

    async def async_trigger_run(
        self,
        trigger_type: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Async variant of :meth:`trigger_run`."""
        body: Dict[str, Any] = {"trigger_type": trigger_type}
        if config is not None:
            body["config"] = config
        return await self._t.async_request("POST", "/v1/pulse/trigger", json=body)

    # -- metrics --------------------------------------------------------------

    def get_metrics(
        self,
        *,
        from_ts: Optional[str] = None,
        to_ts: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get aggregated pipeline metrics.

        Args:
            from_ts: ISO 8601 start timestamp.
            to_ts: ISO 8601 end timestamp.

        Returns:
            Metrics dict with build times, test pass rates, deploy frequencies, etc.
        """
        params: Dict[str, Any] = {}
        if from_ts is not None:
            params["from"] = from_ts
        if to_ts is not None:
            params["to"] = to_ts
        return self._t.request("GET", "/v1/pulse/metrics", params=params)

    async def async_get_metrics(
        self,
        *,
        from_ts: Optional[str] = None,
        to_ts: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Async variant of :meth:`get_metrics`."""
        params: Dict[str, Any] = {}
        if from_ts is not None:
            params["from"] = from_ts
        if to_ts is not None:
            params["to"] = to_ts
        return await self._t.async_request("GET", "/v1/pulse/metrics", params=params)

    # -- bottlenecks ----------------------------------------------------------

    def get_bottlenecks(
        self,
        *,
        min_score: Optional[float] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get detected pipeline bottlenecks ranked by severity score.

        Args:
            min_score: Minimum severity score filter (0.0–1.0).
            limit: Maximum number of bottlenecks to return.

        Returns:
            Dict with ``bottlenecks`` list and ``total`` count.
        """
        params: Dict[str, Any] = {}
        if min_score is not None:
            params["min_score"] = min_score
        if limit is not None:
            params["limit"] = limit
        return self._t.request("GET", "/v1/pulse/bottlenecks", params=params)

    async def async_get_bottlenecks(
        self,
        *,
        min_score: Optional[float] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Async variant of :meth:`get_bottlenecks`."""
        params: Dict[str, Any] = {}
        if min_score is not None:
            params["min_score"] = min_score
        if limit is not None:
            params["limit"] = limit
        return await self._t.async_request(
            "GET", "/v1/pulse/bottlenecks", params=params
        )

    # -- status & brief -------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """Get current pipeline status summary."""
        return self._t.request("GET", "/v1/pulse/status")

    async def async_get_status(self) -> Dict[str, Any]:
        """Async variant of :meth:`get_status`."""
        return await self._t.async_request("GET", "/v1/pulse/status")

    def get_ai_brief(self) -> Dict[str, Any]:
        """Get AI-optimized summary of current pipeline state and recommendations."""
        return self._t.request("GET", "/v1/pulse/ai-brief")

    async def async_get_ai_brief(self) -> Dict[str, Any]:
        """Async variant of :meth:`get_ai_brief`."""
        return await self._t.async_request("GET", "/v1/pulse/ai-brief")
