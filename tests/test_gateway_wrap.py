"""Tests for GatewayResource.wrap() convenience method."""

from __future__ import annotations

import httpx
import pytest
import respx

from sigmashake import SigmaShake


class TestWrapSync:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_wrap_calls_intercept_pre_and_post(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/gateway/intercept/pre").mock(
            return_value=httpx.Response(
                200, json={"allowed": True, "reasons": [], "modified_input": None}
            )
        )
        mock_api.post("/v1/gateway/intercept/post").mock(
            return_value=httpx.Response(
                200, json={"allowed": True, "reasons": [], "modified_input": None}
            )
        )

        def my_tool(x):
            return x * 2

        wrapped = sync_client.gateway.wrap(my_tool, agent_id="test-agent")
        result = wrapped(5)

        assert result == 10

    def test_wrap_is_non_fatal_when_gateway_down(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/gateway/intercept/pre").mock(
            return_value=httpx.Response(500, json={"message": "down"})
        )
        mock_api.post("/v1/gateway/intercept/post").mock(
            return_value=httpx.Response(500, json={"message": "down"})
        )

        def my_tool(x):
            return x + 1

        wrapped = sync_client.gateway.wrap(my_tool)
        result = wrapped(10)
        assert result == 11

    def test_wrap_preserves_function_name(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        def my_special_tool():
            pass

        wrapped = sync_client.gateway.wrap(my_special_tool)
        assert wrapped.__name__ == "my_special_tool"

    def test_wrap_sends_correct_input_shape(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        import json

        captured = {}

        def capture_pre(request: httpx.Request) -> httpx.Response:
            captured["pre"] = json.loads(request.content)
            return httpx.Response(
                200, json={"allowed": True, "reasons": [], "modified_input": None}
            )

        def capture_post(request: httpx.Request) -> httpx.Response:
            captured["post"] = json.loads(request.content)
            return httpx.Response(
                200, json={"allowed": True, "reasons": [], "modified_input": None}
            )

        mock_api.post("/v1/gateway/intercept/pre").mock(side_effect=capture_pre)
        mock_api.post("/v1/gateway/intercept/post").mock(side_effect=capture_post)

        def search(query, limit=10):
            return {"results": [query]}

        wrapped = sync_client.gateway.wrap(search, agent_id="agent-1")
        result = wrapped("hello", limit=5)

        assert result == {"results": ["hello"]}
        assert captured["pre"]["name"] == "search"
        assert captured["pre"]["input"]["args"] == ["hello"]
        assert captured["pre"]["input"]["kwargs"] == {"limit": 5}
        assert captured["post"]["output"] == {"results": ["hello"]}


class TestAsyncWrap:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    @pytest.mark.asyncio
    async def test_async_wrap_calls_intercepts(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/gateway/intercept/pre").mock(
            return_value=httpx.Response(
                200, json={"allowed": True, "reasons": [], "modified_input": None}
            )
        )
        mock_api.post("/v1/gateway/intercept/post").mock(
            return_value=httpx.Response(
                200, json={"allowed": True, "reasons": [], "modified_input": None}
            )
        )

        async def my_async_tool(x):
            return x * 3

        wrapped = async_client.gateway.async_wrap(my_async_tool, agent_id="async-agent")
        result = await wrapped(4)

        assert result == 12
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_wrap_is_non_fatal(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/gateway/intercept/pre").mock(
            return_value=httpx.Response(500, json={"message": "down"})
        )
        mock_api.post("/v1/gateway/intercept/post").mock(
            return_value=httpx.Response(500, json={"message": "down"})
        )

        async def my_async_tool(x):
            return x + 100

        wrapped = async_client.gateway.async_wrap(my_async_tool)
        result = await wrapped(5)
        assert result == 105
        await async_client.aclose()
