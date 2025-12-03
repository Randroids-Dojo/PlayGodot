"""Tests for the WebSocket client."""

import pytest
from playgodot.client import Client


class TestClient:
    """Tests for the Client class."""

    def test_url_generation(self) -> None:
        """Test that the URL is correctly generated."""
        client = Client(host="localhost", port=9999)
        assert client.url == "ws://localhost:9999"

    def test_custom_host_port(self) -> None:
        """Test custom host and port."""
        client = Client(host="192.168.1.1", port=8888)
        assert client.url == "ws://192.168.1.1:8888"

    def test_not_connected_by_default(self) -> None:
        """Test that client is not connected by default."""
        client = Client()
        assert not client.is_connected
