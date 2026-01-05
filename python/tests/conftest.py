"""Shared pytest fixtures for PlayGodot tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_client():
    """Create a mock NativeClient."""
    client = MagicMock()
    client.send = AsyncMock()
    client.is_connected = True
    client._writer = MagicMock()
    client._reader = MagicMock()
    return client


@pytest.fixture
def mock_godot(mock_client):
    """Create a Godot instance with mock client."""
    from playgodot.godot import Godot
    return Godot(client=mock_client, process=None)


@pytest.fixture
def mock_input_simulator(mock_client):
    """Create a NativeInputSimulator with mock client."""
    from playgodot.native_input import NativeInputSimulator
    return NativeInputSimulator(mock_client)
