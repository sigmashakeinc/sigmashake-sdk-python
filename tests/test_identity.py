"""Tests for IdentityResource — raises NotImplementedError."""

from __future__ import annotations

import pytest

from sigmashake import SigmaShake


class TestIdentitySyncCalls:
    def test_issue_raises_not_implemented(self, sync_client: SigmaShake) -> None:
        with pytest.raises(NotImplementedError, match="Not yet implemented"):
            sync_client.identity.issue(agent_id="a1", capabilities=["tool_use"], ttl_secs=3600)

    def test_issue_no_args_raises_not_implemented(self, sync_client: SigmaShake) -> None:
        with pytest.raises(NotImplementedError, match="Not yet implemented"):
            sync_client.identity.issue(agent_id="a1")


class TestIdentityAsyncCalls:
    @pytest.mark.asyncio
    async def test_async_issue_raises_not_implemented(self, async_client: SigmaShake) -> None:
        with pytest.raises(NotImplementedError, match="Not yet implemented"):
            await async_client.identity.async_issue(agent_id="a1", capabilities=["tool_use"])
        await async_client.aclose()
