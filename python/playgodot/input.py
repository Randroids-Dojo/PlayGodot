"""Input simulation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playgodot.client import Client


@dataclass
class MousePosition:
    """Represents a mouse position."""

    x: float
    y: float


class InputSimulator:
    """Handles input simulation commands."""

    def __init__(self, client: Client):
        self._client = client

    async def click(self, x: float, y: float, button: str = "left") -> None:
        """Simulate a mouse click at coordinates.

        Args:
            x: X coordinate.
            y: Y coordinate.
            button: Mouse button ("left", "right", "middle").
        """
        await self._client.send(
            "click",
            {"x": x, "y": y, "button": button},
        )

    async def click_node(self, path: str, button: str = "left") -> None:
        """Simulate a mouse click on a node.

        Args:
            path: The node path.
            button: Mouse button ("left", "right", "middle").
        """
        await self._client.send(
            "click_node",
            {"path": path, "button": button},
        )

    async def double_click(self, x: float, y: float) -> None:
        """Simulate a double-click at coordinates.

        Args:
            x: X coordinate.
            y: Y coordinate.
        """
        await self._client.send(
            "double_click",
            {"x": x, "y": y},
        )

    async def double_click_node(self, path: str) -> None:
        """Simulate a double-click on a node.

        Args:
            path: The node path.
        """
        await self._client.send(
            "double_click_node",
            {"path": path},
        )

    async def right_click(self, x: float, y: float) -> None:
        """Simulate a right-click at coordinates.

        Args:
            x: X coordinate.
            y: Y coordinate.
        """
        await self.click(x, y, button="right")

    async def right_click_node(self, path: str) -> None:
        """Simulate a right-click on a node.

        Args:
            path: The node path.
        """
        await self.click_node(path, button="right")

    async def move_mouse(self, x: float, y: float) -> None:
        """Move the mouse to coordinates.

        Args:
            x: X coordinate.
            y: Y coordinate.
        """
        await self._client.send(
            "move_mouse",
            {"x": x, "y": y},
        )

    async def drag(
        self,
        from_x: float,
        from_y: float,
        to_x: float,
        to_y: float,
        duration: float = 0.5,
    ) -> None:
        """Simulate a drag operation.

        Args:
            from_x: Starting X coordinate.
            from_y: Starting Y coordinate.
            to_x: Ending X coordinate.
            to_y: Ending Y coordinate.
            duration: Drag duration in seconds.
        """
        await self._client.send(
            "drag",
            {
                "from_x": from_x,
                "from_y": from_y,
                "to_x": to_x,
                "to_y": to_y,
                "duration": duration,
            },
        )

    async def drag_node(self, from_path: str, to_path: str, duration: float = 0.5) -> None:
        """Simulate dragging from one node to another.

        Args:
            from_path: Source node path.
            to_path: Target node path.
            duration: Drag duration in seconds.
        """
        await self._client.send(
            "drag_node",
            {
                "from_path": from_path,
                "to_path": to_path,
                "duration": duration,
            },
        )

    async def press_key(self, key: str, modifiers: list[str] | None = None) -> None:
        """Simulate a key press.

        Args:
            key: The key to press (e.g., "space", "enter", "a").
            modifiers: Optional modifiers (e.g., ["ctrl", "shift"]).
        """
        await self._client.send(
            "press_key",
            {"key": key, "modifiers": modifiers or []},
        )

    async def type_text(self, text: str, delay: float = 0.05) -> None:
        """Type a string of text.

        Args:
            text: The text to type.
            delay: Delay between keystrokes in seconds.
        """
        await self._client.send(
            "type_text",
            {"text": text, "delay": delay},
        )

    async def press_action(self, action: str) -> None:
        """Press an input action.

        Args:
            action: The action name (as defined in Input Map).
        """
        await self._client.send(
            "press_action",
            {"action": action},
        )

    async def hold_action(self, action: str, duration: float) -> None:
        """Hold an input action for a duration.

        Args:
            action: The action name.
            duration: Duration to hold in seconds.
        """
        await self._client.send(
            "hold_action",
            {"action": action, "duration": duration},
        )

    async def release_action(self, action: str) -> None:
        """Release an input action.

        Args:
            action: The action name.
        """
        await self._client.send(
            "release_action",
            {"action": action},
        )

    # Touch input methods

    async def tap(self, x: float, y: float) -> None:
        """Simulate a touch tap.

        Args:
            x: X coordinate.
            y: Y coordinate.
        """
        await self._client.send(
            "tap",
            {"x": x, "y": y},
        )

    async def swipe(
        self,
        from_x: float,
        from_y: float,
        to_x: float,
        to_y: float,
        duration: float = 0.3,
    ) -> None:
        """Simulate a swipe gesture.

        Args:
            from_x: Starting X coordinate.
            from_y: Starting Y coordinate.
            to_x: Ending X coordinate.
            to_y: Ending Y coordinate.
            duration: Swipe duration in seconds.
        """
        await self._client.send(
            "swipe",
            {
                "from_x": from_x,
                "from_y": from_y,
                "to_x": to_x,
                "to_y": to_y,
                "duration": duration,
            },
        )

    async def pinch(
        self,
        center_x: float,
        center_y: float,
        scale: float,
        duration: float = 0.3,
    ) -> None:
        """Simulate a pinch gesture.

        Args:
            center_x: Center X coordinate.
            center_y: Center Y coordinate.
            scale: Scale factor (< 1 for pinch in, > 1 for pinch out).
            duration: Gesture duration in seconds.
        """
        await self._client.send(
            "pinch",
            {
                "center_x": center_x,
                "center_y": center_y,
                "scale": scale,
                "duration": duration,
            },
        )
