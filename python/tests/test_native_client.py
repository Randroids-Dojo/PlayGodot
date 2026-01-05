"""Tests for NativeClient protocol handling."""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from playgodot.native_client import NativeClient
from playgodot.exceptions import ConnectionError, TimeoutError


class TestNativeClientInit:
    """Tests for NativeClient initialization."""

    def test_default_host_port(self) -> None:
        client = NativeClient()
        assert client.host == "localhost"
        assert client.port == 6007

    def test_custom_host_port(self) -> None:
        client = NativeClient(host="192.168.1.1", port=9999)
        assert client.host == "192.168.1.1"
        assert client.port == 9999

    def test_not_connected_by_default(self) -> None:
        client = NativeClient()
        assert client.is_connected is False

    def test_initial_pending_empty(self) -> None:
        client = NativeClient()
        assert client._pending == {}

    def test_initial_request_id_zero(self) -> None:
        client = NativeClient()
        assert client._request_id == 0

    def test_initial_godot_thread_id_zero(self) -> None:
        client = NativeClient()
        assert client._godot_thread_id == 0


class TestParamsToData:
    """Tests for _params_to_data method."""

    def setup_method(self) -> None:
        self.client = NativeClient()

    def test_params_get_tree(self) -> None:
        result = self.client._params_to_data("get_tree", {})
        assert result == []

    def test_params_get_node(self) -> None:
        result = self.client._params_to_data("get_node", {"path": "/root/Main"})
        assert result == ["/root/Main"]

    def test_params_get_property(self) -> None:
        result = self.client._params_to_data("get_property", {"path": "/root/Main", "property": "score"})
        assert result == ["/root/Main", "score"]

    def test_params_set_property(self) -> None:
        result = self.client._params_to_data("set_property", {
            "path": "/root/Main",
            "property": "score",
            "value": 100,
        })
        assert result == ["/root/Main", "score", 100]

    def test_params_call_method(self) -> None:
        result = self.client._params_to_data("call_method", {
            "path": "/root/Main",
            "method": "add_score",
            "args": [10],
        })
        assert result == ["/root/Main", "add_score", [10]]

    def test_params_mouse_button(self) -> None:
        result = self.client._params_to_data("mouse_button", {
            "x": 100,
            "y": 200,
            "button": 1,
            "pressed": True,
            "double_click": False,
        })
        assert result == [100, 200, 1, True, False]

    def test_params_mouse_motion(self) -> None:
        result = self.client._params_to_data("mouse_motion", {
            "x": 100,
            "y": 200,
            "rel_x": 10,
            "rel_y": 20,
        })
        assert result == [100, 200, 10, 20]

    def test_params_key(self) -> None:
        result = self.client._params_to_data("key", {
            "keycode": 65,
            "pressed": True,
            "physical": False,
        })
        assert result == [65, True, False]

    def test_params_touch(self) -> None:
        result = self.client._params_to_data("touch", {
            "index": 0,
            "x": 100,
            "y": 200,
            "pressed": True,
        })
        assert result == [0, 100, 200, True]

    def test_params_action(self) -> None:
        result = self.client._params_to_data("action", {
            "action": "ui_accept",
            "pressed": True,
            "strength": 1.0,
        })
        assert result == ["ui_accept", True, 1.0]

    def test_params_screenshot(self) -> None:
        result = self.client._params_to_data("screenshot", {"node_path": "/root/Main"})
        assert result == ["/root/Main"]

    def test_params_query_nodes(self) -> None:
        result = self.client._params_to_data("query_nodes", {"pattern": "/root/*"})
        assert result == ["/root/*"]

    def test_params_count_nodes(self) -> None:
        result = self.client._params_to_data("count_nodes", {"pattern": "/root/*"})
        assert result == ["/root/*"]

    def test_params_get_current_scene(self) -> None:
        result = self.client._params_to_data("get_current_scene", {})
        assert result == []

    def test_params_change_scene(self) -> None:
        result = self.client._params_to_data("change_scene", {"path": "res://level2.tscn"})
        assert result == ["res://level2.tscn"]

    def test_params_reload_scene(self) -> None:
        result = self.client._params_to_data("reload_scene", {})
        assert result == []

    def test_params_pause(self) -> None:
        result = self.client._params_to_data("pause", {"paused": True})
        assert result == [True]

    def test_params_time_scale(self) -> None:
        result = self.client._params_to_data("time_scale", {"scale": 2.0})
        assert result == [2.0]

    def test_params_wait_signal(self) -> None:
        result = self.client._params_to_data("wait_signal", {
            "signal": "pressed",
            "source": "/root/Button",
            "timeout": 5000,
        })
        assert result == ["pressed", "/root/Button", 5000]

    def test_params_unknown_method(self) -> None:
        result = self.client._params_to_data("unknown", {"a": 1, "b": 2})
        assert result == [1, 2]


class TestGetExpectedResponse:
    """Tests for _get_expected_response method."""

    def setup_method(self) -> None:
        self.client = NativeClient()

    def test_expected_response_get_tree(self) -> None:
        assert self.client._get_expected_response("get_tree") == "automation:tree"

    def test_expected_response_get_node(self) -> None:
        assert self.client._get_expected_response("get_node") == "automation:node"

    def test_expected_response_get_property(self) -> None:
        assert self.client._get_expected_response("get_property") == "automation:property"

    def test_expected_response_set_property(self) -> None:
        assert self.client._get_expected_response("set_property") == "automation:set_result"

    def test_expected_response_call_method(self) -> None:
        assert self.client._get_expected_response("call_method") == "automation:call_result"

    def test_expected_response_mouse_button(self) -> None:
        assert self.client._get_expected_response("mouse_button") == "automation:input_result"

    def test_expected_response_screenshot(self) -> None:
        assert self.client._get_expected_response("screenshot") == "automation:screenshot"

    def test_expected_response_query_nodes(self) -> None:
        assert self.client._get_expected_response("query_nodes") == "automation:query_result"

    def test_expected_response_pause(self) -> None:
        assert self.client._get_expected_response("pause") == "automation:pause_result"

    def test_expected_response_wait_signal(self) -> None:
        assert self.client._get_expected_response("wait_signal") == "automation:wait_signal_result"

    def test_expected_response_unknown(self) -> None:
        assert self.client._get_expected_response("custom") == "automation:custom"


class TestDataToResult:
    """Tests for _data_to_result method."""

    def setup_method(self) -> None:
        self.client = NativeClient()

    def test_data_get_tree(self) -> None:
        data = [{"name": "root", "children": []}]
        result = self.client._data_to_result("get_tree", data)
        assert result == {"name": "root", "children": []}

    def test_data_get_node(self) -> None:
        data = [{"path": "/root/Main", "class": "Node2D"}]
        result = self.client._data_to_result("get_node", data)
        assert result == {"path": "/root/Main", "class": "Node2D"}

    def test_data_get_node_null(self) -> None:
        result = self.client._data_to_result("get_node", [])
        assert result is None

    def test_data_get_property(self) -> None:
        data = ["/root/Main", "score", 42]
        result = self.client._data_to_result("get_property", data)
        assert result == {"value": 42}

    def test_data_set_property(self) -> None:
        result = self.client._data_to_result("set_property", [True])
        assert result == {"success": True}

    def test_data_call_method(self) -> None:
        data = ["/root/Main", "add", 15]
        result = self.client._data_to_result("call_method", data)
        assert result == {"value": 15}

    def test_data_input_result(self) -> None:
        result = self.client._data_to_result("mouse_button", [True])
        assert result == {"success": True}

    def test_data_screenshot(self) -> None:
        png_data = b"\x89PNG..."
        result = self.client._data_to_result("screenshot", [png_data])
        assert result == {"data": png_data}

    def test_data_query_nodes(self) -> None:
        paths = ["/root/A", "/root/B"]
        result = self.client._data_to_result("query_nodes", [paths])
        assert result == paths

    def test_data_count_nodes(self) -> None:
        result = self.client._data_to_result("count_nodes", [5])
        assert result == 5

    def test_data_get_current_scene(self) -> None:
        result = self.client._data_to_result("get_current_scene", ["res://main.tscn", "Main"])
        assert result == {"path": "res://main.tscn", "name": "Main"}

    def test_data_change_scene(self) -> None:
        result = self.client._data_to_result("change_scene", [True])
        assert result == {"success": True}

    def test_data_pause(self) -> None:
        result = self.client._data_to_result("pause", [True])
        assert result == {"paused": True}

    def test_data_time_scale(self) -> None:
        result = self.client._data_to_result("time_scale", [1.5])
        assert result == {"scale": 1.5}

    def test_data_wait_signal(self) -> None:
        result = self.client._data_to_result("wait_signal", ["pressed", [42, "arg"]])
        assert result == {"signal": "pressed", "args": [42, "arg"]}


class TestNativeClientAsync:
    """Tests for async methods of NativeClient."""

    @pytest.mark.asyncio
    async def test_send_not_connected_raises(self) -> None:
        client = NativeClient()
        with pytest.raises(ConnectionError) as exc:
            await client.send("get_tree")
        assert "Not connected" in str(exc.value)

    @pytest.mark.asyncio
    async def test_is_connected_true(self) -> None:
        client = NativeClient()
        client._writer = MagicMock()
        client._writer.is_closing.return_value = False
        assert client.is_connected is True

    @pytest.mark.asyncio
    async def test_is_connected_false_when_closing(self) -> None:
        client = NativeClient()
        client._writer = MagicMock()
        client._writer.is_closing.return_value = True
        assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect_cancels_receive_task(self) -> None:
        client = NativeClient()

        # Create a real async task that we can cancel
        started = asyncio.Event()

        async def long_running():
            started.set()
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                raise

        task = asyncio.create_task(long_running())
        await started.wait()  # Wait for task to start

        client._receive_task = task
        client._writer = MagicMock()
        client._writer.close = MagicMock()
        client._writer.wait_closed = AsyncMock()

        await client.disconnect()
        assert task.cancelled()

    @pytest.mark.asyncio
    async def test_disconnect_clears_pending(self) -> None:
        client = NativeClient()
        future = asyncio.get_event_loop().create_future()
        client._pending = {"test": future}
        client._writer = MagicMock()
        client._writer.close = MagicMock()
        client._writer.wait_closed = AsyncMock()

        await client.disconnect()
        assert client._pending == {}
        assert future.cancelled()
