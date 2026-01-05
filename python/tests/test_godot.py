"""Tests for the main Godot class."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from playgodot.godot import Godot
from playgodot.node import Node
from playgodot.exceptions import NodeNotFoundError, TimeoutError


class TestGodotInit:
    """Tests for Godot initialization."""

    def test_init_with_client(self, mock_client) -> None:
        godot = Godot(client=mock_client)
        assert godot._client is mock_client

    def test_init_with_process(self, mock_client) -> None:
        process = MagicMock()
        godot = Godot(client=mock_client, process=process)
        assert godot._process is process

    def test_init_creates_input_simulator(self, mock_client) -> None:
        godot = Godot(client=mock_client)
        assert godot._input is not None


class TestFindGodot:
    """Tests for Godot executable discovery."""

    def test_find_godot_fork_first(self) -> None:
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda name: f"/usr/bin/{name}" if name == "godot-fork" else None
            result = Godot._find_godot()
            assert result == "/usr/bin/godot-fork"

    def test_find_godot_standard(self) -> None:
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda name: f"/usr/bin/{name}" if name == "godot" else None
            result = Godot._find_godot()
            assert result == "/usr/bin/godot"

    def test_find_godot_not_found(self) -> None:
        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            with pytest.raises(FileNotFoundError) as exc:
                Godot._find_godot()
            assert "Godot executable not found" in str(exc.value)


class TestNodeInteraction:
    """Tests for node interaction methods."""

    @pytest.mark.asyncio
    async def test_get_node_success(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = {"path": "/root/Main", "name": "Main", "class": "Node2D"}
        node = await mock_godot.get_node("/root/Main")
        assert isinstance(node, Node)
        assert node.path == "/root/Main"
        mock_client.send.assert_called_with("get_node", {"path": "/root/Main"})

    @pytest.mark.asyncio
    async def test_get_node_not_found(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = None
        with pytest.raises(NodeNotFoundError):
            await mock_godot.get_node("/root/Missing")

    @pytest.mark.asyncio
    async def test_get_property(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = {"value": 42}
        result = await mock_godot.get_property("/root/Main", "score")
        assert result == 42
        mock_client.send.assert_called_with(
            "get_property",
            {"path": "/root/Main", "property": "score"},
        )

    @pytest.mark.asyncio
    async def test_set_property(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = {"success": True}
        await mock_godot.set_property("/root/Main", "score", 100)
        mock_client.send.assert_called_with(
            "set_property",
            {"path": "/root/Main", "property": "score", "value": 100},
        )

    @pytest.mark.asyncio
    async def test_call_method_no_args(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = {"value": "result"}
        result = await mock_godot.call("/root/Main", "get_name")
        assert result == "result"
        mock_client.send.assert_called_with(
            "call_method",
            {"path": "/root/Main", "method": "get_name", "args": []},
        )

    @pytest.mark.asyncio
    async def test_call_method_with_args(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = {"value": 15}
        result = await mock_godot.call("/root/Main", "add", [10, 5])
        assert result == 15
        mock_client.send.assert_called_with(
            "call_method",
            {"path": "/root/Main", "method": "add", "args": [10, 5]},
        )

    @pytest.mark.asyncio
    async def test_node_exists_true(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = {"path": "/root/Main"}
        result = await mock_godot.node_exists("/root/Main")
        assert result is True

    @pytest.mark.asyncio
    async def test_node_exists_false(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = None
        result = await mock_godot.node_exists("/root/Missing")
        assert result is False

    @pytest.mark.asyncio
    async def test_query_nodes(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = ["/root/Main/Enemy1", "/root/Main/Enemy2"]
        result = await mock_godot.query_nodes("/root/Main/*")
        assert result == ["/root/Main/Enemy1", "/root/Main/Enemy2"]

    @pytest.mark.asyncio
    async def test_count_nodes(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = 5
        result = await mock_godot.count_nodes("/root/Main/*")
        assert result == 5


class TestInputMethods:
    """Tests for input simulation methods."""

    @pytest.mark.asyncio
    async def test_click_with_path(self, mock_godot) -> None:
        mock_godot._input.click_node = AsyncMock()
        await mock_godot.click("/root/Main/Button")
        mock_godot._input.click_node.assert_called_with("/root/Main/Button")

    @pytest.mark.asyncio
    async def test_click_with_coordinates(self, mock_godot) -> None:
        mock_godot._input.click = AsyncMock()
        await mock_godot.click(100.0, 200.0)
        mock_godot._input.click.assert_called_with(100.0, 200.0)

    @pytest.mark.asyncio
    async def test_click_no_y_raises(self, mock_godot) -> None:
        with pytest.raises(ValueError) as exc:
            await mock_godot.click(100.0)
        assert "Y coordinate required" in str(exc.value)

    @pytest.mark.asyncio
    async def test_double_click_with_path(self, mock_godot) -> None:
        mock_godot._input.double_click_node = AsyncMock()
        await mock_godot.double_click("/root/Main/Button")
        mock_godot._input.double_click_node.assert_called_with("/root/Main/Button")

    @pytest.mark.asyncio
    async def test_right_click_with_path(self, mock_godot) -> None:
        mock_godot._input.right_click_node = AsyncMock()
        await mock_godot.right_click("/root/Main/Button")
        mock_godot._input.right_click_node.assert_called_with("/root/Main/Button")

    @pytest.mark.asyncio
    async def test_drag(self, mock_godot) -> None:
        mock_godot._input.drag_node = AsyncMock()
        await mock_godot.drag("/root/From", "/root/To", duration=1.0)
        mock_godot._input.drag_node.assert_called_with("/root/From", "/root/To", 1.0)

    @pytest.mark.asyncio
    async def test_move_mouse(self, mock_godot) -> None:
        mock_godot._input.move_mouse = AsyncMock()
        await mock_godot.move_mouse(150.0, 250.0)
        mock_godot._input.move_mouse.assert_called_with(150.0, 250.0)

    @pytest.mark.asyncio
    async def test_press_key_simple(self, mock_godot) -> None:
        mock_godot._input.press_key = AsyncMock()
        await mock_godot.press_key("space")
        mock_godot._input.press_key.assert_called_with("space")

    @pytest.mark.asyncio
    async def test_press_key_with_modifiers(self, mock_godot) -> None:
        mock_godot._input.press_key = AsyncMock()
        await mock_godot.press_key("ctrl+s")
        mock_godot._input.press_key.assert_called_with("s", ["ctrl"])

    @pytest.mark.asyncio
    async def test_type_text(self, mock_godot) -> None:
        mock_godot._input.type_text = AsyncMock()
        await mock_godot.type_text("hello")
        mock_godot._input.type_text.assert_called_with("hello")

    @pytest.mark.asyncio
    async def test_press_action(self, mock_godot) -> None:
        mock_godot._input.press_action = AsyncMock()
        await mock_godot.press_action("ui_accept")
        mock_godot._input.press_action.assert_called_with("ui_accept")

    @pytest.mark.asyncio
    async def test_tap(self, mock_godot) -> None:
        mock_godot._input.tap = AsyncMock()
        await mock_godot.tap(100.0, 200.0)
        mock_godot._input.tap.assert_called_with(100.0, 200.0)

    @pytest.mark.asyncio
    async def test_swipe(self, mock_godot) -> None:
        mock_godot._input.swipe = AsyncMock()
        await mock_godot.swipe(0.0, 0.0, 100.0, 100.0)
        mock_godot._input.swipe.assert_called_with(0.0, 0.0, 100.0, 100.0)

    @pytest.mark.asyncio
    async def test_pinch(self, mock_godot) -> None:
        mock_godot._input.pinch = AsyncMock()
        await mock_godot.pinch((100.0, 100.0), 0.5)
        mock_godot._input.pinch.assert_called_with(100.0, 100.0, 0.5)


class TestSceneManagement:
    """Tests for scene management methods."""

    @pytest.mark.asyncio
    async def test_get_current_scene(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = {"path": "res://main.tscn", "name": "Main"}
        result = await mock_godot.get_current_scene()
        assert result["path"] == "res://main.tscn"
        assert result["name"] == "Main"

    @pytest.mark.asyncio
    async def test_get_current_scene_empty(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = None
        result = await mock_godot.get_current_scene()
        assert result == {"path": "", "name": ""}

    @pytest.mark.asyncio
    async def test_change_scene(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = {"success": True}
        await mock_godot.change_scene("res://level2.tscn")
        mock_client.send.assert_called_with("change_scene", {"path": "res://level2.tscn"})

    @pytest.mark.asyncio
    async def test_reload_scene(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = {"success": True}
        await mock_godot.reload_scene()
        mock_client.send.assert_called_with("reload_scene")

    @pytest.mark.asyncio
    async def test_get_tree(self, mock_godot, mock_client) -> None:
        tree_data = {"name": "root", "children": []}
        mock_client.send.return_value = tree_data
        result = await mock_godot.get_tree()
        assert result == tree_data


class TestGameState:
    """Tests for game state methods."""

    @pytest.mark.asyncio
    async def test_pause(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = {"paused": True}
        await mock_godot.pause()
        mock_client.send.assert_called_with("pause", {"paused": True})

    @pytest.mark.asyncio
    async def test_unpause(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = {"paused": False}
        await mock_godot.unpause()
        mock_client.send.assert_called_with("pause", {"paused": False})

    @pytest.mark.asyncio
    async def test_is_paused(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = {"paused": True}
        result = await mock_godot.is_paused()
        assert result is True

    @pytest.mark.asyncio
    async def test_set_time_scale(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = {"scale": 2.0}
        await mock_godot.set_time_scale(2.0)
        mock_client.send.assert_called_with("time_scale", {"scale": 2.0})

    @pytest.mark.asyncio
    async def test_get_time_scale(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = {"scale": 1.5}
        result = await mock_godot.get_time_scale()
        assert result == 1.5


class TestScreenshot:
    """Tests for screenshot methods."""

    @pytest.mark.asyncio
    async def test_screenshot_returns_bytes(self, mock_godot, mock_client) -> None:
        png_data = b"\x89PNG\r\n\x1a\n..."
        mock_client.send.return_value = {"data": png_data}
        result = await mock_godot.screenshot()
        assert result == png_data

    @pytest.mark.asyncio
    async def test_screenshot_saves_to_file(self, mock_godot, mock_client, tmp_path) -> None:
        png_data = b"\x89PNG\r\n\x1a\n..."
        mock_client.send.return_value = {"data": png_data}
        file_path = tmp_path / "screenshot.png"
        await mock_godot.screenshot(path=str(file_path))
        assert file_path.read_bytes() == png_data

    @pytest.mark.asyncio
    async def test_screenshot_with_node(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = {"data": b"png"}
        await mock_godot.screenshot(node="/root/Main/Viewport")
        mock_client.send.assert_called_with("screenshot", {"node_path": "/root/Main/Viewport"})

    @pytest.mark.asyncio
    async def test_screenshot_failure(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = None
        with pytest.raises(RuntimeError) as exc:
            await mock_godot.screenshot()
        assert "Failed to take screenshot" in str(exc.value)


class TestWaitForSignal:
    """Tests for wait_for_signal method."""

    @pytest.mark.asyncio
    async def test_wait_for_signal_success(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = {"signal": "pressed", "args": []}
        result = await mock_godot.wait_for_signal("pressed")
        assert result["signal"] == "pressed"
        mock_client.send.assert_called_with(
            "wait_signal",
            {"signal": "pressed", "source": "", "timeout": 30000},
            timeout=35.0,
        )

    @pytest.mark.asyncio
    async def test_wait_for_signal_with_source(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = {"signal": "pressed", "args": []}
        await mock_godot.wait_for_signal("pressed", source="/root/Main/Button")
        mock_client.send.assert_called_with(
            "wait_signal",
            {"signal": "pressed", "source": "/root/Main/Button", "timeout": 30000},
            timeout=35.0,
        )

    @pytest.mark.asyncio
    async def test_wait_for_signal_custom_timeout(self, mock_godot, mock_client) -> None:
        mock_client.send.return_value = {"signal": "done", "args": [42]}
        result = await mock_godot.wait_for_signal("done", timeout=10.0)
        assert result["args"] == [42]
        mock_client.send.assert_called_with(
            "wait_signal",
            {"signal": "done", "source": "", "timeout": 10000},
            timeout=15.0,
        )
