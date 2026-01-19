# PlayGodot

[![PyPI version](https://badge.fury.io/py/playgodot.svg)](https://pypi.org/project/playgodot/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Game automation framework for Godot Engine - like [Playwright](https://playwright.dev/), but for games.**

Control Godot games from Python. Automate gameplay, write E2E tests, capture screenshots, simulate input - all from external scripts running outside the engine.

## Why PlayGodot?

Existing Godot tools (GdUnit4, GUT, GodotTestDriver) run *inside* the engine. PlayGodot runs *outside*, giving you:

- **Language freedom** - Write tests in Python, not just GDScript/C#
- **Process isolation** - Tests can't crash with the game
- **CI simplicity** - No need to understand Godot internals
- **Familiar patterns** - API inspired by Playwright
- **No addon required** - Uses Godot's native debugger protocol (requires custom Godot build)

## How It Works

PlayGodot connects to Godot's native debugger protocol with custom automation commands added to the RemoteDebugger. No in-game addon required - the automation layer is built into the engine.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PlayGodot Architecture                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   External Process                           Godot Process              │
│  ┌─────────────────────┐                   ┌─────────────────────┐      │
│  │                     │   TCP Port 6007   │                     │      │
│  │   Python Client     │◄────────────────►│   RemoteDebugger    │      │
│  │                     │   Native Variant  │   (C++ engine code) │      │
│  │  ┌───────────────┐  │                   │  ┌───────────────┐  │      │
│  │  │ playgodot     │  │   Commands:       │  │ Automation    │  │      │
│  │  │               │  │   ─────────────►  │  │ Capture       │  │      │
│  │  │ .launch()     │  │   • get_node      │  │               │  │      │
│  │  │ .click()      │  │   • get_property  │  │ • Native C++  │  │      │
│  │  │ .get_node()   │  │   • set_property  │  │ • No GDScript │  │      │
│  │  │ .call_method()│  │   • call_method   │  │ • Binary      │  │      │
│  │  │ .screenshot() │  │   • screenshot    │  │   protocol    │  │      │
│  │  │ .pause()      │  │   • inject_*      │  │ • Fast &      │  │      │
│  │  │               │  │   • scene_tree    │  │   reliable    │  │      │
│  │  └───────────────┘  │   Responses:      │  └───────────────┘  │      │
│  │                     │   ◄─────────────  │                     │      │
│  │  async/await API    │   • node_info     │  Runs in engine     │      │
│  │                     │   • call_result   │  debug loop         │      │
│  └─────────────────────┘   • screenshots   └─────────────────────┘      │
│           │                • scene_data             ▲                   │
│           │                                         │                   │
│           ▼                                         │                   │
│  ┌─────────────────────┐                   ┌─────────────────────┐      │
│  │   Test Framework    │                   │   Custom Godot      │      │
│  │   (pytest, etc.)    │                   │   (automation fork) │      │
│  └─────────────────────┘                   └─────────────────────┘      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Installation

### Requirements

1. **Custom Godot build** with automation support:
   - Clone: [Randroids-Dojo/godot](https://github.com/Randroids-Dojo/godot) (automation branch)
   - Build: `scons platform=<your_platform> target=editor`

2. **Python client** (Python 3.9+):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install playgodot
   ```

### Godot Setup

No addon required! The automation protocol is built into the custom Godot fork. Just launch your game with the `--remote-debug` flag:

```bash
godot --path /path/to/project --remote-debug tcp://127.0.0.1:6007
```

Or use PlayGodot's `Godot.launch()` which handles this automatically.

### For Contributors

To develop PlayGodot itself:

```bash
git clone https://github.com/Randroids-Dojo/PlayGodot.git
cd PlayGodot/python
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Quick Start

```python
import asyncio
from playgodot import Godot

async def test_game():
    # Launch Godot project
    async with Godot.launch("path/to/project") as game:
        # Wait for game to be ready
        await game.wait_for_node("/root/Main")

        # Click a button
        await game.click("/root/Main/UI/StartButton")

        # Wait for scene change
        await game.wait_for_signal("scene_changed")

        # Take a screenshot
        await game.screenshot("screenshots/game_started.png")

asyncio.run(test_game())
```

## API Reference

### Launching Games

```python
# Launch with default settings
game = await Godot.launch("path/to/project")

# Launch with options
game = await Godot.launch(
    "path/to/project",
    headless=True,           # Run without window (default: True)
    resolution=(1920, 1080), # Window size
    port=6007,               # Debugger port (default: 6007)
    timeout=30000,           # Connection timeout in ms
    verbose=True,            # Enable debug logging
)

# Connect to already-running game
game = await Godot.connect("localhost", 6007)
```

### Node Interaction

```python
# Get node by path
node = await game.get_node("/root/Main/Player")

# Get node properties
position = await game.get_property("/root/Main/Player", "position")
health = await game.get_property("/root/Main/Player", "health")

# Set node properties
await game.set_property("/root/Main/Player", "position", {"x": 100, "y": 200})

# Call node methods
result = await game.call("/root/Main/Game", "get_score")
await game.call("/root/Main/Game", "reset")

# Call with arguments
await game.call("/root/Main/Game", "make_move", [4])  # Single arg
await game.call("/root/Main/Game", "set_player", ["Alice", 100])  # Multiple args
```

### Input Simulation

```python
# Mouse input
await game.click("/root/Main/UI/Button")           # Click node center
await game.click_position(100, 200)                 # Click coordinates
await game.double_click("/root/Main/UI/Item")
await game.right_click("/root/Main/UI/ContextArea")
await game.drag("/root/Main/DragItem", "/root/Main/DropZone")
await game.move_mouse(500, 300)

# Keyboard input
await game.press_key("space")
await game.press_key("ctrl+s")                      # Key combinations
await game.type_text("Hello, World!")               # Type string
await game.press_action("jump")                     # Input actions
await game.hold_action("run", duration=2.0)

# Touch input (mobile)
await game.tap(100, 200)
await game.swipe(100, 200, 400, 200)
await game.pinch(center=(300, 300), scale=0.5)
```

### Waiting

```python
# Wait for node to exist
await game.wait_for_node("/root/Main/Enemy", timeout=5000)

# Wait for node to be visible
await game.wait_for_visible("/root/Main/UI/Popup")

# Wait for signal
await game.wait_for_signal("game_over")
await game.wait_for_signal("health_changed", source="/root/Main/Player")

# Wait for condition (polls until true)
await game.wait_for(
    lambda: game.get_property("/root/Main/Player", "health") < 50,
    timeout=10000
)

# Wait for frames/time
await game.wait_frames(60)      # Wait 60 frames
await game.wait_seconds(2.0)    # Wait 2 seconds
```

### Screenshots & Visual Testing

```python
# Take screenshot
await game.screenshot("output.png")

# Screenshot specific node
await game.screenshot("player.png", node="/root/Main/Player")

# Compare screenshots (returns similarity 0-1)
similarity = await game.compare_screenshot("expected.png", "actual.png")
assert similarity > 0.99, "Screenshots don't match"

# Visual regression testing
await game.assert_screenshot("reference/main_menu.png", threshold=0.01)
```

### Scene Management

```python
# Get current scene
scene = await game.get_current_scene()

# Change scene
await game.change_scene("res://levels/level2.tscn")

# Reload current scene
await game.reload_scene()

# Get scene tree structure
tree = await game.get_tree()
print(tree)  # Hierarchical node structure
```

### Game State

```python
# Get all nodes matching pattern
enemies = await game.query_nodes("/root/Main/Enemies/*")

# Check if node exists
exists = await game.node_exists("/root/Main/Boss")

# Get node count
count = await game.count_nodes("/root/Main/Coins/*")

# Pause/unpause game
await game.pause()
await game.unpause()
await game.set_time_scale(0.5)  # Slow motion
```

## E2E Testing with pytest

```python
# test_game.py
import pytest
from playgodot import Godot

@pytest.fixture
async def game():
    async with Godot.launch("path/to/project") as g:
        yield g

@pytest.mark.asyncio
async def test_player_spawns(game):
    """Player should spawn at starting position."""
    await game.wait_for_node("/root/Main/Player")
    pos = await game.get_property("/root/Main/Player", "position")
    assert pos["x"] == 100
    assert pos["y"] == 200

@pytest.mark.asyncio
async def test_enemy_dies_when_shot(game):
    """Enemy should die when hit by bullet."""
    await game.wait_for_node("/root/Main/Enemy")

    # Simulate shooting
    await game.press_action("shoot")
    await game.wait_seconds(0.5)

    # Enemy should be gone
    exists = await game.node_exists("/root/Main/Enemy")
    assert not exists

@pytest.mark.asyncio
async def test_game_over_on_death(game):
    """Game over screen should appear when player dies."""
    # Kill the player
    await game.set_property("/root/Main/Player", "health", 0)

    # Wait for game over
    await game.wait_for_signal("game_over")
    await game.wait_for_visible("/root/Main/UI/GameOverScreen")

    # Verify screenshot
    await game.assert_screenshot("reference/game_over.png")
```

Run tests:

```bash
pytest test_game.py -v
```

## CI Integration

### GitHub Actions

```yaml
name: Game Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Godot
        uses: chickensoft-games/setup-godot@v2
        with:
          version: 4.3.0

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install PlayGodot
        run: pip install playgodot pytest pytest-asyncio

      - name: Run Tests
        run: pytest tests/ -v --tb=short
```

## Native Debugger Protocol

PlayGodot uses Godot's native debugger protocol over TCP (port 6007). Messages are serialized using Godot's binary Variant format for maximum performance and type fidelity.

### Protocol Overview

The protocol extends Godot's existing `RemoteDebugger` with an `automation` capture that handles game automation commands. All communication uses Godot's native binary serialization.

### Message Format

```
[4 bytes: message length]
[message_type: String]
[data: Array of Variants]
```

### Available Commands

| Command | Data | Response | Description |
|---------|------|----------|-------------|
| `automation:get_node` | `[path]` | `automation:node_info` | Get node info and properties |
| `automation:get_property` | `[path, property]` | `automation:property_value` | Get single property value |
| `automation:set_property` | `[path, property, value]` | `automation:property_set` | Set property value |
| `automation:call_method` | `[path, method, args]` | `automation:call_result` | Call node method |
| `automation:screenshot` | `[node_path?]` | `automation:screenshot` | Capture PNG screenshot |
| `automation:scene_tree` | `[]` | `automation:scene_tree` | Get full scene tree |
| `automation:query_nodes` | `[pattern]` | `automation:query_result` | Find nodes by pattern |
| `automation:count_nodes` | `[pattern]` | `automation:count_result` | Count matching nodes |
| `automation:current_scene` | `[]` | `automation:current_scene` | Get current scene path/name |
| `automation:change_scene` | `[scene_path]` | `automation:scene_changed` | Load new scene |
| `automation:reload_scene` | `[]` | `automation:scene_reloaded` | Reload current scene |
| `automation:pause` | `[paused?]` | `automation:pause_result` | Get/set pause state |
| `automation:time_scale` | `[scale?]` | `automation:time_scale_result` | Get/set time scale |
| `automation:inject_mouse_button` | `[pos, button, pressed, double?]` | - | Simulate mouse click |
| `automation:inject_mouse_motion` | `[pos, relative]` | - | Simulate mouse move |
| `automation:inject_key` | `[keycode, pressed, physical?]` | - | Simulate key press |
| `automation:inject_action` | `[action, pressed, strength?]` | - | Simulate input action |
| `automation:inject_touch` | `[index, pos, pressed]` | - | Simulate touch input |

## Comparison with Other Tools

| | PlayGodot | GdUnit4 | GodotTestDriver | GUT |
|---|-----------|---------|-----------------|-----|
| **Type** | Game automation | Unit testing | Integration testing | Unit testing |
| **Language** | Python | GDScript, C# | C# | GDScript |
| **Runs** | External process | Inside Godot | Inside Godot | Inside Godot |
| **Input simulation** | ✅ | ✅ | ✅ | ❌ |
| **Screenshots** | ✅ | ❌ | ❌ | ❌ |
| **Game modification** | None* | Addon | Addon | Addon |
| **Protocol** | Native debugger | N/A | N/A | N/A |

*Requires custom Godot build, but no changes to your game project.

## Project Structure

```
PlayGodot/
├── python/                     # Python client library
│   ├── playgodot/
│   │   ├── __init__.py
│   │   ├── godot.py           # Main Godot class with async API
│   │   ├── native_client.py   # Native debugger protocol client
│   │   ├── variant.py         # Godot Variant serialization
│   │   └── exceptions.py      # Custom exceptions
│   ├── tests/
│   └── pyproject.toml
│
├── docs/                       # Documentation
│   ├── getting-started.md
│   ├── api-reference.md
│   └── protocol.md
│
└── README.md
```

**Note:** The Godot-side automation is implemented in the custom Godot fork at [Randroids-Dojo/godot](https://github.com/Randroids-Dojo/godot) in `core/debugger/remote_debugger.cpp`.

## Roadmap

### v0.1.0 - Foundation ✅
- [x] WebSocket server addon for Godot 4.x
- [x] Python client with async/await API
- [x] Basic node interaction (get/set/call)
- [x] Mouse and keyboard input simulation
- [x] Screenshot capture

### v0.2.0 - Testing Features ✅
- [x] Signal waiting
- [x] Node existence/visibility waiting
- [x] Screenshot comparison

### v0.3.0 - Native Protocol Migration ✅
- [x] Migrated from WebSocket addon to native debugger protocol
- [x] No addon required - automation built into custom Godot fork
- [x] Binary Variant serialization for performance
- [x] Extended input injection (mouse, keyboard, touch, actions)
- [x] Scene management (tree queries, change/reload)
- [x] Game control (pause, time scale)

### v0.5.0 - Beta Release ✅
- [x] Published to PyPI (`pip install playgodot`)
- [x] Comprehensive test suite (210+ tests)
- [x] Complete documentation (API reference, protocol spec)
- [x] CI/CD with GitHub Actions
- [x] Screenshot comparison with MSE-based similarity

### v1.0.0 - Production Ready
- [ ] Stable API (no breaking changes)
- [ ] Visual regression testing improvements
- [ ] Performance optimizations
- [ ] Additional client libraries (TypeScript, Rust)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repos
git clone https://github.com/Randroids-Dojo/PlayGodot.git
git clone https://github.com/Randroids-Dojo/godot.git
cd godot && git checkout automation

# Build custom Godot
scons platform=macos arch=arm64 target=editor -j8

# Python client development
cd ../PlayGodot/python
pip install -e ".[dev]"
pytest
```

### Areas for Contribution

- **Protocol design** - Help refine the automation protocol
- **Python client** - Implement client features
- **Godot C++ code** - Add new automation commands to RemoteDebugger
- **Documentation** - Improve docs and examples
- **Testing** - Add tests for the framework itself
- **Other clients** - TypeScript, Rust, Go clients

## Related Projects

- **[Godot Skill for Claude Code and Codex](https://github.com/Randroids-Dojo/skills/tree/main/plugins/godot)** - Helps coding agents with Godot development (GDScript, testing, deployment)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Inspired by [Playwright](https://playwright.dev/)
- Thanks to [GodotTestDriver](https://github.com/chickensoft-games/GodotTestDriver) for input simulation patterns
- Thanks to [GdUnit4](https://github.com/MikeSchulze/gdUnit4) for scene runner concepts

---

**PlayGodot** is not affiliated with Godot Engine or the Godot Foundation.
