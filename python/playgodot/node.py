"""Node wrapper for interacting with Godot nodes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playgodot.godot import Godot


class Node:
    """Wrapper for a Godot node, providing convenient access to properties and methods."""

    def __init__(self, godot: Godot, path: str, data: dict[str, Any] | None = None):
        """Initialize a Node wrapper.

        Args:
            godot: The Godot instance this node belongs to.
            path: The node path in the scene tree.
            data: Optional node data from the server.
        """
        self._godot = godot
        self._path = path
        self._data = data or {}

    @property
    def path(self) -> str:
        """Get the node path."""
        return self._path

    @property
    def class_name(self) -> str:
        """Get the node's class name."""
        return self._data.get("class", "")

    @property
    def name(self) -> str:
        """Get the node's name."""
        return self._data.get("name", self._path.split("/")[-1])

    async def get_property(self, property_name: str) -> Any:
        """Get a property value from this node.

        Args:
            property_name: The property name.

        Returns:
            The property value.
        """
        return await self._godot.get_property(self._path, property_name)

    async def set_property(self, property_name: str, value: Any) -> None:
        """Set a property value on this node.

        Args:
            property_name: The property name.
            value: The value to set.
        """
        await self._godot.set_property(self._path, property_name, value)

    async def call(self, method: str, args: list[Any] | None = None) -> Any:
        """Call a method on this node.

        Args:
            method: The method name.
            args: Optional arguments for the method.

        Returns:
            The return value from the method.
        """
        return await self._godot.call(self._path, method, args)

    async def click(self) -> None:
        """Click on this node (for Control nodes)."""
        await self._godot.click(self._path)

    async def double_click(self) -> None:
        """Double-click on this node."""
        await self._godot.double_click(self._path)

    async def is_visible(self) -> bool:
        """Check if this node is visible.

        Returns:
            True if the node is visible.
        """
        return await self._godot.get_property(self._path, "visible")

    async def get_children(self) -> list[Node]:
        """Get all child nodes.

        Returns:
            A list of child Node wrappers.
        """
        result = await self._godot._client.send(
            "get_children",
            {"path": self._path},
        )
        return [
            Node(self._godot, child["path"], child)
            for child in result.get("children", [])
        ]

    def __repr__(self) -> str:
        """Get string representation."""
        class_name = self.class_name or "Node"
        return f"<Node {class_name} path='{self._path}'>"
