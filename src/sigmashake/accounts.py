"""Account management operations."""

from __future__ import annotations

from typing import Any, List, Optional, TYPE_CHECKING

from .models import (
    Account,
    AddSeatBody,
    Seat,
    Subscription,
    TenantUsage,
    Tier,
    UpdateSubscriptionBody,
)

if TYPE_CHECKING:
    from .client import _HTTPTransport


class AccountsResource:
    """Account CRUD and subscription management."""

    def __init__(self, transport: _HTTPTransport) -> None:
        self._t = transport

    # -- accounts -------------------------------------------------------------

    def create(self, name: str, tier: str = "free") -> Account:
        body = {"name": name, "tier": tier}
        data = self._t.request("POST", "/v1/accounts", json=body)
        return Account.model_validate(data)

    async def async_create(self, name: str, tier: str = "free") -> Account:
        body = {"name": name, "tier": tier}
        data = await self._t.async_request("POST", "/v1/accounts", json=body)
        return Account.model_validate(data)

    def get(self, account_id: str) -> Account:
        data = self._t.request("GET", f"/v1/accounts/{account_id}")
        return Account.model_validate(data)

    async def async_get(self, account_id: str) -> Account:
        data = await self._t.async_request("GET", f"/v1/accounts/{account_id}")
        return Account.model_validate(data)

    def get_usage(self, account_id: str) -> TenantUsage:
        data = self._t.request("GET", f"/v1/accounts/{account_id}/usage")
        return TenantUsage.model_validate(data)

    async def async_get_usage(self, account_id: str) -> TenantUsage:
        data = await self._t.async_request("GET", f"/v1/accounts/{account_id}/usage")
        return TenantUsage.model_validate(data)

    # -- subscriptions --------------------------------------------------------

    def get_subscription(self, account_id: str) -> Subscription:
        data = self._t.request("GET", f"/v1/accounts/{account_id}/subscription")
        return Subscription.model_validate(data)

    async def async_get_subscription(self, account_id: str) -> Subscription:
        data = await self._t.async_request("GET", f"/v1/accounts/{account_id}/subscription")
        return Subscription.model_validate(data)

    def update_subscription(self, account_id: str, **kwargs: Any) -> Subscription:
        data = self._t.request("PUT", f"/v1/accounts/{account_id}/subscription", json=kwargs)
        return Subscription.model_validate(data)

    async def async_update_subscription(self, account_id: str, **kwargs: Any) -> Subscription:
        data = await self._t.async_request("PUT", f"/v1/accounts/{account_id}/subscription", json=kwargs)
        return Subscription.model_validate(data)

    # -- seats ----------------------------------------------------------------

    def add_seat(self, account_id: str, user_email: str, role: str = "member") -> Seat:
        body = {"user_email": user_email, "role": role}
        data = self._t.request("POST", f"/v1/accounts/{account_id}/seats", json=body)
        return Seat.model_validate(data)

    async def async_add_seat(self, account_id: str, user_email: str, role: str = "member") -> Seat:
        body = {"user_email": user_email, "role": role}
        data = await self._t.async_request("POST", f"/v1/accounts/{account_id}/seats", json=body)
        return Seat.model_validate(data)

    def list_seats(self, account_id: str) -> List[Seat]:
        data = self._t.request("GET", f"/v1/accounts/{account_id}/seats")
        return [Seat.model_validate(s) for s in data.get("seats", data if isinstance(data, list) else [])]

    async def async_list_seats(self, account_id: str) -> List[Seat]:
        data = await self._t.async_request("GET", f"/v1/accounts/{account_id}/seats")
        return [Seat.model_validate(s) for s in data.get("seats", data if isinstance(data, list) else [])]
