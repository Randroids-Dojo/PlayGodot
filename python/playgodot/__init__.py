"""PlayGodot - External automation and testing framework for Godot Engine games.

Uses Godot's native RemoteDebugger protocol for automation.
"""

from playgodot.exceptions import (
    CommandError,
    ConnectionError,
    NodeNotFoundError,
    PlayGodotError,
    TimeoutError,
)
from playgodot.godot import Godot
from playgodot.native_client import NativeClient
from playgodot.node import Node

__version__ = "0.6.0"
__all__ = [
    "Godot",
    "Node",
    "NativeClient",
    "PlayGodotError",
    "ConnectionError",
    "TimeoutError",
    "NodeNotFoundError",
    "CommandError",
]
