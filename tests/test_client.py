"""Tests for client initialization, resource access, and HTTP error mapping."""

from __future__ import annotations

import httpx
import pytest
import respx

from sigmashake import (
    SigmaShake,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    SigmaShakeError,
    ValidationError,
)


class TestClientInit:
    def test_creates_sync_client(self, sync_client: SigmaShake) -> None:
        assert sync_client._transport._sync_client is not None
        assert sync_client._transport._async_client is None

    def test_creates_async_client(self, async_client: SigmaShake) -> None:
        assert async_client._transport._async_client is not None
        assert async_client._transport._sync_client is None

    def test_default_base_url(self, api_key: str) -> None:
        client = SigmaShake(api_key=api_key)
        assert client._transport._base_url == "https://api.sigmashake.com"
        client.close()

    def test_custom_base_url(self, api_key: str) -> None:
        client = SigmaShake(api_key=api_key, base_url="https://custom.api.com/")
        assert client._transport._base_url == "https://custom.api.com"
        client.close()

    def test_resource_namespaces_exist(self, sync_client: SigmaShake) -> None:
        assert sync_client.auth is not None
        assert sync_client.identity is not None
        assert sync_client.accounts is not None
        assert sync_client.agents is not None
        assert sync_client.shield is not None
        assert sync_client.soc is not None
        assert sync_client.gateway is not None
        assert sync_client.db is not None
        assert sync_client.memory is not None
        assert sync_client.documents is not None

    def test_context_manager_sync(self, api_key: str, base_url: str) -> None:
        with SigmaShake(api_key=api_key, base_url=base_url) as client:
            assert client._transport._sync_client is not None


class TestErrorMapping:
    """Test that HTTP status codes map to the correct SDK exceptions."""

    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_401_raises_authentication_error(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/auth/token").mock(
            return_value=httpx.Response(401, json={"message": "Invalid API key"})
        )
        with pytest.raises(AuthenticationError) as exc_info:
            sync_client.auth.create_token(agent_id="a1", scopes=["read"])
        assert exc_info.value.status_code == 401
        assert "Invalid API key" in str(exc_info.value)

    def test_403_raises_authorization_error(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/auth/token").mock(
            return_value=httpx.Response(403, json={"message": "Forbidden"})
        )
        with pytest.raises(AuthorizationError):
            sync_client.auth.create_token(agent_id="a1")

    def test_404_raises_not_found_error(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/accounts/nonexistent").mock(
            return_value=httpx.Response(404, json={"message": "Not found"})
        )
        with pytest.raises(NotFoundError):
            sync_client.accounts.get("nonexistent")

    def test_422_raises_validation_error(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/accounts").mock(
            return_value=httpx.Response(422, json={"message": "Invalid tier"})
        )
        with pytest.raises(ValidationError):
            sync_client.accounts.create(name="test", tier="invalid")

    def test_429_raises_rate_limit_error(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/auth/token").mock(
            return_value=httpx.Response(
                429, json={"message": "Too many requests", "retry_after": 1.5}
            )
        )
        with pytest.raises(RateLimitError) as exc_info:
            sync_client.auth.create_token(agent_id="a1")
        assert exc_info.value.retry_after == 1.5

    def test_500_raises_server_error(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/auth/token").mock(
            return_value=httpx.Response(500, json={"message": "Internal error"})
        )
        with pytest.raises(ServerError) as exc_info:
            sync_client.auth.create_token(agent_id="a1")
        assert exc_info.value.status_code == 500

    def test_unknown_error_code_raises_base(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/auth/token").mock(
            return_value=httpx.Response(418, json={"message": "I'm a teapot"})
        )
        with pytest.raises(SigmaShakeError):
            sync_client.auth.create_token(agent_id="a1")

    def test_error_carries_response_body(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        body = {"message": "Bad", "code": "INVALID_SCOPE", "details": {"field": "scopes"}}
        mock_api.post("/v1/auth/token").mock(
            return_value=httpx.Response(422, json=body)
        )
        with pytest.raises(ValidationError) as exc_info:
            sync_client.auth.create_token(agent_id="a1")
        assert exc_info.value.error_code == "INVALID_SCOPE"
        assert exc_info.value.response_body == body


class TestSyncAPICalls:
    """Test that sync resource methods make correct HTTP requests and parse responses."""

    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_auth_create_token(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/auth/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "token": "tok-abc",
                    "expires_at": "2026-12-31T23:59:59Z",
                    "scopes": ["read"],
                },
            )
        )
        token = sync_client.auth.create_token(agent_id="a1", scopes=["read"])
        assert token.token == "tok-abc"
        assert token.scopes == ["read"]

    def test_shield_register_agent(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/shield/register").mock(
            return_value=httpx.Response(
                200,
                json={
                    "session_id": "sess-1",
                    "agent_id": "a1",
                    "agent_type": "coding",
                    "created_at": "2026-01-01T00:00:00Z",
                    "expires_at": "2026-01-01T01:00:00Z",
                },
            )
        )
        session = sync_client.shield.register_agent(agent_id="a1", agent_type="coding")
        assert session.session_id == "sess-1"
        assert session.agent_type == "coding"

    def test_shield_scan(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/shield/scan").mock(
            return_value=httpx.Response(
                200,
                json={"allowed": True, "risk_score": 0.1, "reasons": []},
            )
        )
        result = sync_client.shield.scan(
            agent_id="a1",
            session_id="sess-1",
            operation={"name": "Bash", "input": {"command": "ls"}},
        )
        assert result.allowed is True
        assert result.risk_score == 0.1

    def test_memory_store_and_get(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/memory").mock(
            return_value=httpx.Response(
                200,
                json={"key": "ctx", "value": "data", "tags": ["s1"]},
            )
        )
        entry = sync_client.memory.store(key="ctx", value="data", tags=["s1"])
        assert entry.key == "ctx"
        assert entry.tags == ["s1"]

    def test_db_query(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/db/query").mock(
            return_value=httpx.Response(
                200,
                json={"columns": ["id", "data"], "rows": [[2, "b"], [3, "c"]], "total": 2},
            )
        )
        result = sync_client.db.query(
            "events", filters=[{"column": "id", "op": "gt", "value": 1}]
        )
        assert result.total == 2
        assert len(result.rows) == 2

    def test_gateway_intercept_pre(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/gateway/intercept/pre").mock(
            return_value=httpx.Response(
                200,
                json={"allowed": True, "reasons": [], "modified_input": None},
            )
        )
        result = sync_client.gateway.intercept_pre(
            name="Bash", input={"command": "ls"}, session_id="s1", agent_id="a1"
        )
        assert result.allowed is True

    def test_accounts_create(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/accounts").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "acc-1",
                    "name": "My Org",
                    "tier": "pro",
                    "created_at": "2026-01-01T00:00:00Z",
                },
            )
        )
        account = sync_client.accounts.create(name="My Org", tier="pro")
        assert account.id == "acc-1"
        assert account.tier.value == "pro"

    def test_soc_list_incidents(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/soc/incidents").mock(
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
                        }
                    ]
                },
            )
        )
        incidents = sync_client.soc.list_incidents(status="open", severity="critical")
        assert len(incidents) == 1
        assert incidents[0].severity == "critical"

    def test_documents_search(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/documents/search").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "total": 0},
            )
        )
        resp = sync_client.documents.search(query="auth", limit=5)
        assert resp.total == 0

    def test_identity_issue(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/identity/issue").mock(
            return_value=httpx.Response(
                200,
                json={
                    "token": "id-tok-abc",
                    "claims": {
                        "agent_id": "a1",
                        "capabilities": ["tool_use"],
                        "issued_at": "2026-01-01T00:00:00Z",
                        "expires_at": "2026-01-01T01:00:00Z",
                    },
                },
            )
        )
        identity = sync_client.identity.issue(
            agent_id="a1", capabilities=["tool_use"], ttl_secs=3600
        )
        assert identity.token == "id-tok-abc"
        assert identity.claims.agent_id == "a1"


class TestAsyncAPICalls:
    """Test async variants of key methods."""

    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    @pytest.mark.asyncio
    async def test_auth_create_token_async(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/auth/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "token": "tok-async",
                    "expires_at": "2026-12-31T23:59:59Z",
                    "scopes": ["write"],
                },
            )
        )
        token = await async_client.auth.async_create_token(agent_id="a1", scopes=["write"])
        assert token.token == "tok-async"
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_memory_store_async(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/memory").mock(
            return_value=httpx.Response(
                200,
                json={"key": "k", "value": "v", "tags": []},
            )
        )
        entry = await async_client.memory.async_store(key="k", value="v")
        assert entry.key == "k"
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_error_mapping_async(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/auth/token").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )
        with pytest.raises(AuthenticationError):
            await async_client.auth.async_create_token(agent_id="a1")
        await async_client.aclose()
