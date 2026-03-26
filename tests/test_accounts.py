"""Tests for AccountsResource — CRUD, subscriptions, seats, usage."""

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
from sigmashake.models import Account, Seat, Subscription, TenantUsage, Tier


class TestAccountsSyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_create_account(
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
        assert isinstance(account, Account)
        assert account.id == "acc-1"
        assert account.name == "My Org"
        assert account.tier == Tier.pro

    def test_create_account_default_tier(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        import json

        captured = {}

        def capture(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "id": "acc-2",
                    "name": "Free Org",
                    "tier": "free",
                    "created_at": "2026-01-01T00:00:00Z",
                },
            )

        mock_api.post("/v1/accounts").mock(side_effect=capture)
        account = sync_client.accounts.create(name="Free Org")
        assert captured["body"]["tier"] == "free"
        assert account.tier == Tier.free

    def test_get_account(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/accounts/acc-1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "acc-1",
                    "name": "Test Org",
                    "tier": "enterprise",
                    "created_at": "2026-01-01T00:00:00Z",
                },
            )
        )
        account = sync_client.accounts.get("acc-1")
        assert account.id == "acc-1"
        assert account.tier == Tier.enterprise

    def test_get_usage(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/accounts/acc-1/usage").mock(
            return_value=httpx.Response(
                200,
                json={
                    "account_id": "acc-1",
                    "period_start": "2026-01-01T00:00:00Z",
                    "period_end": "2026-02-01T00:00:00Z",
                    "api_calls": 5000,
                    "storage_bytes": 1000000,
                    "compute_seconds": 450.5,
                },
            )
        )
        usage = sync_client.accounts.get_usage("acc-1")
        assert isinstance(usage, TenantUsage)
        assert usage.api_calls == 5000
        assert usage.compute_seconds == 450.5

    def test_get_subscription(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/accounts/acc-1/subscription").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "sub-1",
                    "account_id": "acc-1",
                    "tier": "pro",
                    "status": "active",
                },
            )
        )
        sub = sync_client.accounts.get_subscription("acc-1")
        assert isinstance(sub, Subscription)
        assert sub.id == "sub-1"
        assert sub.tier == Tier.pro

    def test_update_subscription(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.put("/v1/accounts/acc-1/subscription").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "sub-1",
                    "account_id": "acc-1",
                    "tier": "enterprise",
                    "status": "active",
                },
            )
        )
        sub = sync_client.accounts.update_subscription("acc-1", tier="enterprise")
        assert sub.tier == Tier.enterprise

    def test_add_seat(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/accounts/acc-1/seats").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "seat-1",
                    "account_id": "acc-1",
                    "user_email": "user@example.com",
                    "role": "member",
                    "created_at": "2026-01-01T00:00:00Z",
                },
            )
        )
        seat = sync_client.accounts.add_seat("acc-1", user_email="user@example.com")
        assert isinstance(seat, Seat)
        assert seat.user_email == "user@example.com"
        assert seat.role.value == "member"

    def test_add_seat_with_role(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/accounts/acc-1/seats").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "seat-2",
                    "account_id": "acc-1",
                    "user_email": "admin@example.com",
                    "role": "admin",
                    "created_at": "2026-01-01T00:00:00Z",
                },
            )
        )
        seat = sync_client.accounts.add_seat(
            "acc-1", user_email="admin@example.com", role="admin"
        )
        assert seat.role.value == "admin"

    def test_list_seats(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/accounts/acc-1/seats").mock(
            return_value=httpx.Response(
                200,
                json={
                    "seats": [
                        {
                            "id": "seat-1",
                            "account_id": "acc-1",
                            "user_email": "a@b.com",
                            "role": "owner",
                            "created_at": "2026-01-01T00:00:00Z",
                        },
                        {
                            "id": "seat-2",
                            "account_id": "acc-1",
                            "user_email": "c@d.com",
                            "role": "member",
                            "created_at": "2026-01-02T00:00:00Z",
                        },
                    ]
                },
            )
        )
        seats = sync_client.accounts.list_seats("acc-1")
        assert len(seats) == 2
        assert seats[0].role.value == "owner"


class TestAccountsErrorHandling:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    def test_404_on_get_account(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/accounts/nonexistent").mock(
            return_value=httpx.Response(404, json={"message": "Not found"})
        )
        with pytest.raises(NotFoundError):
            sync_client.accounts.get("nonexistent")

    def test_422_on_create_account(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/accounts").mock(
            return_value=httpx.Response(422, json={"message": "Invalid tier"})
        )
        with pytest.raises(ValidationError):
            sync_client.accounts.create(name="test", tier="invalid")

    def test_401_on_get_usage(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/accounts/acc-1/usage").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )
        with pytest.raises(AuthenticationError):
            sync_client.accounts.get_usage("acc-1")

    def test_429_on_create_account(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/accounts").mock(
            return_value=httpx.Response(
                429, json={"message": "Too many requests", "retry_after": 3.0}
            )
        )
        with pytest.raises(RateLimitError) as exc_info:
            sync_client.accounts.create(name="test")
        assert exc_info.value.retry_after == 3.0

    def test_500_on_get_subscription(
        self, sync_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/accounts/acc-1/subscription").mock(
            return_value=httpx.Response(500, json={"message": "Internal error"})
        )
        with pytest.raises(ServerError):
            sync_client.accounts.get_subscription("acc-1")


class TestAccountsAsyncCalls:
    @pytest.fixture()
    def mock_api(self, base_url: str):
        with respx.mock(base_url=base_url, assert_all_called=False) as router:
            yield router

    @pytest.mark.asyncio
    async def test_async_create_account(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.post("/v1/accounts").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "acc-async",
                    "name": "Async Org",
                    "tier": "pro",
                    "created_at": "2026-01-01T00:00:00Z",
                },
            )
        )
        account = await async_client.accounts.async_create(name="Async Org", tier="pro")
        assert account.id == "acc-async"
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_get_account(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/accounts/acc-1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "acc-1",
                    "name": "Test",
                    "tier": "free",
                    "created_at": "2026-01-01T00:00:00Z",
                },
            )
        )
        account = await async_client.accounts.async_get("acc-1")
        assert account.id == "acc-1"
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_get_usage(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/accounts/acc-1/usage").mock(
            return_value=httpx.Response(
                200,
                json={
                    "account_id": "acc-1",
                    "period_start": "2026-01-01T00:00:00Z",
                    "period_end": "2026-02-01T00:00:00Z",
                    "api_calls": 100,
                    "storage_bytes": 0,
                    "compute_seconds": 0.0,
                },
            )
        )
        usage = await async_client.accounts.async_get_usage("acc-1")
        assert usage.api_calls == 100
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_list_seats(
        self, async_client: SigmaShake, mock_api: respx.Router
    ) -> None:
        mock_api.get("/v1/accounts/acc-1/seats").mock(
            return_value=httpx.Response(
                200,
                json={
                    "seats": [
                        {
                            "id": "seat-1",
                            "account_id": "acc-1",
                            "user_email": "u@x.com",
                            "role": "member",
                            "created_at": "2026-01-01T00:00:00Z",
                        }
                    ]
                },
            )
        )
        seats = await async_client.accounts.async_list_seats("acc-1")
        assert len(seats) == 1
        await async_client.aclose()
