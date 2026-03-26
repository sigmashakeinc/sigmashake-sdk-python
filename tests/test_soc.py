"""Tests for SOCResource — incidents, timelines, top hosts."""

from __future__ import annotations

import httpx
import pytest
import respx

from sigmashake import (
    SigmaShake,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
)
from sigmashake.models import HostTrafficSummary, SessionTimeline, StoredIncident


class TestSOCSyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_list_alerts(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/api/v1/soc/alerts").mock(
            return_value=httpx.Response(
                200,
                json={
                    "incidents": [
                        {
                            "id": "inc-1",
                            "severity": "critical",
                            "status": "open",
                            "title": "Breach detected",
                            "created_at": "2026-01-01T00:00:00Z",
                        },
                        {
                            "id": "inc-2",
                            "severity": "high",
                            "status": "open",
                            "title": "Anomaly detected",
                            "created_at": "2026-01-02T00:00:00Z",
                        },
                    ]
                },
            )
        )
        incidents = sync_client.soc.list_alerts()
        assert len(incidents) == 2
        assert all(isinstance(i, StoredIncident) for i in incidents)
        assert incidents[0].severity == "critical"
        assert incidents[1].title == "Anomaly detected"

    def test_list_incidents_deprecated_alias(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/api/v1/soc/alerts").mock(
            return_value=httpx.Response(200, json={"incidents": []})
        )
        incidents = sync_client.soc.list_incidents()
        assert incidents == []

    def test_list_alerts_with_filters(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["params"] = dict(request.url.params)
            return httpx.Response(
                200,
                json={
                    "incidents": [
                        {
                            "id": "inc-1",
                            "severity": "critical",
                            "status": "open",
                            "title": "Breach",
                            "created_at": "2026-01-01T00:00:00Z",
                        }
                    ]
                },
            )

        mock_api.get("/api/v1/soc/alerts").mock(side_effect=capture)
        incidents = sync_client.soc.list_alerts(
            status="open", severity="critical", limit=50
        )
        assert captured["params"]["status"] == "open"
        assert captured["params"]["severity"] == "critical"
        assert captured["params"]["limit"] == "50"
        assert len(incidents) == 1

    def test_list_alerts_empty(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/api/v1/soc/alerts").mock(
            return_value=httpx.Response(200, json={"incidents": []})
        )
        incidents = sync_client.soc.list_alerts()
        assert incidents == []

    def test_get_timeline(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/api/v1/soc/timeline/sess-1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "session_id": "sess-1",
                    "events": [
                        {"type": "tool_call", "ts": 1000},
                        {"type": "tool_result", "ts": 1001},
                    ],
                },
            )
        )
        timeline = sync_client.soc.get_timeline("sess-1")
        assert isinstance(timeline, SessionTimeline)
        assert timeline.session_id == "sess-1"
        assert len(timeline.events) == 2

    def test_top_hosts_raises_not_implemented(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        with pytest.raises(NotImplementedError, match="Not yet implemented"):
            sync_client.soc.top_hosts(tenant_id="t1")


class TestSOCErrorHandling:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_401_on_list_alerts(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/api/v1/soc/alerts").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )
        with pytest.raises(AuthenticationError):
            sync_client.soc.list_alerts()

    def test_404_on_get_timeline(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/api/v1/soc/timeline/nonexistent").mock(
            return_value=httpx.Response(404, json={"message": "Session not found"})
        )
        with pytest.raises(NotFoundError):
            sync_client.soc.get_timeline("nonexistent")

    def test_429_on_list_alerts(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/api/v1/soc/alerts").mock(
            return_value=httpx.Response(
                429, json={"message": "Rate limited", "retry_after": 2.0}
            )
        )
        with pytest.raises(RateLimitError) as exc_info:
            sync_client.soc.list_alerts()
        assert exc_info.value.retry_after == 2.0

    def test_top_hosts_not_implemented(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        with pytest.raises(NotImplementedError):
            sync_client.soc.top_hosts(tenant_id="t1")


class TestSOCAsyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    @pytest.mark.asyncio
    async def test_async_list_incidents(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/soc/incidents").mock(
            return_value=httpx.Response(
                200,
                json={
                    "incidents": [
                        {
                            "id": "inc-1",
                            "severity": "high",
                            "status": "open",
                            "title": "Alert",
                            "created_at": "2026-01-01T00:00:00Z",
                        }
                    ]
                },
            )
        )
        incidents = await async_client.soc.async_list_incidents()
        assert len(incidents) == 1
        assert incidents[0].severity == "high"
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_get_timeline(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/soc/sessions/sess-1/timeline").mock(
            return_value=httpx.Response(
                200,
                json={"session_id": "sess-1", "events": [{"type": "start", "ts": 0}]},
            )
        )
        timeline = await async_client.soc.async_get_timeline("sess-1")
        assert timeline.session_id == "sess-1"
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_top_hosts(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/soc/analytics/top-hosts").mock(
            return_value=httpx.Response(
                200,
                json={
                    "hosts": [
                        {"host": "api.example.com", "request_count": 100},
                    ]
                },
            )
        )
        hosts = await async_client.soc.async_top_hosts(tenant_id="t1")
        assert len(hosts) == 1
        await async_client.aclose()
