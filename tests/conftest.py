"""Pytest configuration and common fixtures for kodekloud-mcp."""

from typing import Any

import pytest

from kodekloud_mcp.config import Settings
from kodekloud_mcp.kodekloud_client import KodeKloudClient
from kodekloud_mcp.server import create_server


@pytest.fixture
def mock_settings() -> Settings:
    """Settings configured for offline mock mode."""
    return Settings(
        session_credential="mock_token_12345",
        use_mock=True,
        enable_write_tools=False,
        cache_ttl_seconds=60,
    )


@pytest.fixture
def mock_write_settings() -> Settings:
    """Settings configured for offline mock mode with write tools enabled."""
    return Settings(
        session_credential="mock_token_12345",
        use_mock=True,
        enable_write_tools=True,
        cache_ttl_seconds=60,
    )


@pytest.fixture
def mock_client(mock_settings: Settings) -> KodeKloudClient:
    """Client configured for mock mode."""
    return KodeKloudClient(settings=mock_settings)


@pytest.fixture
def mock_server(mock_settings: Settings) -> Any:
    """Server configured with mock settings (read-only)."""
    return create_server(settings=mock_settings)


@pytest.fixture
def mock_write_server(mock_write_settings: Settings) -> Any:
    """Server configured with write tools enabled."""
    return create_server(settings=mock_write_settings)
