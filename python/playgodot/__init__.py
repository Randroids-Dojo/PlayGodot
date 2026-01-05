"""PlayGodot - External automation and testing framework for Godot Engine games.

Uses Godot's native RemoteDebugger protocol for automation.
"""

from playgodot.godot import Godot
from playgodot.node import Node
from playgodot.native_client import NativeClient
from playgodot.exceptions import (
    PlayGodotError,
    ConnectionError,
    TimeoutError,
    NodeNotFoundError,
    CommandError,
)

__version__ = "0.5.0"
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
