"""PlayGodot - External automation and testing framework for Godot Engine games."""

from playgodot.godot import Godot
from playgodot.node import Node
from playgodot.exceptions import (
    PlayGodotError,
    ConnectionError,
    TimeoutError,
    NodeNotFoundError,
    CommandError,
)

__version__ = "0.1.0"
__all__ = [
    "Godot",
    "Node",
    "PlayGodotError",
    "ConnectionError",
    "TimeoutError",
    "NodeNotFoundError",
    "CommandError",
]
