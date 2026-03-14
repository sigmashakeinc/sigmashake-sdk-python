"""Database operations."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .models import (
    ClusterStatusResponse,
    QueryResponse,
    ScrollQueryResponse,
)

if TYPE_CHECKING:
    from .client import _HTTPTransport


class DBResource:
    """SigmaShake database operations."""

    def __init__(self, transport: _HTTPTransport) -> None:
        self._t = transport

    # -- tables ---------------------------------------------------------------

    def create_table(
        self,
        table_name: str,
        columns: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        body = {"table_name": table_name, "columns": columns}
        return self._t.request("POST", "/v1/db/tables", json=body)

    async def async_create_table(
        self,
        table_name: str,
        columns: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        body = {"table_name": table_name, "columns": columns}
        return await self._t.async_request("POST", "/v1/db/tables", json=body)

    # -- insert ---------------------------------------------------------------

    def insert(
        self,
        table_name: str,
        columns: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        body = {"table_name": table_name, "columns": columns}
        return self._t.request("POST", "/v1/db/insert", json=body)

    async def async_insert(
        self,
        table_name: str,
        columns: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        body = {"table_name": table_name, "columns": columns}
        return await self._t.async_request("POST", "/v1/db/insert", json=body)

    # -- query ----------------------------------------------------------------

    def query(
        self,
        table_name: str,
        filters: Optional[List[Dict[str, Any]]] = None,
        columns: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> QueryResponse:
        body: Dict[str, Any] = {"table_name": table_name}
        if filters:
            body["filters"] = filters
        if columns:
            body["columns"] = columns
        if limit is not None:
            body["limit"] = limit
        if offset is not None:
            body["offset"] = offset
        data = self._t.request("POST", "/v1/db/query", json=body)
        return QueryResponse.model_validate(data)

    async def async_query(
        self,
        table_name: str,
        filters: Optional[List[Dict[str, Any]]] = None,
        columns: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> QueryResponse:
        body: Dict[str, Any] = {"table_name": table_name}
        if filters:
            body["filters"] = filters
        if columns:
            body["columns"] = columns
        if limit is not None:
            body["limit"] = limit
        if offset is not None:
            body["offset"] = offset
        data = await self._t.async_request("POST", "/v1/db/query", json=body)
        return QueryResponse.model_validate(data)

    # -- vector search --------------------------------------------------------

    def vector_search(
        self,
        table_name: str,
        column: str,
        vector: List[float],
        top_k: int = 10,
        filters: Optional[List[Dict[str, Any]]] = None,
    ) -> QueryResponse:
        body: Dict[str, Any] = {
            "table_name": table_name,
            "column": column,
            "vector": vector,
            "top_k": top_k,
        }
        if filters:
            body["filters"] = filters
        data = self._t.request("POST", "/v1/db/vector-search", json=body)
        return QueryResponse.model_validate(data)

    async def async_vector_search(
        self,
        table_name: str,
        column: str,
        vector: List[float],
        top_k: int = 10,
        filters: Optional[List[Dict[str, Any]]] = None,
    ) -> QueryResponse:
        body: Dict[str, Any] = {
            "table_name": table_name,
            "column": column,
            "vector": vector,
            "top_k": top_k,
        }
        if filters:
            body["filters"] = filters
        data = await self._t.async_request("POST", "/v1/db/vector-search", json=body)
        return QueryResponse.model_validate(data)

    # -- scroll ---------------------------------------------------------------

    def scroll(
        self,
        table_name: str,
        batch_size: int = 100,
        cursor: Optional[str] = None,
        filters: Optional[List[Dict[str, Any]]] = None,
    ) -> ScrollQueryResponse:
        body: Dict[str, Any] = {"table_name": table_name, "batch_size": batch_size}
        if cursor:
            body["cursor"] = cursor
        if filters:
            body["filters"] = filters
        data = self._t.request("POST", "/v1/db/scroll", json=body)
        return ScrollQueryResponse.model_validate(data)

    async def async_scroll(
        self,
        table_name: str,
        batch_size: int = 100,
        cursor: Optional[str] = None,
        filters: Optional[List[Dict[str, Any]]] = None,
    ) -> ScrollQueryResponse:
        body: Dict[str, Any] = {"table_name": table_name, "batch_size": batch_size}
        if cursor:
            body["cursor"] = cursor
        if filters:
            body["filters"] = filters
        data = await self._t.async_request("POST", "/v1/db/scroll", json=body)
        return ScrollQueryResponse.model_validate(data)

    # -- cluster --------------------------------------------------------------

    def init_cluster(
        self,
        cluster_name: str,
        node_count: int = 1,
        replication_factor: int = 1,
        config: Optional[Dict[str, Any]] = None,
    ) -> ClusterStatusResponse:
        body = {
            "cluster_name": cluster_name,
            "node_count": node_count,
            "replication_factor": replication_factor,
            "config": config or {},
        }
        data = self._t.request("POST", "/v1/db/cluster/init", json=body)
        return ClusterStatusResponse.model_validate(data)

    async def async_init_cluster(
        self,
        cluster_name: str,
        node_count: int = 1,
        replication_factor: int = 1,
        config: Optional[Dict[str, Any]] = None,
    ) -> ClusterStatusResponse:
        body = {
            "cluster_name": cluster_name,
            "node_count": node_count,
            "replication_factor": replication_factor,
            "config": config or {},
        }
        data = await self._t.async_request("POST", "/v1/db/cluster/init", json=body)
        return ClusterStatusResponse.model_validate(data)

    def cluster_status(self, cluster_name: str) -> ClusterStatusResponse:
        data = self._t.request("GET", f"/v1/db/cluster/{cluster_name}/status")
        return ClusterStatusResponse.model_validate(data)

    async def async_cluster_status(self, cluster_name: str) -> ClusterStatusResponse:
        data = await self._t.async_request("GET", f"/v1/db/cluster/{cluster_name}/status")
        return ClusterStatusResponse.model_validate(data)
