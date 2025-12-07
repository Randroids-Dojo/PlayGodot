"""Main Godot class for game automation."""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from typing import Any, Callable, TypeVar, Union, Protocol
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from playgodot.client import Client
from playgodot.native_client import NativeClient
from playgodot.node import Node
from playgodot.input import InputSimulator
from playgodot.native_input import NativeInputSimulator
from playgodot.screenshot import ScreenshotManager
from playgodot.exceptions import ConnectionError, NodeNotFoundError, TimeoutError

T = TypeVar("T")

# Protocol type for clients (both WebSocket and Native)
ClientType = Union[Client, NativeClient]
InputType = Union[InputSimulator, NativeInputSimulator]


class Godot:
    """Main class for automating Godot games."""

    def __init__(
        self,
        client: ClientType,
        process: subprocess.Popen[bytes] | None = None,
        native: bool = False,
    ):
        """Initialize Godot automation instance.

        Args:
            client: The WebSocket or Native TCP client.
            process: Optional subprocess for the Godot process.
            native: Whether using native debugger protocol.
        """
        self._client = client
        self._process = process
        self._native = native

        if native and isinstance(client, NativeClient):
            self._input: InputType = NativeInputSimulator(client)
        else:
            self._input = InputSimulator(client)  # type: ignore[arg-type]

        # Screenshot only works with addon for now
        if isinstance(client, Client):
            self._screenshot = ScreenshotManager(client)
        else:
            self._screenshot = None  # type: ignore[assignment]

    @classmethod
    @asynccontextmanager
    async def launch(
        cls,
        project_path: str | Path,
        *,
        headless: bool = True,
        resolution: tuple[int, int] | None = None,
        port: int = 9999,
        timeout: float = 30.0,
        godot_path: str | None = None,
        verbose: bool = False,
        native: bool = False,
    ) -> AsyncGenerator[Godot, None]:
        """Launch a Godot project and connect to it.

        Args:
            project_path: Path to the Godot project directory.
            headless: Run without window (default True).
            resolution: Window resolution as (width, height).
            port: WebSocket port (default 9999) or debugger port (default 6007).
            timeout: Connection timeout in seconds.
            godot_path: Path to Godot executable (auto-detected if not provided).
            verbose: Enable verbose logging.
            native: Use native debugger protocol instead of WebSocket addon.

        Yields:
            A connected Godot instance.
        """
        project_path = Path(project_path).resolve()

        # Build command
        godot_exe = godot_path or cls._find_godot()
        cmd = [godot_exe, "--path", str(project_path)]

        if headless:
            cmd.append("--headless")

        if resolution:
            cmd.extend(["--resolution", f"{resolution[0]}x{resolution[1]}"])

        if verbose:
            cmd.append("--verbose")

        # For native protocol, enable remote debugging
        if native:
            debug_port = port if port != 9999 else 6007
            cmd.extend(["--remote-debug", f"tcp://127.0.0.1:{debug_port}"])
            print(f"[PlayGodot] Starting Godot with remote debugging on port {debug_port}")
        else:
            debug_port = port

        print(f"[PlayGodot] Starting Godot: {' '.join(cmd)}")

        client: ClientType
        process: subprocess.Popen[bytes] | None = None

        try:
            if native:
                # For native protocol: start server FIRST, then launch Godot
                # Godot will connect to us as a client
                client = NativeClient(host="127.0.0.1", port=debug_port)

                # Start listening before Godot launches
                print(f"[PlayGodot] Starting debug server on port {debug_port}...")
                await client._start_server()

                # Now launch Godot which will connect to us
                process = subprocess.Popen(cmd)

                # Wait for Godot to connect
                print(f"[PlayGodot] Waiting for Godot to connect...")
                await client.connect(timeout=timeout)
                print(f"[PlayGodot] Godot connected via native protocol")
            else:
                # For WebSocket: launch Godot first, then connect
                process = subprocess.Popen(cmd)
                client = Client(port=port)

                # Wait for Godot to start and retry connection
                connected = False
                last_error = None
                start_time = asyncio.get_event_loop().time()
                attempt = 0

                while asyncio.get_event_loop().time() - start_time < timeout:
                    # Check if process crashed
                    if process.poll() is not None:
                        raise ConnectionError(
                            f"Godot process exited with code {process.returncode}.\n"
                            f"Command: {' '.join(cmd)}\n"
                            f"Check the output above for errors."
                        )

                    try:
                        attempt += 1
                        if attempt % 10 == 1:
                            print(f"[PlayGodot] WebSocket connection attempt {attempt}...")
                        await client.connect(timeout=2.0)
                        connected = True
                        print(f"[PlayGodot] Connected after {attempt} attempts")
                        break
                    except Exception as e:
                        last_error = e
                        await asyncio.sleep(0.5)

                if not connected:
                    raise ConnectionError(
                        f"Failed to connect to Godot after {timeout}s ({attempt} attempts).\n"
                        f"Command: {' '.join(cmd)}\n"
                        f"Last error: {last_error}\n"
                        f"Process running: {process.poll() is None}\n"
                        f"Check the Godot output above for errors."
                    )

            instance = cls(client, process, native=native)
            yield instance
        finally:
            await client.disconnect()
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

    @classmethod
    async def connect(
        cls,
        host: str = "localhost",
        port: int = 9999,
        timeout: float = 30.0,
        native: bool = False,
    ) -> Godot:
        """Connect to an already-running Godot game.

        Args:
            host: The host to connect to.
            port: The WebSocket port (default 9999) or debugger port (default 6007).
            timeout: Connection timeout in seconds.
            native: Use native debugger protocol instead of WebSocket addon.

        Returns:
            A connected Godot instance.
        """
        if native:
            # Use default debug port if not specified
            actual_port = port if port != 9999 else 6007
            client: ClientType = NativeClient(host=host, port=actual_port)
        else:
            client = Client(host=host, port=port)
        await client.connect(timeout=timeout)
        return cls(client, native=native)

    async def disconnect(self) -> None:
        """Disconnect from the game."""
        await self._client.disconnect()
        if self._process and self._process.poll() is None:
            self._process.terminate()

    @staticmethod
    def _find_godot() -> str:
        """Find the Godot executable."""
        import shutil

        # Common names for Godot executable
        names = ["godot", "godot4", "Godot", "Godot4"]

        for name in names:
            path = shutil.which(name)
            if path:
                return path

        raise FileNotFoundError(
            "Godot executable not found. Please install Godot or provide godot_path."
        )

    # Node interaction

    async def get_node(self, path: str) -> Node:
        """Get a node by path.

        Args:
            path: The node path (e.g., "/root/Main/Player").

        Returns:
            A Node wrapper.

        Raises:
            NodeNotFoundError: If the node doesn't exist.
        """
        result = await self._client.send("get_node", {"path": path})
        if result is None:
            raise NodeNotFoundError(path)
        return Node(self, path, result)

    async def get_property(self, path: str, property_name: str) -> Any:
        """Get a property value from a node.

        Args:
            path: The node path.
            property_name: The property name.

        Returns:
            The property value.
        """
        result = await self._client.send(
            "get_property",
            {"path": path, "property": property_name},
        )
        return result.get("value")

    async def set_property(self, path: str, property_name: str, value: Any) -> None:
        """Set a property value on a node.

        Args:
            path: The node path.
            property_name: The property name.
            value: The value to set.
        """
        await self._client.send(
            "set_property",
            {"path": path, "property": property_name, "value": value},
        )

    async def call(
        self,
        path: str,
        method: str,
        args: list[Any] | None = None,
    ) -> Any:
        """Call a method on a node.

        Args:
            path: The node path.
            method: The method name.
            args: Optional arguments.

        Returns:
            The return value from the method.
        """
        result = await self._client.send(
            "call_method",
            {"path": path, "method": method, "args": args or []},
        )
        return result.get("value")

    async def node_exists(self, path: str) -> bool:
        """Check if a node exists.

        Args:
            path: The node path.

        Returns:
            True if the node exists.
        """
        result = await self._client.send("node_exists", {"path": path})
        return result.get("exists", False)

    async def query_nodes(self, pattern: str) -> list[Node]:
        """Query nodes matching a pattern.

        Args:
            pattern: A node path pattern (supports * wildcards).

        Returns:
            A list of matching nodes.
        """
        result = await self._client.send("query_nodes", {"pattern": pattern})
        return [
            Node(self, node["path"], node) for node in result.get("nodes", [])
        ]

    async def count_nodes(self, pattern: str) -> int:
        """Count nodes matching a pattern.

        Args:
            pattern: A node path pattern.

        Returns:
            The number of matching nodes.
        """
        result = await self._client.send("count_nodes", {"pattern": pattern})
        return result.get("count", 0)

    # Input simulation (delegates to InputSimulator)

    async def click(self, path_or_x: str | float, y: float | None = None) -> None:
        """Click on a node or at coordinates.

        Args:
            path_or_x: Node path or X coordinate.
            y: Y coordinate (required if path_or_x is a coordinate).
        """
        if isinstance(path_or_x, str):
            await self._input.click_node(path_or_x)
        else:
            if y is None:
                raise ValueError("Y coordinate required when clicking by position")
            await self._input.click(path_or_x, y)

    async def click_position(self, x: float, y: float) -> None:
        """Click at coordinates."""
        await self._input.click(x, y)

    async def double_click(self, path_or_x: str | float, y: float | None = None) -> None:
        """Double-click on a node or at coordinates."""
        if isinstance(path_or_x, str):
            await self._input.double_click_node(path_or_x)
        else:
            if y is None:
                raise ValueError("Y coordinate required")
            await self._input.double_click(path_or_x, y)

    async def right_click(self, path_or_x: str | float, y: float | None = None) -> None:
        """Right-click on a node or at coordinates."""
        if isinstance(path_or_x, str):
            await self._input.right_click_node(path_or_x)
        else:
            if y is None:
                raise ValueError("Y coordinate required")
            await self._input.right_click(path_or_x, y)

    async def drag(
        self,
        from_path: str,
        to_path: str,
        duration: float = 0.5,
    ) -> None:
        """Drag from one node to another."""
        await self._input.drag_node(from_path, to_path, duration)

    async def move_mouse(self, x: float, y: float) -> None:
        """Move mouse to coordinates."""
        await self._input.move_mouse(x, y)

    async def press_key(self, key: str) -> None:
        """Press a key.

        Args:
            key: Key specification (e.g., "space", "ctrl+s").
        """
        if "+" in key:
            parts = key.split("+")
            modifiers = parts[:-1]
            key = parts[-1]
            await self._input.press_key(key, modifiers)
        else:
            await self._input.press_key(key)

    async def type_text(self, text: str) -> None:
        """Type a string of text."""
        await self._input.type_text(text)

    async def press_action(self, action: str) -> None:
        """Press an input action."""
        await self._input.press_action(action)

    async def hold_action(self, action: str, duration: float) -> None:
        """Hold an input action."""
        await self._input.hold_action(action, duration)

    async def tap(self, x: float, y: float) -> None:
        """Tap at coordinates (touch)."""
        await self._input.tap(x, y)

    async def swipe(
        self,
        from_x: float,
        from_y: float,
        to_x: float,
        to_y: float,
    ) -> None:
        """Swipe gesture."""
        await self._input.swipe(from_x, from_y, to_x, to_y)

    async def pinch(
        self,
        center: tuple[float, float],
        scale: float,
    ) -> None:
        """Pinch gesture."""
        await self._input.pinch(center[0], center[1], scale)

    # Waiting

    async def wait_for_node(self, path: str, timeout: float = 5.0) -> Node:
        """Wait for a node to exist.

        Args:
            path: The node path.
            timeout: Timeout in seconds.

        Returns:
            The node once it exists.

        Raises:
            TimeoutError: If the node doesn't appear in time.
        """
        return await self._wait_for(
            lambda: self.get_node(path),
            timeout=timeout,
            message=f"Node '{path}' not found",
        )

    async def wait_for_visible(self, path: str, timeout: float = 5.0) -> None:
        """Wait for a node to be visible.

        Args:
            path: The node path.
            timeout: Timeout in seconds.
        """

        async def check_visible() -> bool:
            try:
                visible = await self.get_property(path, "visible")
                return bool(visible)
            except NodeNotFoundError:
                return False

        await self._wait_for(
            check_visible,
            timeout=timeout,
            expected=True,
            message=f"Node '{path}' not visible",
        )

    async def wait_for_signal(
        self,
        signal_name: str,
        source: str | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Wait for a signal to be emitted.

        Args:
            signal_name: The signal name.
            source: Optional source node path.
            timeout: Timeout in seconds.

        Returns:
            Signal data including any arguments.
        """
        params: dict[str, Any] = {"signal": signal_name, "timeout": timeout * 1000}
        if source:
            params["source"] = source

        result = await self._client.send("wait_signal", params, timeout=timeout + 5)
        return result

    async def wait_for(
        self,
        condition: Callable[[], Any],
        timeout: float = 10.0,
        interval: float = 0.1,
    ) -> Any:
        """Wait for a condition to be truthy.

        Args:
            condition: A callable that returns a truthy value when satisfied.
            timeout: Timeout in seconds.
            interval: Polling interval in seconds.

        Returns:
            The truthy value from the condition.
        """
        return await self._wait_for(
            condition,
            timeout=timeout,
            interval=interval,
        )

    async def wait_frames(self, count: int) -> None:
        """Wait for a number of frames.

        Args:
            count: Number of frames to wait.
        """
        await self._client.send("wait_frames", {"count": count})

    async def wait_seconds(self, seconds: float) -> None:
        """Wait for a number of seconds (game time).

        Args:
            seconds: Seconds to wait.
        """
        await self._client.send("wait_seconds", {"seconds": seconds})

    async def _wait_for(
        self,
        fn: Callable[[], Any],
        timeout: float = 5.0,
        interval: float = 0.1,
        expected: Any = None,
        message: str | None = None,
    ) -> Any:
        """Internal wait helper."""
        start = asyncio.get_event_loop().time()

        while True:
            try:
                result = fn()
                if asyncio.iscoroutine(result):
                    result = await result

                if expected is not None:
                    if result == expected:
                        return result
                elif result:
                    return result
            except (NodeNotFoundError, Exception):
                pass

            elapsed = asyncio.get_event_loop().time() - start
            if elapsed >= timeout:
                raise TimeoutError(
                    message or f"Condition not met within {timeout}s"
                )

            await asyncio.sleep(interval)

    # Screenshots

    async def screenshot(
        self,
        path: str | None = None,
        node: str | None = None,
    ) -> bytes:
        """Take a screenshot.

        Args:
            path: Optional file path to save.
            node: Optional node to screenshot.

        Returns:
            PNG image bytes.

        Raises:
            NotImplementedError: If using native protocol (screenshots not supported).
        """
        if self._screenshot is None:
            raise NotImplementedError(
                "Screenshots are not supported with the native debugger protocol. "
                "Use the WebSocket addon protocol for screenshot functionality."
            )
        return await self._screenshot.capture(path, node)

    async def compare_screenshot(
        self,
        expected: str,
        actual: str | None = None,
    ) -> float:
        """Compare screenshots."""
        if self._screenshot is None:
            raise NotImplementedError(
                "Screenshots are not supported with the native debugger protocol."
            )
        return await self._screenshot.compare(expected, actual)

    async def assert_screenshot(
        self,
        reference: str,
        threshold: float = 0.99,
    ) -> None:
        """Assert screenshot matches reference."""
        if self._screenshot is None:
            raise NotImplementedError(
                "Screenshots are not supported with the native debugger protocol."
            )
        await self._screenshot.assert_matches(reference, threshold)

    # Scene management

    async def get_current_scene(self) -> str:
        """Get the current scene path.

        Returns:
            The resource path of the current scene.
        """
        result = await self._client.send("get_current_scene")
        return result.get("path", "")

    async def change_scene(self, scene_path: str) -> None:
        """Change to a different scene.

        Args:
            scene_path: The resource path of the scene.
        """
        await self._client.send("change_scene", {"path": scene_path})

    async def reload_scene(self) -> None:
        """Reload the current scene."""
        await self._client.send("reload_scene")

    async def get_tree(self) -> dict[str, Any]:
        """Get the scene tree structure.

        Returns:
            A hierarchical representation of the scene tree.
        """
        result = await self._client.send("get_tree")
        return result

    # Game state

    async def pause(self) -> None:
        """Pause the game."""
        await self._client.send("pause")

    async def unpause(self) -> None:
        """Unpause the game."""
        await self._client.send("unpause")

    async def set_time_scale(self, scale: float) -> None:
        """Set the game time scale.

        Args:
            scale: Time scale (1.0 = normal, 0.5 = half speed, etc.).
        """
        await self._client.send("set_time_scale", {"scale": scale})
