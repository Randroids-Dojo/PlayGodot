"""Tests for exceptions."""

import pytest
from playgodot.exceptions import (
    PlayGodotError,
    ConnectionError,
    TimeoutError,
    NodeNotFoundError,
    CommandError,
)


class TestExceptions:
    """Tests for PlayGodot exceptions."""

    def test_base_exception(self) -> None:
        """Test PlayGodotError is the base class."""
        assert issubclass(ConnectionError, PlayGodotError)
        assert issubclass(TimeoutError, PlayGodotError)
        assert issubclass(NodeNotFoundError, PlayGodotError)
        assert issubclass(CommandError, PlayGodotError)

    def test_node_not_found_error(self) -> None:
        """Test NodeNotFoundError stores the path."""
        error = NodeNotFoundError("/root/Main/Player")
        assert error.path == "/root/Main/Player"
        assert "Node not found: /root/Main/Player" in str(error)

    def test_node_not_found_custom_message(self) -> None:
        """Test NodeNotFoundError with custom message."""
        error = NodeNotFoundError("/root/Main/Enemy", "Enemy was destroyed")
        assert error.path == "/root/Main/Enemy"
        assert "Enemy was destroyed" in str(error)

    def test_command_error(self) -> None:
        """Test CommandError stores method and code."""
        error = CommandError("get_node", "Invalid path", code=-32600)
        assert error.method == "get_node"
        assert error.code == -32600
        assert "get_node" in str(error)
        assert "Invalid path" in str(error)
