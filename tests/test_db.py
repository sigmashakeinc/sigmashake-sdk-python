"""Tests for DBResource — tables, queries, vector search, scroll, cluster."""

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
    ValidationError,
)
from sigmashake.models import ClusterStatusResponse, QueryResponse, ScrollQueryResponse


class TestDBSyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_create_table(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/db/tables").mock(
            return_value=httpx.Response(
                200,
                json={"table_name": "events", "status": "created"},
            )
        )
        result = sync_client.db.create_table(
            table_name="events",
            columns=[
                {"name": "id", "col_type": "uint64"},
                {"name": "data", "col_type": "string"},
            ],
        )
        assert result["table_name"] == "events"
        assert result["status"] == "created"

    def test_create_table_sends_correct_body(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        import json

        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json={"table_name": "t1", "status": "created"})

        mock_api.post("/v1/db/tables").mock(side_effect=capture)
        sync_client.db.create_table(
            table_name="t1",
            columns=[{"name": "id", "col_type": "uint64"}],
        )
        assert captured["body"]["table_name"] == "t1"
        assert len(captured["body"]["columns"]) == 1

    def test_insert(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/db/insert").mock(
            return_value=httpx.Response(
                200,
                json={"inserted": 3},
            )
        )
        result = sync_client.db.insert(
            table_name="events",
            columns=[
                {"name": "id", "data": [1, 2, 3]},
                {"name": "data", "data": ["a", "b", "c"]},
            ],
        )
        assert result["inserted"] == 3

    def test_query(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/db/query").mock(
            return_value=httpx.Response(
                200,
                json={
                    "columns": ["id", "data"],
                    "rows": [[1, "a"], [2, "b"]],
                    "total": 2,
                },
            )
        )
        result = sync_client.db.query("events")
        assert isinstance(result, QueryResponse)
        assert result.total == 2
        assert len(result.rows) == 2
        assert result.columns == ["id", "data"]

    def test_query_with_filters(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        import json

        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200, json={"columns": ["id"], "rows": [[5]], "total": 1}
            )

        mock_api.post("/v1/db/query").mock(side_effect=capture)
        sync_client.db.query(
            "events",
            filters=[{"column": "id", "op": "gt", "value": 4}],
            columns=["id"],
            limit=10,
            offset=0,
        )
        assert captured["body"]["filters"][0]["op"] == "gt"
        assert captured["body"]["limit"] == 10
        assert captured["body"]["columns"] == ["id"]

    def test_vector_search(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/db/vector-search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "columns": ["id", "score"],
                    "rows": [[1, 0.95], [2, 0.87]],
                    "total": 2,
                },
            )
        )
        result = sync_client.db.vector_search(
            table_name="embeddings",
            column="vec",
            vector=[0.1, 0.2, 0.3],
            top_k=5,
        )
        assert isinstance(result, QueryResponse)
        assert result.total == 2

    def test_vector_search_sends_correct_body(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        import json

        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200, json={"columns": [], "rows": [], "total": 0}
            )

        mock_api.post("/v1/db/vector-search").mock(side_effect=capture)
        sync_client.db.vector_search(
            table_name="emb",
            column="vec",
            vector=[1.0, 2.0],
            top_k=3,
        )
        assert captured["body"]["table_name"] == "emb"
        assert captured["body"]["column"] == "vec"
        assert captured["body"]["vector"] == [1.0, 2.0]
        assert captured["body"]["top_k"] == 3

    def test_scroll(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/db/scroll").mock(
            return_value=httpx.Response(
                200,
                json={
                    "columns": ["id"],
                    "rows": [[1], [2], [3]],
                    "next_cursor": "cursor-abc",
                    "has_more": True,
                },
            )
        )
        result = sync_client.db.scroll(table_name="events", batch_size=3)
        assert isinstance(result, ScrollQueryResponse)
        assert result.has_more is True
        assert result.next_cursor == "cursor-abc"
        assert len(result.rows) == 3

    def test_scroll_with_cursor(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        import json

        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "columns": ["id"],
                    "rows": [[4], [5]],
                    "next_cursor": None,
                    "has_more": False,
                },
            )

        mock_api.post("/v1/db/scroll").mock(side_effect=capture)
        result = sync_client.db.scroll(
            table_name="events", batch_size=100, cursor="cursor-abc"
        )
        assert captured["body"]["cursor"] == "cursor-abc"
        assert result.has_more is False

    def test_init_cluster(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/db/cluster/init").mock(
            return_value=httpx.Response(
                200,
                json={
                    "cluster_name": "prod",
                    "status": "initializing",
                    "node_count": 3,
                    "healthy_nodes": 0,
                },
            )
        )
        result = sync_client.db.init_cluster(
            cluster_name="prod", node_count=3, replication_factor=2
        )
        assert isinstance(result, ClusterStatusResponse)
        assert result.cluster_name == "prod"
        assert result.node_count == 3

    def test_cluster_status(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/db/cluster/prod/status").mock(
            return_value=httpx.Response(
                200,
                json={
                    "cluster_name": "prod",
                    "status": "healthy",
                    "node_count": 3,
                    "healthy_nodes": 3,
                },
            )
        )
        result = sync_client.db.cluster_status("prod")
        assert result.status == "healthy"
        assert result.healthy_nodes == 3


class TestDBErrorHandling:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_401_on_query(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/db/query").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )
        with pytest.raises(AuthenticationError):
            sync_client.db.query("events")

    def test_404_on_cluster_status(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/db/cluster/nonexistent/status").mock(
            return_value=httpx.Response(404, json={"message": "Cluster not found"})
        )
        with pytest.raises(NotFoundError):
            sync_client.db.cluster_status("nonexistent")

    def test_422_on_create_table(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/db/tables").mock(
            return_value=httpx.Response(
                422, json={"message": "Invalid column type"}
            )
        )
        with pytest.raises(ValidationError):
            sync_client.db.create_table("t", columns=[{"name": "x", "col_type": "bad"}])

    def test_429_on_insert(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/db/insert").mock(
            return_value=httpx.Response(
                429, json={"message": "Rate limited", "retry_after": 5.0}
            )
        )
        with pytest.raises(RateLimitError) as exc_info:
            sync_client.db.insert("events", columns=[])
        assert exc_info.value.retry_after == 5.0

    def test_500_on_vector_search(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/db/vector-search").mock(
            return_value=httpx.Response(500, json={"message": "Internal error"})
        )
        with pytest.raises(ServerError):
            sync_client.db.vector_search("emb", "vec", [0.1], top_k=5)


class TestDBAsyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    @pytest.mark.asyncio
    async def test_async_query(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/db/query").mock(
            return_value=httpx.Response(
                200,
                json={"columns": ["id"], "rows": [[1]], "total": 1},
            )
        )
        result = await async_client.db.async_query("events")
        assert result.total == 1
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_create_table(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/db/tables").mock(
            return_value=httpx.Response(
                200, json={"table_name": "t1", "status": "created"}
            )
        )
        result = await async_client.db.async_create_table(
            "t1", columns=[{"name": "id", "col_type": "uint64"}]
        )
        assert result["status"] == "created"
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_insert(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/db/insert").mock(
            return_value=httpx.Response(200, json={"inserted": 2})
        )
        result = await async_client.db.async_insert(
            "events", columns=[{"name": "id", "data": [1, 2]}]
        )
        assert result["inserted"] == 2
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_vector_search(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/db/vector-search").mock(
            return_value=httpx.Response(
                200, json={"columns": ["id"], "rows": [[1]], "total": 1}
            )
        )
        result = await async_client.db.async_vector_search(
            "emb", "vec", [0.1, 0.2], top_k=1
        )
        assert result.total == 1
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_scroll(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/db/scroll").mock(
            return_value=httpx.Response(
                200,
                json={
                    "columns": ["id"],
                    "rows": [[1]],
                    "next_cursor": None,
                    "has_more": False,
                },
            )
        )
        result = await async_client.db.async_scroll("events")
        assert result.has_more is False
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_init_cluster(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/db/cluster/init").mock(
            return_value=httpx.Response(
                200,
                json={
                    "cluster_name": "dev",
                    "status": "initializing",
                    "node_count": 1,
                    "healthy_nodes": 0,
                },
            )
        )
        result = await async_client.db.async_init_cluster("dev")
        assert result.cluster_name == "dev"
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_cluster_status(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/db/cluster/dev/status").mock(
            return_value=httpx.Response(
                200,
                json={
                    "cluster_name": "dev",
                    "status": "healthy",
                    "node_count": 1,
                    "healthy_nodes": 1,
                },
            )
        )
        result = await async_client.db.async_cluster_status("dev")
        assert result.status == "healthy"
        await async_client.aclose()
