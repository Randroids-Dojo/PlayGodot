"""Main Godot class for game automation.

Uses Godot's native RemoteDebugger protocol for automation.
"""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from typing import Any, Callable, TypeVar
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from playgodot.native_client import NativeClient
from playgodot.node import Node
from playgodot.native_input import NativeInputSimulator
from playgodot.exceptions import ConnectionError, NodeNotFoundError, TimeoutError

T = TypeVar("T")


class Godot:
    """Main class for automating Godot games.

    Uses Godot's native RemoteDebugger protocol for all communication.
    Requires a Godot build with automation support.
    """

    def __init__(
        self,
        client: NativeClient,
        process: subprocess.Popen[bytes] | None = None,
    ):
        """Initialize Godot automation instance.

        Args:
            client: The native TCP client.
            process: Optional subprocess for the Godot process.
        """
        self._client = client
        self._process = process
        self._input = NativeInputSimulator(client)

    @classmethod
    @asynccontextmanager
    async def launch(
        cls,
        project_path: str | Path,
        *,
        headless: bool = True,
        resolution: tuple[int, int] | None = None,
        port: int = 6007,
        timeout: float = 30.0,
        godot_path: str | None = None,
        verbose: bool = False,
    ) -> AsyncGenerator[Godot, None]:
        """Launch a Godot project and connect to it.

        Args:
            project_path: Path to the Godot project directory.
            headless: Run without window (default True).
            resolution: Window resolution as (width, height).
            port: Debugger port (default 6007).
            timeout: Connection timeout in seconds.
            godot_path: Path to Godot executable (auto-detected if not provided).
            verbose: Enable verbose logging.

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

        # Enable remote debugging
        cmd.extend(["--remote-debug", f"tcp://127.0.0.1:{port}"])
        print(f"[PlayGodot] Starting Godot with remote debugging on port {port}")
        print(f"[PlayGodot] Command: {' '.join(cmd)}")

        client = NativeClient(host="127.0.0.1", port=port)
        process: subprocess.Popen[bytes] | None = None

        try:
            # Start listening before Godot launches
            print(f"[PlayGodot] Starting debug server on port {port}...")
            await client._start_server()

            # Launch Godot which will connect to us
            process = subprocess.Popen(cmd)

            # Wait for Godot to connect
            print(f"[PlayGodot] Waiting for Godot to connect...")
            await client.connect(timeout=timeout)
            print(f"[PlayGodot] Godot connected")

            instance = cls(client, process)
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
        port: int = 6007,
        timeout: float = 30.0,
    ) -> Godot:
        """Connect to an already-running Godot game.

        Args:
            host: The host to connect to.
            port: The debugger port (default 6007).
            timeout: Connection timeout in seconds.

        Returns:
            A connected Godot instance.
        """
        client = NativeClient(host=host, port=port)
        await client.connect(timeout=timeout)
        return cls(client)

    async def disconnect(self) -> None:
        """Disconnect from the game."""
        await self._client.disconnect()
        if self._process and self._process.poll() is None:
            self._process.terminate()

    @staticmethod
    def _find_godot() -> str:
        """Find the Godot executable."""
        import shutil

        # Common names for Godot executable (including fork)
        names = ["godot-fork", "godot", "godot4", "Godot", "Godot4"]

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
        try:
            result = await self._client.send("get_node", {"path": path})
            return result is not None
        except NodeNotFoundError:
            return False

    async def query_nodes(self, pattern: str) -> list[str]:
        """Query node paths matching a pattern.

        Args:
            pattern: A node path pattern (supports * wildcards).

        Returns:
            A list of matching node paths.
        """
        result = await self._client.send("query_nodes", {"pattern": pattern})
        return result if isinstance(result, list) else []

    async def count_nodes(self, pattern: str) -> int:
        """Count nodes matching a pattern.

        Args:
            pattern: A node path pattern.

        Returns:
            The number of matching nodes.
        """
        result = await self._client.send("count_nodes", {"pattern": pattern})
        return result if isinstance(result, int) else 0

    # Input simulation

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

    async def wait_for_signal(
        self,
        signal_name: str,
        source: str | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Wait for a Godot signal to be emitted.

        Args:
            signal_name: The name of the signal to wait for.
            source: Optional node path to filter signal source.
            timeout: Timeout in seconds (default 30.0).

        Returns:
            Dict with 'signal' name and 'args' list of signal arguments.

        Raises:
            TimeoutError: If the signal is not emitted within the timeout.
        """
        result = await self._client.send(
            "wait_signal",
            {
                "signal": signal_name,
                "source": source or "",
                "timeout": int(timeout * 1000),  # Convert to milliseconds
            },
            timeout=timeout + 5.0,  # Add buffer for network overhead
        )
        return result

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
        """
        result = await self._client.send("screenshot", {"node_path": node or ""})
        if result is None:
            raise RuntimeError("Failed to take screenshot")
        png_data = result["data"]  # Already raw bytes from PackedByteArray
        if path:
            with open(path, "wb") as f:
                f.write(png_data)
        return png_data

    async def compare_screenshot(
        self,
        expected: str | bytes,
        actual: bytes | None = None,
    ) -> float:
        """Compare current screenshot to expected image.

        Uses mean squared error to calculate similarity.

        Args:
            expected: Path to expected image file or raw image bytes.
            actual: Optional actual screenshot bytes. If None, takes a new screenshot.

        Returns:
            Similarity score from 0.0 (completely different) to 1.0 (identical).

        Raises:
            FileNotFoundError: If expected image file doesn't exist.
            ValueError: If images have different dimensions.
        """
        from PIL import Image
        import io

        # Get actual screenshot
        if actual is None:
            actual = await self.screenshot()

        # Load expected image
        if isinstance(expected, str):
            expected_path = Path(expected)
            if not expected_path.exists():
                raise FileNotFoundError(f"Expected image not found: {expected}")
            expected_img = Image.open(expected_path)
        else:
            expected_img = Image.open(io.BytesIO(expected))

        # Load actual image
        actual_img = Image.open(io.BytesIO(actual))

        # Validate dimensions match
        if expected_img.size != actual_img.size:
            raise ValueError(
                f"Image dimensions don't match: expected {expected_img.size}, "
                f"actual {actual_img.size}"
            )

        # Convert to same mode (RGBA for consistency)
        expected_img = expected_img.convert("RGBA")
        actual_img = actual_img.convert("RGBA")

        # Calculate similarity
        return self._calculate_image_similarity(expected_img, actual_img)

    def _calculate_image_similarity(
        self,
        img1: Any,  # PIL.Image.Image
        img2: Any,  # PIL.Image.Image
    ) -> float:
        """Calculate similarity between two PIL Images using MSE.

        Args:
            img1: First image.
            img2: Second image.

        Returns:
            Similarity score from 0.0 to 1.0.
        """
        import numpy as np

        # Convert to numpy arrays
        arr1 = np.array(img1, dtype=np.float64)
        arr2 = np.array(img2, dtype=np.float64)

        # Calculate mean squared error
        mse = np.mean((arr1 - arr2) ** 2)

        # Convert MSE to similarity score (0-1)
        # Max possible MSE is 255^2 = 65025 per channel
        max_mse = 255.0 ** 2
        similarity = 1.0 - (mse / max_mse)

        return max(0.0, min(1.0, similarity))

    async def assert_screenshot(
        self,
        reference: str,
        threshold: float = 0.99,
        save_diff: str | None = None,
    ) -> None:
        """Assert current screenshot matches reference within threshold.

        Args:
            reference: Path to reference image file.
            threshold: Minimum similarity threshold (default 0.99 = 99% similar).
            save_diff: Optional path to save diff image on failure.

        Raises:
            AssertionError: If similarity is below threshold.
            FileNotFoundError: If reference image doesn't exist.
        """
        actual = await self.screenshot()
        similarity = await self.compare_screenshot(reference, actual)

        if similarity < threshold:
            # Save the actual screenshot for debugging
            actual_path = Path(reference).with_suffix(".actual.png")
            with open(actual_path, "wb") as f:
                f.write(actual)

            # Optionally generate and save diff image
            if save_diff:
                await self._save_diff_image(reference, actual, save_diff)

            raise AssertionError(
                f"Screenshot assertion failed: similarity {similarity:.4f} "
                f"is below threshold {threshold:.4f}. "
                f"Actual screenshot saved to: {actual_path}"
            )

    async def _save_diff_image(
        self,
        reference_path: str,
        actual_bytes: bytes,
        diff_path: str,
    ) -> None:
        """Generate and save a diff image highlighting differences.

        Args:
            reference_path: Path to reference image.
            actual_bytes: Actual screenshot bytes.
            diff_path: Path to save diff image.
        """
        from PIL import Image, ImageChops
        import io

        reference_img = Image.open(reference_path).convert("RGBA")
        actual_img = Image.open(io.BytesIO(actual_bytes)).convert("RGBA")

        # Create diff image
        diff = ImageChops.difference(reference_img, actual_img)

        # Amplify differences for visibility
        diff = diff.point(lambda x: min(255, x * 3))

        diff.save(diff_path)

    # Scene management

    async def get_current_scene(self) -> dict[str, str]:
        """Get the current scene info.

        Returns:
            Dict with 'path' and 'name' of the current scene.
        """
        result = await self._client.send("get_current_scene")
        return result if result else {"path": "", "name": ""}

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
        await self._client.send("pause", {"paused": True})

    async def unpause(self) -> None:
        """Unpause the game."""
        await self._client.send("pause", {"paused": False})

    async def is_paused(self) -> bool:
        """Check if the game is paused.

        Returns:
            True if game is paused.
        """
        result = await self._client.send("pause", {"paused": None})
        return result.get("paused", False)

    async def set_time_scale(self, scale: float) -> None:
        """Set the game time scale.

        Args:
            scale: Time scale (1.0 = normal, 0.5 = half speed, etc.).
        """
        await self._client.send("time_scale", {"scale": scale})

    async def get_time_scale(self) -> float:
        """Get the current game time scale.

        Returns:
            The current time scale.
        """
        result = await self._client.send("time_scale", {"scale": None})
        return result.get("scale", 1.0)
