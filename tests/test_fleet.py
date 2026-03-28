"""Tests for fleet resource methods and fleet model serialization."""

from __future__ import annotations

import httpx
import pytest
import respx

from sigmashake import SigmaShake
from sigmashake.models import (
    AgentStatus,
    CommandType,
    FleetAgent,
    FleetAgentDetail,
    FleetAgentListResponse,
    FleetAlertThresholds,
    FleetBroadcastResponse,
    FleetCommand,
    FleetCommandAuditEntry,
    FleetCommandHistory,
    FleetCommandResponse,
    FleetConfig,
    FleetEvent,
    FleetMetricPoint,
    FleetMetricsResponse,
    FleetStatus,
)


class TestFleetModels:
    def test_agent_status_values(self) -> None:
        assert AgentStatus.active.value == "active"
        assert AgentStatus.offline.value == "offline"
        assert AgentStatus.busy.value == "busy"

    def test_command_type_values(self) -> None:
        assert CommandType.restart.value == "restart"
        assert CommandType.pause.value == "pause"
        assert CommandType.update_config.value == "update_config"

    def test_fleet_status_defaults(self) -> None:
        status = FleetStatus()
        assert status.total == 0
        assert status.online == 0

    def test_fleet_status_deserialize(self) -> None:
        status = FleetStatus.model_validate(
            {"total": 847, "online": 812, "degraded": 23, "offline": 12}
        )
        assert status.total == 847
        assert status.degraded == 23

    def test_fleet_agent_deserialize(self) -> None:
        agent = FleetAgent.model_validate({
            "agent_id": "agent-a1",
            "status": "active",
            "last_seen": "2026-03-15T10:00:00Z",
            "version": "2.1.0",
            "cpu_pct": 23.5,
        })
        assert agent.agent_id == "agent-a1"
        assert agent.status == AgentStatus.active
        assert agent.cpu_pct == 23.5

    def test_fleet_agent_detail_deserialize(self) -> None:
        detail = FleetAgentDetail.model_validate({
            "agent_id": "agent-b2",
            "status": "busy",
            "version": "2.1.0",
            "cpu_pct": 87.0,
            "memory_mb": 512.0,
            "llm_tokens_in": 1000,
            "llm_tokens_out": 500,
            "llm_cost_usd": 1.20,
            "capabilities": ["tool_use", "code_gen"],
            "metadata": {"region": "us-east-1"},
        })
        assert detail.status == AgentStatus.busy
        assert detail.capabilities == ["tool_use", "code_gen"]
        assert detail.llm_tokens_in == 1000

    def test_fleet_agent_list_response(self) -> None:
        resp = FleetAgentListResponse.model_validate({
            "agents": [
                {"agent_id": "a1", "status": "active"},
                {"agent_id": "a2", "status": "offline"},
            ],
            "total": 2,
            "limit": 100,
            "offset": 0,
        })
        assert len(resp.agents) == 2
        assert resp.total == 2

    def test_fleet_command_serialize(self) -> None:
        cmd = FleetCommand(command_type=CommandType.restart, payload={"reason": "update"})
        data = cmd.model_dump()
        assert data["command_type"] == "restart"
        assert data["payload"]["reason"] == "update"

    def test_fleet_command_response(self) -> None:
        resp = FleetCommandResponse.model_validate({
            "command_id": "cmd-1",
            "agent_id": "a1",
            "command_type": "pause",
            "status": "pending",
            "issued_at": "2026-03-15T10:00:00Z",
        })
        assert resp.command_type == CommandType.pause

    def test_fleet_broadcast_response(self) -> None:
        resp = FleetBroadcastResponse.model_validate({
            "command_id": "cmd-2",
            "command_type": "update_config",
            "target_count": 847,
        })
        assert resp.target_count == 847

    def test_fleet_metric_point(self) -> None:
        point = FleetMetricPoint.model_validate({
            "timestamp": "2026-03-15T10:00:00Z",
            "cpu_pct": 45.0,
            "memory_mb": 256.0,
            "llm_tokens_in": 100,
            "llm_tokens_out": 50,
            "llm_cost_usd": 0.05,
        })
        assert point.cpu_pct == 45.0

    def test_fleet_metrics_response(self) -> None:
        resp = FleetMetricsResponse.model_validate({
            "agent_id": "a1",
            "metrics": [
                {"timestamp": "2026-03-15T10:00:00Z", "cpu_pct": 10.0},
                {"timestamp": "2026-03-15T10:01:00Z", "cpu_pct": 20.0},
            ],
        })
        assert len(resp.metrics) == 2

    def test_fleet_command_audit_entry(self) -> None:
        entry = FleetCommandAuditEntry.model_validate({
            "id": "cmd-1",
            "command_type": "restart",
            "payload": {},
            "issued_at": "2026-03-15T10:00:00Z",
            "acked": True,
            "ack_message": "restarted successfully",
        })
        assert entry.acked is True

    def test_fleet_command_history(self) -> None:
        history = FleetCommandHistory.model_validate({
            "agent_id": "a1",
            "commands": [
                {
                    "id": "cmd-1",
                    "command_type": "pause",
                    "payload": {},
                    "issued_at": "2026-03-15T10:00:00Z",
                }
            ],
            "total": 1,
        })
        assert history.total == 1

    def test_fleet_config_defaults(self) -> None:
        config = FleetConfig()
        assert config.heartbeat_interval_secs == 60
        assert config.metrics_interval_secs == 60
        assert config.alert_thresholds.missed_heartbeats == 3

    def test_fleet_config_roundtrip(self) -> None:
        config = FleetConfig(
            heartbeat_interval_secs=15,
            max_agents=5000,
            alert_thresholds=FleetAlertThresholds(missed_heartbeats=5, error_rate_pct=10.0),
            auto_scale_enabled=True,
        )
        data = config.model_dump()
        restored = FleetConfig.model_validate(data)
        assert restored.heartbeat_interval_secs == 15
        assert restored.alert_thresholds.error_rate_pct == 10.0
        assert restored.auto_scale_enabled is True

    def test_fleet_event(self) -> None:
        event = FleetEvent.model_validate({
            "event_type": "agent_connected",
            "agent_id": "a1",
            "timestamp": "2026-03-15T10:00:00Z",
            "data": {"shard": "fleet-t1-0"},
        })
        assert event.event_type == "agent_connected"


class TestFleetSyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_fleet_status(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/fleet/status").mock(
            return_value=httpx.Response(
                200, json={"total": 100, "online": 90, "degraded": 5, "offline": 5}
            )
        )
        status = sync_client.fleet.status()
        assert status.total == 100
        assert status.online == 90

    def test_fleet_list_agents(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/fleet/agents").mock(
            return_value=httpx.Response(
                200,
                json={
                    "agents": [
                        {"agent_id": "a1", "status": "active"},
                        {"agent_id": "a2", "status": "idle"},
                    ],
                    "total": 2,
                    "limit": 100,
                    "offset": 0,
                },
            )
        )
        resp = sync_client.fleet.list_agents()
        assert len(resp.agents) == 2
        assert resp.agents[0].status == AgentStatus.active

    def test_fleet_list_agents_with_filter(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/fleet/agents").mock(
            return_value=httpx.Response(
                200,
                json={"agents": [{"agent_id": "a1", "status": "offline"}], "total": 1},
            )
        )
        resp = sync_client.fleet.list_agents(status="offline", limit=10)
        assert resp.total == 1

    def test_fleet_get_agent(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/fleet/agents/agent-x1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "agent_id": "agent-x1",
                    "status": "busy",
                    "version": "2.1.0",
                    "capabilities": ["tool_use"],
                },
            )
        )
        detail = sync_client.fleet.get_agent("agent-x1")
        assert detail.agent_id == "agent-x1"
        assert detail.status == AgentStatus.busy

    def test_fleet_send_command(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/fleet/agents/a1/command").mock(
            return_value=httpx.Response(
                200,
                json={
                    "command_id": "cmd-1",
                    "agent_id": "a1",
                    "command_type": "restart",
                    "status": "pending",
                    "issued_at": "2026-03-15T10:00:00Z",
                },
            )
        )
        cmd = FleetCommand(command_type=CommandType.restart)
        resp = sync_client.fleet.send_command("a1", cmd)
        assert resp.command_id == "cmd-1"
        assert resp.command_type == CommandType.restart

    def test_fleet_broadcast(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/fleet/broadcast").mock(
            return_value=httpx.Response(
                200,
                json={
                    "command_id": "cmd-2",
                    "command_type": "update_config",
                    "target_count": 100,
                },
            )
        )
        cmd = FleetCommand(
            command_type=CommandType.update_config,
            payload={"heartbeat_interval_secs": 15},
        )
        resp = sync_client.fleet.broadcast(cmd)
        assert resp.target_count == 100

    def test_fleet_get_metrics(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/fleet/agents/a1/metrics").mock(
            return_value=httpx.Response(
                200,
                json={
                    "agent_id": "a1",
                    "metrics": [
                        {"timestamp": "2026-03-15T10:00:00Z", "cpu_pct": 30.0},
                    ],
                },
            )
        )
        resp = sync_client.fleet.get_metrics("a1", period="1h")
        assert resp.agent_id == "a1"
        assert len(resp.metrics) == 1

    def test_fleet_get_command_history(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/fleet/agents/a1/commands").mock(
            return_value=httpx.Response(
                200,
                json={
                    "agent_id": "a1",
                    "commands": [
                        {
                            "id": "cmd-1",
                            "command_type": "restart",
                            "payload": {},
                            "issued_at": "2026-03-15T10:00:00Z",
                            "acked": True,
                            "ack_message": "ok",
                        }
                    ],
                    "total": 1,
                },
            )
        )
        history = sync_client.fleet.get_command_history("a1")
        assert history.total == 1
        assert history.commands[0].acked is True

    def test_fleet_get_config(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/fleet/config").mock(
            return_value=httpx.Response(
                200,
                json={
                    "heartbeat_interval_secs": 60,
                    "metrics_interval_secs": 60,
                    "max_agents": 1000,
                    "alert_thresholds": {"missed_heartbeats": 3, "error_rate_pct": 5.0},
                    "auto_scale_enabled": False,
                },
            )
        )
        config = sync_client.fleet.get_config()
        assert config.heartbeat_interval_secs == 60
        assert config.alert_thresholds.missed_heartbeats == 3

    def test_fleet_update_config(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.put("/v1/fleet/config").mock(
            return_value=httpx.Response(
                200,
                json={
                    "heartbeat_interval_secs": 15,
                    "metrics_interval_secs": 30,
                    "max_agents": 5000,
                    "alert_thresholds": {"missed_heartbeats": 5, "error_rate_pct": 10.0},
                    "auto_scale_enabled": True,
                },
            )
        )
        new_config = FleetConfig(
            heartbeat_interval_secs=15,
            metrics_interval_secs=30,
            max_agents=5000,
            alert_thresholds=FleetAlertThresholds(missed_heartbeats=5, error_rate_pct=10.0),
            auto_scale_enabled=True,
        )
        config = sync_client.fleet.update_config(new_config)
        assert config.heartbeat_interval_secs == 15
        assert config.auto_scale_enabled is True


class TestFleetAsyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    @pytest.mark.asyncio
    async def test_fleet_status_async(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/fleet/status").mock(
            return_value=httpx.Response(
                200, json={"total": 50, "online": 48, "degraded": 1, "offline": 1}
            )
        )
        status = await async_client.fleet.async_status()
        assert status.total == 50
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_fleet_list_agents_async(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/fleet/agents").mock(
            return_value=httpx.Response(
                200,
                json={
                    "agents": [{"agent_id": "a1", "status": "active"}],
                    "total": 1,
                },
            )
        )
        resp = await async_client.fleet.async_list_agents()
        assert len(resp.agents) == 1
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_fleet_send_command_async(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/fleet/agents/a1/command").mock(
            return_value=httpx.Response(
                200,
                json={
                    "command_id": "cmd-1",
                    "agent_id": "a1",
                    "command_type": "pause",
                    "status": "pending",
                },
            )
        )
        cmd = FleetCommand(command_type=CommandType.pause)
        resp = await async_client.fleet.async_send_command("a1", cmd)
        assert resp.command_type == CommandType.pause
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_fleet_get_config_async(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/fleet/config").mock(
            return_value=httpx.Response(
                200,
                json={
                    "heartbeat_interval_secs": 60,
                    "metrics_interval_secs": 60,
                    "max_agents": 1000,
                    "alert_thresholds": {"missed_heartbeats": 3, "error_rate_pct": 5.0},
                    "auto_scale_enabled": False,
                },
            )
        )
        config = await async_client.fleet.async_get_config()
        assert config.heartbeat_interval_secs == 60
        await async_client.aclose()
