"""PlayGodot exceptions."""

from __future__ import annotations


class PlayGodotError(Exception):
    """Base exception for PlayGodot errors."""

    pass


class ConnectionError(PlayGodotError):
    """Raised when connection to Godot fails."""

    pass


class TimeoutError(PlayGodotError):
    """Raised when an operation times out."""

    pass


class NodeNotFoundError(PlayGodotError):
    """Raised when a node cannot be found."""

    def __init__(self, path: str, message: str | None = None):
        self.path = path
        super().__init__(message or f"Node not found: {path}")


class CommandError(PlayGodotError):
    """Raised when a command fails on the Godot side."""

    def __init__(self, method: str, message: str, code: int | None = None):
        self.method = method
        self.code = code
        super().__init__(f"Command '{method}' failed: {message}")
