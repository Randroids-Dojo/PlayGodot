"""Native input simulation for the RemoteDebugger protocol.

Translates high-level input commands to the low-level primitives
supported by Godot's built-in automation protocol.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playgodot.native_client import NativeClient


# Godot key codes from core/os/keyboard.h
KEY_CODES = {
    # Special keys
    "escape": 0x01_0000,
    "tab": 0x01_0001,
    "backtab": 0x01_0002,
    "backspace": 0x01_0003,
    "enter": 0x01_0004,
    "return": 0x01_0004,
    "kp_enter": 0x01_0005,
    "insert": 0x01_0006,
    "delete": 0x01_0007,
    "pause": 0x01_0008,
    "print": 0x01_0009,
    "sysreq": 0x01_000A,
    "clear": 0x01_000B,
    "home": 0x01_000C,
    "end": 0x01_000D,
    "left": 0x01_000E,
    "up": 0x01_000F,
    "right": 0x01_0010,
    "down": 0x01_0011,
    "pageup": 0x01_0012,
    "pagedown": 0x01_0013,
    "shift": 0x01_0014,
    "ctrl": 0x01_0015,
    "meta": 0x01_0016,
    "alt": 0x01_0017,
    "capslock": 0x01_0018,
    "numlock": 0x01_0019,
    "scrolllock": 0x01_001A,
    "f1": 0x01_001B,
    "f2": 0x01_001C,
    "f3": 0x01_001D,
    "f4": 0x01_001E,
    "f5": 0x01_001F,
    "f6": 0x01_0020,
    "f7": 0x01_0021,
    "f8": 0x01_0022,
    "f9": 0x01_0023,
    "f10": 0x01_0024,
    "f11": 0x01_0025,
    "f12": 0x01_0026,
    "space": 0x20,
}

# Add lowercase letters
for i, char in enumerate("abcdefghijklmnopqrstuvwxyz"):
    KEY_CODES[char] = ord(char.upper())

# Add numbers
for i in range(10):
    KEY_CODES[str(i)] = ord(str(i))

# Mouse button indices from core/os/mouse.h
MOUSE_BUTTONS = {
    "left": 1,
    "right": 2,
    "middle": 3,
    "wheel_up": 4,
    "wheel_down": 5,
}


class NativeInputSimulator:
    """Handles input simulation using native automation protocol."""

    def __init__(self, client: NativeClient):
        self._client = client

    async def _get_node_center(self, path: str) -> tuple[float, float]:
        """Get the center position of a Control or Node2D node in global coordinates."""
        result = await self._client.send("get_node", {"path": path})
        if result is None:
            raise ValueError(f"Node not found: {path}")

        # Calculate global position by walking up the parent tree
        global_x, global_y = await self._get_global_position(path)

        # For Control nodes, add half the size to get center
        if "size" in result:
            size = result.get("size", {"x": 0, "y": 0})
            global_x += size.get("x", 0) / 2
            global_y += size.get("y", 0) / 2

        return (global_x, global_y)

    async def _get_global_position(self, path: str) -> tuple[float, float]:
        """Calculate global position by walking up parent tree."""
        global_x = 0.0
        global_y = 0.0

        # Walk up the path, accumulating positions
        parts = path.split("/")
        for i in range(len(parts), 2, -1):  # Start from full path, go up to /root/X
            current_path = "/".join(parts[:i])
            result = await self._client.send("get_node", {"path": current_path})
            if result and "position" in result:
                pos = result["position"]
                global_x += pos.get("x", 0)
                global_y += pos.get("y", 0)

        return (global_x, global_y)

    async def click(self, x: float, y: float, button: str = "left") -> None:
        """Simulate a mouse click at coordinates."""
        button_idx = MOUSE_BUTTONS.get(button, 1)
        # Press
        await self._client.send("mouse_button", {
            "x": x, "y": y, "button": button_idx, "pressed": True
        })
        await asyncio.sleep(0.05)
        # Release
        await self._client.send("mouse_button", {
            "x": x, "y": y, "button": button_idx, "pressed": False
        })

    async def click_node(self, path: str, button: str = "left") -> None:
        """Simulate a mouse click on a node."""
        x, y = await self._get_node_center(path)
        await self.click(x, y, button)

    async def double_click(self, x: float, y: float) -> None:
        """Simulate a double-click at coordinates."""
        # First click
        await self._client.send("mouse_button", {
            "x": x, "y": y, "button": 1, "pressed": True
        })
        await asyncio.sleep(0.02)
        await self._client.send("mouse_button", {
            "x": x, "y": y, "button": 1, "pressed": False
        })
        await asyncio.sleep(0.05)
        # Second click with double_click flag
        await self._client.send("mouse_button", {
            "x": x, "y": y, "button": 1, "pressed": True, "double_click": True
        })
        await asyncio.sleep(0.02)
        await self._client.send("mouse_button", {
            "x": x, "y": y, "button": 1, "pressed": False
        })

    async def double_click_node(self, path: str) -> None:
        """Simulate a double-click on a node."""
        x, y = await self._get_node_center(path)
        await self.double_click(x, y)

    async def right_click(self, x: float, y: float) -> None:
        """Simulate a right-click at coordinates."""
        await self.click(x, y, button="right")

    async def right_click_node(self, path: str) -> None:
        """Simulate a right-click on a node."""
        await self.click_node(path, button="right")

    async def move_mouse(self, x: float, y: float) -> None:
        """Move the mouse to coordinates."""
        await self._client.send("mouse_motion", {
            "x": x, "y": y, "rel_x": 0, "rel_y": 0
        })

    async def drag(
        self,
        from_x: float,
        from_y: float,
        to_x: float,
        to_y: float,
        duration: float = 0.5,
    ) -> None:
        """Simulate a drag operation."""
        # Press at start
        await self._client.send("mouse_button", {
            "x": from_x, "y": from_y, "button": 1, "pressed": True
        })

        # Move in steps
        steps = max(int(duration * 60), 10)  # ~60fps
        for i in range(1, steps + 1):
            t = i / steps
            x = from_x + (to_x - from_x) * t
            y = from_y + (to_y - from_y) * t
            await self._client.send("mouse_motion", {
                "x": x, "y": y,
                "rel_x": (to_x - from_x) / steps,
                "rel_y": (to_y - from_y) / steps
            })
            await asyncio.sleep(duration / steps)

        # Release at end
        await self._client.send("mouse_button", {
            "x": to_x, "y": to_y, "button": 1, "pressed": False
        })

    async def drag_node(self, from_path: str, to_path: str, duration: float = 0.5) -> None:
        """Simulate dragging from one node to another."""
        from_x, from_y = await self._get_node_center(from_path)
        to_x, to_y = await self._get_node_center(to_path)
        await self.drag(from_x, from_y, to_x, to_y, duration)

    async def press_key(self, key: str, modifiers: list[str] | None = None) -> None:
        """Simulate a key press."""
        # Press modifiers
        if modifiers:
            for mod in modifiers:
                keycode = KEY_CODES.get(mod.lower(), 0)
                if keycode:
                    await self._client.send("key", {
                        "keycode": keycode, "pressed": True
                    })

        # Press and release key
        keycode = KEY_CODES.get(key.lower(), ord(key.upper()) if len(key) == 1 else 0)
        await self._client.send("key", {"keycode": keycode, "pressed": True})
        await asyncio.sleep(0.02)
        await self._client.send("key", {"keycode": keycode, "pressed": False})

        # Release modifiers
        if modifiers:
            for mod in reversed(modifiers):
                keycode = KEY_CODES.get(mod.lower(), 0)
                if keycode:
                    await self._client.send("key", {
                        "keycode": keycode, "pressed": False
                    })

    async def type_text(self, text: str, delay: float = 0.05) -> None:
        """Type a string of text."""
        for char in text:
            keycode = ord(char.upper()) if char.isalpha() else ord(char)
            # For uppercase, hold shift
            needs_shift = char.isupper()
            if needs_shift:
                await self._client.send("key", {
                    "keycode": KEY_CODES["shift"], "pressed": True
                })
            await self._client.send("key", {"keycode": keycode, "pressed": True})
            await asyncio.sleep(delay / 2)
            await self._client.send("key", {"keycode": keycode, "pressed": False})
            if needs_shift:
                await self._client.send("key", {
                    "keycode": KEY_CODES["shift"], "pressed": False
                })
            await asyncio.sleep(delay / 2)

    async def press_action(self, action: str) -> None:
        """Press an input action."""
        await self._client.send("action", {"action": action, "pressed": True})
        await asyncio.sleep(0.02)
        await self._client.send("action", {"action": action, "pressed": False})

    async def hold_action(self, action: str, duration: float) -> None:
        """Hold an input action for a duration."""
        await self._client.send("action", {"action": action, "pressed": True})
        await asyncio.sleep(duration)
        await self._client.send("action", {"action": action, "pressed": False})

    async def release_action(self, action: str) -> None:
        """Release an input action."""
        await self._client.send("action", {"action": action, "pressed": False})

    async def tap(self, x: float, y: float) -> None:
        """Simulate a touch tap."""
        await self._client.send("touch", {"index": 0, "x": x, "y": y, "pressed": True})
        await asyncio.sleep(0.05)
        await self._client.send("touch", {"index": 0, "x": x, "y": y, "pressed": False})

    async def swipe(
        self,
        from_x: float,
        from_y: float,
        to_x: float,
        to_y: float,
        duration: float = 0.3,
    ) -> None:
        """Simulate a swipe gesture."""
        # Touch down
        await self._client.send("touch", {
            "index": 0, "x": from_x, "y": from_y, "pressed": True
        })

        # Move in steps (using drag events for touch movement isn't directly supported,
        # but we can simulate with multiple touch events)
        steps = max(int(duration * 60), 10)
        for i in range(1, steps + 1):
            t = i / steps
            x = from_x + (to_x - from_x) * t
            y = from_y + (to_y - from_y) * t
            # Keep touch pressed while moving
            await self._client.send("touch", {
                "index": 0, "x": x, "y": y, "pressed": True
            })
            await asyncio.sleep(duration / steps)

        # Touch up
        await self._client.send("touch", {
            "index": 0, "x": to_x, "y": to_y, "pressed": False
        })

    async def pinch(
        self,
        center_x: float,
        center_y: float,
        scale: float,
        duration: float = 0.3,
    ) -> None:
        """Simulate a pinch gesture.

        Uses two touch points moving toward or away from center.
        """
        # Initial distance from center
        initial_dist = 100.0
        final_dist = initial_dist * scale

        steps = max(int(duration * 60), 10)

        # Start both touch points
        await self._client.send("touch", {
            "index": 0,
            "x": center_x - initial_dist,
            "y": center_y,
            "pressed": True
        })
        await self._client.send("touch", {
            "index": 1,
            "x": center_x + initial_dist,
            "y": center_y,
            "pressed": True
        })

        # Move fingers
        for i in range(1, steps + 1):
            t = i / steps
            dist = initial_dist + (final_dist - initial_dist) * t
            await self._client.send("touch", {
                "index": 0,
                "x": center_x - dist,
                "y": center_y,
                "pressed": True
            })
            await self._client.send("touch", {
                "index": 1,
                "x": center_x + dist,
                "y": center_y,
                "pressed": True
            })
            await asyncio.sleep(duration / steps)

        # Release both
        await self._client.send("touch", {
            "index": 0,
            "x": center_x - final_dist,
            "y": center_y,
            "pressed": False
        })
        await self._client.send("touch", {
            "index": 1,
            "x": center_x + final_dist,
            "y": center_y,
            "pressed": False
        })
