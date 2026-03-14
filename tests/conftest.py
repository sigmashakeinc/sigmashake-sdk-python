"""Shared fixtures for SigmaShake SDK tests."""

from __future__ import annotations

import pytest
import respx

from sigmashake import SigmaShake


@pytest.fixture()
def base_url() -> str:
    return "https://api.test.sigmashake.com"


@pytest.fixture()
def api_key() -> str:
    return "sk-test-key-000"


@pytest.fixture()
def sync_client(base_url: str, api_key: str) -> SigmaShake:
    client = SigmaShake(api_key=api_key, base_url=base_url)
    yield client
    client.close()


@pytest.fixture()
def async_client(base_url: str, api_key: str) -> SigmaShake:
    return SigmaShake(api_key=api_key, base_url=base_url, async_mode=True)


@pytest.fixture()
def mock_api(base_url: str):
    with respx.mock(base_url=base_url, assert_all_called=False) as router:
        yield router
