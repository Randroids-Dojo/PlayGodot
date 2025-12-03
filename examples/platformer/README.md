# Platformer Example

This example demonstrates how to use PlayGodot to test a 2D platformer game, including input simulation and screenshot verification.

## Structure

```
platformer/
├── godot/              # Godot project
│   ├── project.godot
│   ├── scenes/
│   │   ├── main.tscn
│   │   └── player.tscn
│   ├── scripts/
│   │   ├── player.gd
│   │   └── game.gd
│   └── sprites/
├── tests/              # Python tests
│   ├── conftest.py
│   ├── test_player.py
│   └── test_levels.py
├── screenshots/        # Reference screenshots
│   └── level1_start.png
└── README.md
```

## Running Tests

```bash
pip install playgodot[image] pytest pytest-asyncio
pytest tests/ -v
```

## Example Tests

### Player Movement Test

```python
import pytest
from playgodot import Godot

@pytest.fixture
async def game():
    async with Godot.launch("godot/") as g:
        await g.wait_for_node("/root/Main/Player")
        yield g

@pytest.mark.asyncio
async def test_player_moves_right(game):
    """Test that holding right moves the player."""
    initial_pos = await game.get_property("/root/Main/Player", "position")

    await game.hold_action("move_right", duration=0.5)
    await game.wait_seconds(0.1)

    final_pos = await game.get_property("/root/Main/Player", "position")
    assert final_pos["x"] > initial_pos["x"]

@pytest.mark.asyncio
async def test_player_jumps(game):
    """Test that the player can jump."""
    initial_pos = await game.get_property("/root/Main/Player", "position")

    await game.press_action("jump")
    await game.wait_frames(10)

    mid_jump_pos = await game.get_property("/root/Main/Player", "position")
    assert mid_jump_pos["y"] < initial_pos["y"]  # Y is inverted in Godot
```

### Visual Regression Test

```python
@pytest.mark.asyncio
async def test_level_start_screenshot(game):
    """Verify the level looks correct on start."""
    await game.assert_screenshot(
        "screenshots/level1_start.png",
        threshold=0.99
    )
```

## What This Example Demonstrates

- Input action simulation (hold, press)
- Waiting for frames and time
- Reading node properties
- Visual regression testing with screenshots
- Testing player physics and movement
