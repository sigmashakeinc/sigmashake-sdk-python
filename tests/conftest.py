"""Shared fixtures for SigmaShake SDK tests."""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

# Stub claude_agent_sdk before any test imports it --------------------------------
if "claude_agent_sdk" not in sys.modules:
    _mock_sdk = ModuleType("claude_agent_sdk")

    def _tool(name, description, schema):
        """Minimal tool decorator that attaches metadata."""
        def decorator(fn):
            fn.name = name
            fn.description = description
            fn.schema = schema
            return fn
        return decorator

    _mock_sdk.tool = _tool  # type: ignore[attr-defined]
    _mock_sdk.create_sdk_mcp_server = MagicMock(return_value={"name": "sigmashake"})  # type: ignore[attr-defined]
    _mock_sdk.ClaudeSDKClient = MagicMock  # type: ignore[attr-defined]
    _mock_sdk.ClaudeAgentOptions = MagicMock  # type: ignore[attr-defined]
    _mock_sdk.AgentDefinition = MagicMock  # type: ignore[attr-defined]
    sys.modules["claude_agent_sdk"] = _mock_sdk
# ----------------------------------------------------------------------------------

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
