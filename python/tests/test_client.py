"""Tests for the NativeClient."""

import pytest
from playgodot.native_client import NativeClient


class TestNativeClient:
    """Tests for the NativeClient class."""

    def test_default_host_port(self) -> None:
        """Test default host and port."""
        client = NativeClient()
        assert client.host == "localhost"
        assert client.port == 6007

    def test_custom_host_port(self) -> None:
        """Test custom host and port."""
        client = NativeClient(host="192.168.1.1", port=8888)
        assert client.host == "192.168.1.1"
        assert client.port == 8888

    def test_not_connected_by_default(self) -> None:
        """Test that client is not connected by default."""
        client = NativeClient()
        assert not client.is_connected