# Getting Started with PlayGodot

This guide will help you set up PlayGodot and write your first automated tests for a Godot game.

## Prerequisites

- **Python 3.9+** - For running the test client
- **Custom Godot fork** - PlayGodot requires [Randroids-Dojo/godot](https://github.com/Randroids-Dojo/godot) (automation branch) with built-in automation support
- **pip** - Python package manager

## Installation

### Install the Python Client

```bash
pip install playgodot
```

That's it! PlayGodot uses Godot's native remote debugger protocol, so **no addon or plugin installation is required** in your Godot project.

## How It Works

PlayGodot connects to Godot using the built-in `--remote-debug` flag:

1. PlayGodot starts a TCP server on port 6007
2. PlayGodot launches your Godot project with `--remote-debug tcp://localhost:6007`
3. Godot connects to PlayGodot and accepts automation commands
4. Your Python code controls the game through this connection

## Writing Your First Test

Create a file called `test_game.py`:

```python
import asyncio
from playgodot import Godot

async def test_game():
    # Launch your game
    async with Godot.launch("path/to/your/game") as game:
        # Wait for the main scene to load
        await game.wait_for_node("/root/Main")
        print("Game loaded!")

        # Get the player node
        player = await game.get_node("/root/Main/Player")
        print(f"Found player: {player}")

        # Get player position
        position = await game.get_property("/root/Main/Player", "position")
        print(f"Player position: {position}")

        # Click a button
        await game.click("/root/Main/UI/StartButton")
        print("Clicked start button!")

        # Wait a moment
        await asyncio.sleep(1.0)

        # Take a screenshot
        await game.screenshot("test_screenshot.png")
        print("Screenshot saved!")

# Run the test
asyncio.run(test_game())
```

Run it:

```bash
python test_game.py
```

## Using pytest

For more structured testing, use pytest:

```python
# tests/test_game.py
import asyncio
import pytest
from playgodot import Godot

@pytest.fixture
async def game():
    """Fixture that provides a connected game instance."""
    async with Godot.launch("path/to/your/game") as g:
        await g.wait_for_node("/root/Main")
        yield g

@pytest.mark.asyncio
async def test_player_exists(game):
    """Test that the player spawns."""
    exists = await game.node_exists("/root/Main/Player")
    assert exists, "Player should exist"

@pytest.mark.asyncio
async def test_start_button_works(game):
    """Test that the start button changes scenes."""
    await game.click("/root/Main/UI/StartButton")
    await asyncio.sleep(0.5)

    scene = await game.get_current_scene()
    assert "game.tscn" in scene["path"]
```

Install test dependencies:

```bash
pip install pytest pytest-asyncio
```

Run tests:

```bash
pytest tests/ -v
```

## Common Operations

### Finding Nodes

```python
# Get a node
player = await game.get_node("/root/Main/Player")

# Check if node exists
exists = await game.node_exists("/root/Main/Enemy")

# Find all enemies
enemies = await game.query_nodes("/root/Main/Enemies/*")
```

### Reading/Writing Properties

```python
# Get a property
health = await game.get_property("/root/Main/Player", "health")

# Set a property
await game.set_property("/root/Main/Player", "health", 100)
```

### Calling Methods

```python
# Call a method
score = await game.call("/root/Main/Game", "get_score")

# Call with arguments
await game.call("/root/Main/Game", "add_score", [50])
```

### Input Simulation

```python
# Click on nodes
await game.click("/root/Main/UI/Button")

# Press keys
await game.press_key("space")
await game.press_key("ctrl+s")

# Input actions
await game.press_action("jump")
await game.hold_action("run", duration=2.0)

# Type text
await game.type_text("Player1")
```

### Waiting

```python
# Wait for node to exist
await game.wait_for_node("/root/Main/Boss", timeout=10.0)

# Wait for signal
await game.wait_for_signal("game_over")

# Wait for visibility
await game.wait_for_visible("/root/Main/UI/Popup")

# Wait using asyncio
import asyncio
await asyncio.sleep(2.0)
```

### Screenshots

```python
# Capture screenshot
await game.screenshot("screenshot.png")

# Compare with reference
similarity = await game.compare_screenshot("expected.png")
assert similarity > 0.99

# Assert screenshot matches
await game.assert_screenshot("reference.png", threshold=0.99)
```

## Launch Options

### Headless Testing

By default, PlayGodot runs games in headless mode (no window). This is ideal for CI environments.

To see the game window during development:

```python
async with Godot.launch("path/to/game", headless=False) as game:
    # Game window will be visible
    ...
```

### Custom Port

If port 6007 is in use, specify a different port:

```python
async with Godot.launch("path/to/game", port=6008) as game:
    ...
```

### Custom Godot Path

If Godot isn't in your PATH:

```python
async with Godot.launch(
    "path/to/game",
    godot_path="/path/to/godot"
) as game:
    ...
```

### Resolution

Set the window resolution:

```python
async with Godot.launch(
    "path/to/game",
    resolution=(1920, 1080)
) as game:
    ...
```

### Launching a Specific Scene

Test a specific scene directly instead of the project's main scene. This is useful for isolated scene testing without navigating through menus:

```python
async with Godot.launch(
    "path/to/game",
    scene="res://scenes/experiment.tscn"
) as game:
    await game.wait_for_node("/root/Experiment")
    # Test the scene directly
```

This enables:
- **Faster tests**: Skip navigation, test scenes directly
- **Better isolation**: Each scene can have independent tests
- **Simpler fixtures**: One fixture per testable scene
- **More robust tests**: Tests don't break when navigation UI changes

## Connecting to a Running Game

Instead of launching a new instance, you can connect to an already-running game:

```bash
# Start your game manually with the remote debug flag
godot --remote-debug tcp://localhost:6007 --path /path/to/project
```

Then connect from Python:

```python
game = await Godot.connect("localhost", 6007)
# ... use the game
await game.disconnect()
```

## Troubleshooting

### "Godot did not connect within timeout"

- Make sure no other process is using port 6007
- Verify your project path is correct
- Check that Godot is in your PATH or provide `godot_path`

### "Not connected to Godot"

- The connection was lost unexpectedly
- Check if your game crashed or exited
- Look for errors in Godot's output

### Commands timing out

- Increase the timeout: `await game.get_node("/root/Main", timeout=60.0)`
- Check if the node path is correct
- Ensure the scene has loaded fully

## Next Steps

- Check out the [API Reference](api-reference.md) for all available methods
- See [CI Integration](ci-integration.md) for setting up GitHub Actions
- Read the [Protocol Specification](../protocol/PROTOCOL.md) for low-level details
- Browse the [Examples](../examples/) for complete working projects
