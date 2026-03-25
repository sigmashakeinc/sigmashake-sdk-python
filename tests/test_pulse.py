"""Tests for the Pulse resource — event ingestion, runs, metrics, bottlenecks."""

from __future__ import annotations

import httpx
import pytest
import respx

from sigmashake import SigmaShake, PulseResource


class TestPulseResource:
    def test_pulse_resource_available_on_client(self, sync_client: SigmaShake) -> None:
        assert hasattr(sync_client, "pulse")
        assert isinstance(sync_client.pulse, PulseResource)

    def test_push_event_posts_to_events_endpoint(
        self, sync_client: SigmaShake, mock_api: respx.MockRouter
    ) -> None:
        events = [{"event_type": "build_start", "timestamp": "2026-03-25T10:00:00Z"}]
        mock_api.post("/v1/pulse/events").mock(
            return_value=httpx.Response(202, json={"accepted": 1, "run_id": "run-abc"})
        )
        result = sync_client.pulse.push_event(events)
        assert result["accepted"] == 1
        assert result["run_id"] == "run-abc"

    def test_push_event_sends_events_in_body(
        self, sync_client: SigmaShake, mock_api: respx.MockRouter
    ) -> None:
        events = [
            {"event_type": "test_pass", "timestamp": "2026-03-25T10:01:00Z"},
            {"event_type": "deploy_start", "timestamp": "2026-03-25T10:02:00Z"},
        ]
        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            import json
            captured["body"] = json.loads(request.content)
            return httpx.Response(202, json={"accepted": 2, "run_id": None})

        mock_api.post("/v1/pulse/events").mock(side_effect=capture)
        sync_client.pulse.push_event(events)
        assert "events" in captured["body"]
        assert len(captured["body"]["events"]) == 2

    def test_get_runs_calls_history_endpoint(
        self, sync_client: SigmaShake, mock_api: respx.MockRouter
    ) -> None:
        mock_api.get("/v1/pulse/history").mock(
            return_value=httpx.Response(
                200, json={"items": [], "total": 0, "page": 1, "per_page": 20}
            )
        )
        result = sync_client.pulse.get_runs()
        assert result["total"] == 0
        assert "items" in result

    def test_get_runs_passes_pagination_params(
        self, sync_client: SigmaShake, mock_api: respx.MockRouter
    ) -> None:
        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["params"] = dict(request.url.params)
            return httpx.Response(
                200, json={"items": [], "total": 0, "page": 2, "per_page": 5}
            )

        mock_api.get("/v1/pulse/history").mock(side_effect=capture)
        sync_client.pulse.get_runs(page=2, per_page=5, from_ts="2026-03-01T00:00:00Z")
        assert captured["params"]["page"] == "2"
        assert captured["params"]["per_page"] == "5"
        assert "from" in captured["params"]

    def test_get_run_calls_correct_url(
        self, sync_client: SigmaShake, mock_api: respx.MockRouter
    ) -> None:
        run_id = "d4c3b2a1-0000-0000-0000-111111111111"
        mock_api.get(f"/v1/pulse/runs/{run_id}").mock(
            return_value=httpx.Response(
                200, json={"id": run_id, "status": "success", "phases": []}
            )
        )
        result = sync_client.pulse.get_run(run_id)
        assert result["id"] == run_id
        assert result["status"] == "success"

    def test_trigger_run_posts_trigger_type(
        self, sync_client: SigmaShake, mock_api: respx.MockRouter
    ) -> None:
        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            import json
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                202,
                json={"id": "run-001", "status": "pending", "trigger_type": "manual"},
            )

        mock_api.post("/v1/pulse/trigger").mock(side_effect=capture)
        result = sync_client.pulse.trigger_run("manual")
        assert captured["body"]["trigger_type"] == "manual"
        assert result["status"] == "pending"

    def test_get_metrics_calls_metrics_endpoint(
        self, sync_client: SigmaShake, mock_api: respx.MockRouter
    ) -> None:
        mock_api.get("/v1/pulse/metrics").mock(
            return_value=httpx.Response(
                200,
                json={
                    "build_time_p50_ms": 12000,
                    "test_pass_rate": 0.98,
                    "deploy_frequency_per_day": 3.5,
                },
            )
        )
        result = sync_client.pulse.get_metrics()
        assert result["test_pass_rate"] == 0.98
        assert "build_time_p50_ms" in result

    def test_get_metrics_passes_time_range(
        self, sync_client: SigmaShake, mock_api: respx.MockRouter
    ) -> None:
        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["params"] = dict(request.url.params)
            return httpx.Response(200, json={"build_time_p50_ms": 0})

        mock_api.get("/v1/pulse/metrics").mock(side_effect=capture)
        sync_client.pulse.get_metrics(
            from_ts="2026-03-01T00:00:00Z", to_ts="2026-03-25T00:00:00Z"
        )
        assert "from" in captured["params"]
        assert "to" in captured["params"]

    def test_get_bottlenecks_returns_list(
        self, sync_client: SigmaShake, mock_api: respx.MockRouter
    ) -> None:
        mock_api.get("/v1/pulse/bottlenecks").mock(
            return_value=httpx.Response(
                200,
                json={
                    "bottlenecks": [
                        {"phase": "build", "score": 0.87, "description": "slow build"}
                    ],
                    "total": 1,
                },
            )
        )
        result = sync_client.pulse.get_bottlenecks()
        assert result["total"] == 1
        assert result["bottlenecks"][0]["phase"] == "build"

    def test_get_bottlenecks_passes_filters(
        self, sync_client: SigmaShake, mock_api: respx.MockRouter
    ) -> None:
        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["params"] = dict(request.url.params)
            return httpx.Response(200, json={"bottlenecks": [], "total": 0})

        mock_api.get("/v1/pulse/bottlenecks").mock(side_effect=capture)
        sync_client.pulse.get_bottlenecks(min_score=0.5, limit=10)
        assert captured["params"]["min_score"] == "0.5"
        assert captured["params"]["limit"] == "10"

    def test_get_status_returns_status(
        self, sync_client: SigmaShake, mock_api: respx.MockRouter
    ) -> None:
        mock_api.get("/v1/pulse/status").mock(
            return_value=httpx.Response(
                200, json={"healthy": True, "active_runs": 2, "queue_depth": 0}
            )
        )
        result = sync_client.pulse.get_status()
        assert result["healthy"] is True
        assert "active_runs" in result

    def test_get_ai_brief_returns_brief(
        self, sync_client: SigmaShake, mock_api: respx.MockRouter
    ) -> None:
        mock_api.get("/v1/pulse/ai-brief").mock(
            return_value=httpx.Response(
                200,
                json={
                    "summary": "Pipeline healthy. Build times up 12%.",
                    "recommendations": [],
                },
            )
        )
        result = sync_client.pulse.get_ai_brief()
        assert "summary" in result
        assert isinstance(result["recommendations"], list)


@pytest.mark.asyncio
class TestPulseResourceAsync:
    async def test_async_push_event(
        self, async_client: SigmaShake, mock_api: respx.MockRouter
    ) -> None:
        mock_api.post("/v1/pulse/events").mock(
            return_value=httpx.Response(202, json={"accepted": 1, "run_id": None})
        )
        result = await async_client.pulse.async_push_event(
            [{"event_type": "deploy_end", "timestamp": "2026-03-25T11:00:00Z"}]
        )
        assert result["accepted"] == 1

    async def test_async_get_runs(
        self, async_client: SigmaShake, mock_api: respx.MockRouter
    ) -> None:
        mock_api.get("/v1/pulse/history").mock(
            return_value=httpx.Response(
                200, json={"items": [{"id": "run-1"}], "total": 1, "page": 1, "per_page": 20}
            )
        )
        result = await async_client.pulse.async_get_runs()
        assert result["total"] == 1
        assert len(result["items"]) == 1

    async def test_async_get_metrics(
        self, async_client: SigmaShake, mock_api: respx.MockRouter
    ) -> None:
        mock_api.get("/v1/pulse/metrics").mock(
            return_value=httpx.Response(200, json={"test_pass_rate": 1.0})
        )
        result = await async_client.pulse.async_get_metrics()
        assert result["test_pass_rate"] == 1.0

    async def test_async_get_bottlenecks(
        self, async_client: SigmaShake, mock_api: respx.MockRouter
    ) -> None:
        mock_api.get("/v1/pulse/bottlenecks").mock(
            return_value=httpx.Response(200, json={"bottlenecks": [], "total": 0})
        )
        result = await async_client.pulse.async_get_bottlenecks()
        assert result["total"] == 0
        assert isinstance(result["bottlenecks"], list)
