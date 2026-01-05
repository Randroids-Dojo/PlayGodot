"""Native TCP server for Godot RemoteDebugger automation protocol.

Listens for Godot's debugger connection and uses the native binary
Variant serialization format instead of WebSocket + JSON-RPC.

When Godot is started with --remote-debug tcp://host:port, it connects
to an external debugger as a client. PlayGodot acts as that server.

This allows PlayGodot to work with Godot's built-in automation protocol
without requiring any addon to be installed in the game.
"""

from __future__ import annotations

import asyncio
import struct
from typing import Any

from playgodot.variant import encode_message, decode_message, decode_variant
from playgodot.exceptions import ConnectionError, CommandError, TimeoutError


class NativeClient:
    """TCP server that accepts Godot's RemoteDebugger connection.

    Despite the name 'Client', this acts as a server that Godot connects to.
    The name is kept for API compatibility with the WebSocket Client class.
    """

    def __init__(self, host: str = "localhost", port: int = 6007):
        """Initialize the native server.

        Args:
            host: The host to bind to.
            port: The debugger port (default 6007).
        """
        self.host = host
        self.port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._server: asyncio.Server | None = None
        self._pending: dict[str, asyncio.Future[Any]] = {}
        self._receive_task: asyncio.Task[None] | None = None
        self._request_id = 0
        self._connected_event: asyncio.Event | None = None
        self._godot_thread_id: int = 0  # Will be set from first received message

    @property
    def is_connected(self) -> bool:
        """Check if Godot is connected."""
        return self._writer is not None and not self._writer.is_closing()

    async def _start_server(self) -> None:
        """Start the TCP server (called before launching Godot).

        Raises:
            ConnectionError: If server fails to start.
        """
        self._connected_event = asyncio.Event()

        try:
            self._server = await asyncio.start_server(
                self._handle_connection,
                self.host,
                self.port,
            )
            print(f"[NativeClient] Listening on {self.host}:{self.port}")
        except OSError as e:
            raise ConnectionError(
                f"Failed to start server on {self.host}:{self.port}: {e}"
            )

    async def connect(self, timeout: float = 30.0) -> None:
        """Wait for Godot to connect to our server.

        If the server hasn't been started yet, starts it first.
        Also waits for the Godot thread ID to be captured from the first message.

        Args:
            timeout: Timeout waiting for Godot to connect.

        Raises:
            ConnectionError: If server fails to start or Godot doesn't connect.
        """
        # Start server if not already running
        if self._server is None:
            await self._start_server()

        # Wait for Godot to connect
        if self._connected_event is None:
            self._connected_event = asyncio.Event()

        start_time = asyncio.get_event_loop().time()
        try:
            await asyncio.wait_for(
                self._connected_event.wait(),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            raise ConnectionError(
                f"Godot did not connect to {self.host}:{self.port} within {timeout}s"
            )

        # Wait for Godot's thread ID to be captured from first message
        remaining = timeout - (asyncio.get_event_loop().time() - start_time)
        while self._godot_thread_id == 0 and remaining > 0:
            await asyncio.sleep(0.1)
            remaining = timeout - (asyncio.get_event_loop().time() - start_time)

        if self._godot_thread_id == 0:
            print("[NativeClient] Warning: Godot thread ID not captured yet")

    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Handle incoming connection from Godot."""
        print("[NativeClient] Godot connected")
        self._reader = reader
        self._writer = writer
        self._receive_task = asyncio.create_task(self._receive_loop())

        if self._connected_event:
            self._connected_event.set()

    async def disconnect(self) -> None:
        """Disconnect from Godot and stop the server."""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
            self._writer = None
            self._reader = None

        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

        # Cancel pending requests
        for future in self._pending.values():
            if not future.done():
                future.cancel()
        self._pending.clear()

    async def send(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> Any:
        """Send an automation command and wait for the response.

        This translates the WebSocket client interface to the native protocol.
        The method name is mapped to automation:command format.

        Args:
            method: The RPC method name (e.g., "get_tree", "get_node").
            params: Optional parameters (will be converted to array).
            timeout: Request timeout in seconds.

        Returns:
            The result from the response.

        Raises:
            ConnectionError: If not connected.
            TimeoutError: If request times out.
            CommandError: If the command fails.
        """
        if not self._writer or not self._reader:
            raise ConnectionError("Not connected to Godot")

        # Map method + params to automation protocol data array
        data = self._params_to_data(method, params or {})

        # Generate unique key for this request
        self._request_id += 1
        request_key = f"automation:{method}_{self._request_id}"

        # Create future for response
        future: asyncio.Future[Any] = asyncio.get_event_loop().create_future()
        expected_response = self._get_expected_response(method)
        self._pending[expected_response] = future

        try:
            # Use Godot's main thread ID (captured from first received message)
            message = encode_message(f"automation:{method}", self._godot_thread_id, data)
            print(f"[NativeClient] Sending: automation:{method} with thread_id={self._godot_thread_id}, data: {data}")
            self._writer.write(message)
            await self._writer.drain()
            print(f"[NativeClient] Waiting for response: {expected_response}")
            result = await asyncio.wait_for(future, timeout=timeout)
            print(f"[NativeClient] Received response: {result}")
            return self._data_to_result(method, result)
        except asyncio.TimeoutError:
            print(f"[NativeClient] Timeout waiting for: {expected_response}")
            print(f"[NativeClient] Pending requests: {list(self._pending.keys())}")
            raise TimeoutError(f"Request '{method}' timed out after {timeout}s")
        finally:
            self._pending.pop(expected_response, None)

    def _params_to_data(self, method: str, params: dict[str, Any]) -> list:
        """Convert JSON-RPC style params to automation protocol data array."""
        if method == "get_tree":
            return []
        elif method == "get_node":
            return [params.get("path", "")]
        elif method == "get_property":
            return [params.get("path", ""), params.get("property", "")]
        elif method == "set_property":
            return [
                params.get("path", ""),
                params.get("property", ""),
                params.get("value"),
            ]
        elif method == "call_method":
            return [
                params.get("path", ""),
                params.get("method", ""),
                params.get("args", []),
            ]
        elif method == "node_exists":
            # Use get_node and check if result is null
            return [params.get("path", "")]
        elif method == "query_nodes":
            # Not directly supported, would need custom implementation
            return [params.get("pattern", "")]
        elif method == "count_nodes":
            return [params.get("pattern", "")]
        elif method == "mouse_button":
            # mouse_button: [x, y, button_index, pressed, double_click?]
            return [
                params.get("x", 0),
                params.get("y", 0),
                params.get("button", 1),
                params.get("pressed", True),
                params.get("double_click", False),
            ]
        elif method == "mouse_motion":
            return [
                params.get("x", 0),
                params.get("y", 0),
                params.get("rel_x", 0),
                params.get("rel_y", 0),
            ]
        elif method == "key":
            return [
                params.get("keycode", 0),
                params.get("pressed", True),
                params.get("physical", False),
            ]
        elif method == "touch":
            return [
                params.get("index", 0),
                params.get("x", 0),
                params.get("y", 0),
                params.get("pressed", True),
            ]
        elif method == "action":
            return [
                params.get("action", ""),
                params.get("pressed", True),
                params.get("strength", 1.0),
            ]
        # Extended automation commands (Phase 3)
        elif method == "screenshot":
            return [params.get("node_path", "")]
        elif method == "query_nodes":
            return [params.get("pattern", "*")]
        elif method == "count_nodes":
            return [params.get("pattern", "*")]
        elif method == "get_current_scene":
            return []
        elif method == "change_scene":
            return [params.get("path", "")]
        elif method == "reload_scene":
            return []
        elif method == "pause":
            return [params.get("paused", True)]
        elif method == "time_scale":
            return [params.get("scale", 1.0)]
        elif method == "wait_signal":
            return [
                params.get("signal", ""),
                params.get("source", ""),
                params.get("timeout", 30000),
            ]
        else:
            # For unknown methods, just pass params as list
            return list(params.values()) if params else []

    def _get_expected_response(self, method: str) -> str:
        """Get the expected response message name for a method."""
        response_map = {
            "get_tree": "automation:tree",
            "get_node": "automation:node",
            "node_exists": "automation:node",
            "get_property": "automation:property",
            "set_property": "automation:set_result",
            "call_method": "automation:call_result",
            "mouse_button": "automation:input_result",
            "mouse_motion": "automation:input_result",
            "key": "automation:input_result",
            "touch": "automation:input_result",
            "action": "automation:input_result",
            # Extended automation (Phase 3)
            "screenshot": "automation:screenshot",
            "query_nodes": "automation:query_result",
            "count_nodes": "automation:count_result",
            "get_current_scene": "automation:current_scene",
            "change_scene": "automation:scene_result",
            "reload_scene": "automation:scene_result",
            "pause": "automation:pause_result",
            "time_scale": "automation:time_scale_result",
            "wait_signal": "automation:wait_signal_result",
        }
        return response_map.get(method, f"automation:{method}")

    def _data_to_result(self, method: str, data: list) -> Any:
        """Convert automation protocol response data to JSON-RPC style result."""
        if method == "get_tree":
            # Response is [tree_dict]
            return data[0] if data else {}
        elif method == "get_node":
            # Response is [node_dict or null]
            return data[0] if data else None
        elif method == "node_exists":
            # We sent get_node, check if result is not null
            return {"exists": data[0] is not None} if data else {"exists": False}
        elif method == "get_property":
            # Response is [path, property, value]
            if len(data) >= 3:
                return {"value": data[2]}
            return {"value": None}
        elif method == "set_property":
            # Response is [success]
            return {"success": bool(data[0])} if data else {"success": False}
        elif method == "call_method":
            # Response is [path, method, result]
            if len(data) >= 3:
                return {"value": data[2]}
            return {"value": None}
        elif method in ("mouse_button", "mouse_motion", "key", "touch", "action"):
            # Response is [success]
            return {"success": bool(data[0])} if data else {"success": False}
        # Extended automation (Phase 3)
        elif method == "screenshot":
            # Response is [png_bytes] - raw PNG data as PackedByteArray
            if data and len(data) >= 1:
                return {"data": data[0]}  # Raw PNG bytes
            return None
        elif method == "query_nodes":
            # Response is [array_of_node_paths]
            return data[0] if data else []
        elif method == "count_nodes":
            # Response is [count]
            return data[0] if data else 0
        elif method == "get_current_scene":
            # Response is [scene_path, scene_name]
            if len(data) >= 2:
                return {"path": data[0], "name": data[1]}
            return None
        elif method in ("change_scene", "reload_scene"):
            # Response is [success]
            return {"success": bool(data[0])} if data else {"success": False}
        elif method == "pause":
            # Response is [paused_state]
            return {"paused": bool(data[0])} if data else {"paused": False}
        elif method == "time_scale":
            # Response is [current_scale]
            return {"scale": float(data[0])} if data else {"scale": 1.0}
        elif method == "wait_signal":
            # Response is [signal_name, args_array]
            if len(data) >= 2:
                return {"signal": data[0], "args": data[1]}
            return {"signal": "", "args": []}
        else:
            return data

    async def _receive_loop(self) -> None:
        """Background task that receives and dispatches responses."""
        if not self._reader:
            return

        try:
            while True:
                # Read 4-byte size header
                size_data = await self._reader.readexactly(4)
                size = struct.unpack("<I", size_data)[0]

                # Read the variant data
                variant_data = await self._reader.readexactly(size)

                # Decode the message
                try:
                    name, thread_id, data = decode_message(variant_data)

                    # Capture the Godot main thread ID from the first message
                    if self._godot_thread_id == 0 and thread_id != 0:
                        self._godot_thread_id = thread_id
                        print(f"[NativeClient] Captured Godot thread ID: {thread_id}")

                    await self._handle_response(name, data)
                except Exception as e:
                    print(f"[NativeClient] Failed to decode message: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

        except asyncio.IncompleteReadError:
            # Connection closed
            pass
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[NativeClient] Receive loop error: {e}")

    async def _handle_response(self, name: str, data: list) -> None:
        """Handle a response message from Godot."""
        print(f"[NativeClient] Received message: {name} with data length: {len(data)}")
        # Find matching pending request
        future = self._pending.get(name)
        if future and not future.done():
            print(f"[NativeClient] Found pending request for: {name}")
            future.set_result(data)
        else:
            print(f"[NativeClient] No pending request for: {name} (pending: {list(self._pending.keys())})")
