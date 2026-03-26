"""Tests for MemoryResource — store, get, recall, delete."""

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
from sigmashake.models import MemoryEntry


class TestMemorySyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_store(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.put("/api/v1/agents/agent-1/memory/ctx").mock(
            return_value=httpx.Response(
                200,
                json={"key": "ctx", "value": "important data", "tags": ["s1"]},
            )
        )
        entry = sync_client.memory.store("agent-1", key="ctx", value="important data", tags=["s1"])
        assert isinstance(entry, MemoryEntry)
        assert entry.key == "ctx"
        assert entry.value == "important data"
        assert entry.tags == ["s1"]

    def test_store_without_tags(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        import json

        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200, json={"key": "k", "value": "v", "tags": []}
            )

        mock_api.put("/api/v1/agents/agent-1/memory/k").mock(side_effect=capture)
        entry = sync_client.memory.store("agent-1", key="k", value="v")
        assert captured["body"]["tags"] == []
        assert entry.tags == []

    def test_store_sends_correct_body(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        import json

        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200, json={"key": "k", "value": "v", "tags": ["t1", "t2"]}
            )

        mock_api.put("/api/v1/agents/agent-1/memory/k").mock(side_effect=capture)
        sync_client.memory.store("agent-1", key="k", value="v", tags=["t1", "t2"])
        assert captured["body"]["key"] == "k"
        assert captured["body"]["value"] == "v"
        assert captured["body"]["tags"] == ["t1", "t2"]

    def test_get(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/api/v1/agents/agent-1/memory/my-key").mock(
            return_value=httpx.Response(
                200,
                json={"key": "my-key", "value": "stored value", "tags": ["session-1"]},
            )
        )
        entry = sync_client.memory.get("agent-1", "my-key")
        assert entry.key == "my-key"
        assert entry.value == "stored value"

    def test_recall_with_query(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/api/v1/agents/agent-1/memory/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "entries": [
                        {"key": "k1", "value": "v1", "tags": ["tag-a"]},
                        {"key": "k2", "value": "v2", "tags": ["tag-a"]},
                    ]
                },
            )
        )
        entries = sync_client.memory.recall("agent-1", query="tag-a")
        assert len(entries) == 2
        assert all(isinstance(e, MemoryEntry) for e in entries)
        assert entries[0].key == "k1"

    def test_recall_sends_correct_body(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        import json

        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "entries": [
                        {"key": "ctx:1", "value": "v1", "tags": []},
                    ]
                },
            )

        mock_api.post("/api/v1/agents/agent-1/memory/search").mock(side_effect=capture)
        entries = sync_client.memory.recall("agent-1", query="ctx:")
        assert captured["body"]["query"] == "ctx:"
        assert len(entries) == 1

    def test_recall_empty_result(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/api/v1/agents/agent-1/memory/search").mock(
            return_value=httpx.Response(200, json={"entries": []})
        )
        entries = sync_client.memory.recall("agent-1", query="nothing")
        assert entries == []

    def test_delete(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.delete("/api/v1/agents/agent-1/memory/my-key").mock(
            return_value=httpx.Response(200, json={})
        )
        # delete returns None; just verify no exception
        sync_client.memory.delete("agent-1", "my-key")


class TestMemoryErrorHandling:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_401_on_store(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/memory").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )
        with pytest.raises(AuthenticationError):
            sync_client.memory.store(key="k", value="v")

    def test_404_on_get(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/memory/nonexistent").mock(
            return_value=httpx.Response(404, json={"message": "Key not found"})
        )
        with pytest.raises(NotFoundError):
            sync_client.memory.get("nonexistent")

    def test_429_on_store(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/memory").mock(
            return_value=httpx.Response(
                429, json={"message": "Rate limited", "retry_after": 1.5}
            )
        )
        with pytest.raises(RateLimitError) as exc_info:
            sync_client.memory.store(key="k", value="v")
        assert exc_info.value.retry_after == 1.5

    def test_500_on_recall(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/memory/recall").mock(
            return_value=httpx.Response(500, json={"message": "Internal error"})
        )
        with pytest.raises(ServerError):
            sync_client.memory.recall()

    def test_404_on_delete(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.delete("/v1/memory/missing").mock(
            return_value=httpx.Response(404, json={"message": "Key not found"})
        )
        with pytest.raises(NotFoundError):
            sync_client.memory.delete("missing")


class TestMemoryAsyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    @pytest.mark.asyncio
    async def test_async_store(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/memory").mock(
            return_value=httpx.Response(
                200, json={"key": "k", "value": "v", "tags": []}
            )
        )
        entry = await async_client.memory.async_store(key="k", value="v")
        assert entry.key == "k"
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_get(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/memory/k").mock(
            return_value=httpx.Response(
                200, json={"key": "k", "value": "v", "tags": ["t1"]}
            )
        )
        entry = await async_client.memory.async_get("k")
        assert entry.value == "v"
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_recall(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/memory/recall").mock(
            return_value=httpx.Response(
                200,
                json={
                    "entries": [
                        {"key": "k1", "value": "v1", "tags": []},
                    ]
                },
            )
        )
        entries = await async_client.memory.async_recall(tags=["t"])
        assert len(entries) == 1
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_delete(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.delete("/v1/memory/k").mock(
            return_value=httpx.Response(200, json={})
        )
        await async_client.memory.async_delete("k")
        await async_client.aclose()
