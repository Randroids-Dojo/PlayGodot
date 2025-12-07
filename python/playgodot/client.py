"""WebSocket client for communicating with Godot."""

from __future__ import annotations

import asyncio
import json
from typing import Any, TYPE_CHECKING

import websockets

if TYPE_CHECKING:
    from websockets.asyncio.client import ClientConnection

from playgodot.exceptions import ConnectionError, CommandError, TimeoutError


class Client:
    """WebSocket client that communicates with the PlayGodot addon in Godot."""

    def __init__(self, host: str = "localhost", port: int = 9999):
        self.host = host
        self.port = port
        self._ws: ClientConnection | None = None
        self._request_id = 0
        self._pending_requests: dict[int, asyncio.Future[Any]] = {}
        self._receive_task: asyncio.Task[None] | None = None

    @property
    def url(self) -> str:
        """Get the WebSocket URL."""
        return f"ws://{self.host}:{self.port}"

    async def connect(self, timeout: float = 30.0) -> None:
        """Connect to the Godot WebSocket server.

        Args:
            timeout: Connection timeout in seconds.

        Raises:
            ConnectionError: If connection fails.
        """
        try:
            self._ws = await asyncio.wait_for(
                websockets.connect(self.url),
                timeout=timeout,
            )
            self._receive_task = asyncio.create_task(self._receive_loop())
        except asyncio.TimeoutError:
            raise ConnectionError(f"Connection to {self.url} timed out after {timeout}s")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.url}: {e}")

    async def disconnect(self) -> None:
        """Disconnect from the Godot WebSocket server."""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        if self._ws:
            await self._ws.close()
            self._ws = None

        # Cancel any pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()

    async def send(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> Any:
        """Send a JSON-RPC request and wait for the response.

        Args:
            method: The RPC method name.
            params: Optional parameters for the method.
            timeout: Request timeout in seconds.

        Returns:
            The result from the response.

        Raises:
            ConnectionError: If not connected.
            TimeoutError: If request times out.
            CommandError: If the command fails on the Godot side.
        """
        if not self._ws:
            raise ConnectionError("Not connected to Godot")

        self._request_id += 1
        request_id = self._request_id

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params:
            request["params"] = params

        # Create a future for the response
        future: asyncio.Future[Any] = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future

        try:
            await self._ws.send(json.dumps(request))
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request '{method}' timed out after {timeout}s")
        finally:
            self._pending_requests.pop(request_id, None)

    async def _receive_loop(self) -> None:
        """Background task that receives and dispatches responses."""
        if not self._ws:
            return

        try:
            async for message in self._ws:
                try:
                    data = json.loads(message)
                    await self._handle_response(data)
                except json.JSONDecodeError:
                    continue
        except websockets.exceptions.ConnectionClosed:
            pass

    async def _handle_response(self, data: dict[str, Any]) -> None:
        """Handle a JSON-RPC response."""
        request_id = data.get("id")
        if request_id is None:
            # This might be a notification, ignore for now
            return

        future = self._pending_requests.get(request_id)
        if not future or future.done():
            return

        if "error" in data:
            error = data["error"]
            future.set_exception(
                CommandError(
                    method="unknown",
                    message=error.get("message", "Unknown error"),
                    code=error.get("code"),
                )
            )
        else:
            future.set_result(data.get("result"))

    @property
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return self._ws is not None and self._ws.open
