# Platformer Example

A comprehensive example demonstrating PlayGodot's full capabilities for testing a 2D platformer game.

This example showcases **all major PlayGodot features** including input simulation, property access, signal waiting, visual regression testing, and game state management.

## Structure

```
platformer/
├── godot/                      # Godot 4.x project
│   ├── project.godot           # Project configuration with input actions
│   ├── scenes/
│   │   ├── main.tscn           # Main game scene
│   │   ├── player.tscn         # Player character
│   │   └── coin.tscn           # Collectible coin
│   └── scripts/
│       ├── game.gd             # Game manager
│       ├── player.gd           # Player controller
│       └── coin.gd             # Collectible logic
├── tests/                      # Python tests
│   ├── conftest.py             # Pytest fixtures
│   ├── test_player_movement.py # Input & movement tests
│   ├── test_game_state.py      # State & scene management
│   ├── test_visual.py          # Screenshot testing
│   ├── test_signals_and_waiting.py  # Signals & waiting
│   └── test_collectibles.py    # Game mechanics
├── screenshots/                # Reference screenshots
└── README.md
```

## The Game

A simple 2D platformer with:
- Player movement (left/right with A/D or arrows)
- Jumping (Space, W, or Up arrow)
- Collectible coins (5 total)
- Score tracking
- Pause menu (Escape)
- Level restart (R)

## Running Tests

```bash
# Install PlayGodot with image support for screenshot tests
pip install playgodot[image] pytest pytest-asyncio

# Run all tests
cd examples/platformer
pytest tests/ -v

# Run specific test file
pytest tests/test_player_movement.py -v

# Run with output
pytest tests/ -v -s
```

## PlayGodot Features Demonstrated

### 1. Input Simulation

#### Input Actions (`press_action`, `hold_action`)
```python
# Press and release an action
await game.press_action("jump")

# Hold an action for duration
await game.hold_action("move_right", duration=0.5)
```

#### Keyboard Input (`press_key`)
```python
# Press a single key
await game.press_key("space")

# Press key with modifier
await game.press_key("ctrl+s")
```

### 2. Property Access

#### Reading Properties (`get_property`)
```python
# Read position (returns dict with x, y)
position = await game.get_property("/root/Main/Player", "position")

# Read text
label_text = await game.get_property("/root/Main/HUD/ScoreLabel", "text")

# Read visibility
visible = await game.get_property("/root/Main/HUD/PauseMenu", "visible")
```

#### Setting Properties (`set_property`)
```python
# Set a property value
await game.set_property("/root/Main/Player", "position", {"x": 100, "y": 200})
```

### 3. Method Calls (`call`)

```python
# Call method with no arguments
score = await game.call("/root/Main", "get_score")

# Call method with arguments
result = await game.call("/root/Main/Player", "set_position_for_test", [200.0, 400.0])

# Get player state
state = await game.call("/root/Main/Player", "get_state")  # "idle", "running", "jumping", "falling"
```

### 4. Node Querying

```python
# Query nodes matching pattern
coins = await game.query_nodes("/root/Main/Coins/*")

# Count matching nodes
count = await game.count_nodes("/root/Main/Coins/*")

# Get scene tree structure
tree = await game.get_tree()
```

### 5. Waiting Patterns

#### Wait for Node (`wait_for_node`)
```python
# Wait for node to exist
player = await game.wait_for_node("/root/Main/Player", timeout=5.0)
```

#### Wait for Visibility (`wait_for_visible`)
```python
# Wait for UI element to appear
await game.wait_for_visible("/root/Main/HUD/PauseMenu", timeout=5.0)
```

#### Custom Conditions (`wait_for`)
```python
# Wait for any condition
async def player_grounded():
    return await game.call("/root/Main/Player", "is_grounded")

await game.wait_for(player_grounded, timeout=5.0, interval=0.1)
```

#### Wait for Signal (`wait_for_signal`)
```python
# Wait for a Godot signal
result = await game.wait_for_signal("jumped", source="/root/Main/Player", timeout=5.0)
```

### 6. Visual Testing

#### Taking Screenshots
```python
# Get screenshot as bytes
png_data = await game.screenshot()

# Save to file
await game.screenshot(path="screenshot.png")
```

#### Comparing Screenshots
```python
# Compare two screenshots (returns 0.0-1.0 similarity)
similarity = await game.compare_screenshot(expected_bytes, actual_bytes)
```

#### Visual Regression
```python
# Assert screenshot matches reference (raises if below threshold)
await game.assert_screenshot(
    "screenshots/reference.png",
    threshold=0.95,  # 95% similarity required
    save_diff="diff.png"  # Optional: save diff image on failure
)
```

### 7. Scene Management

```python
# Get current scene info
scene = await game.get_current_scene()

# Reload current scene
await game.reload_scene()

# Change to different scene
await game.change_scene("res://scenes/level2.tscn")
```

### 8. Game State Control

#### Pausing
```python
# Pause/unpause programmatically
await game.pause()
await game.unpause()

# Check pause state
is_paused = await game.is_paused()
```

#### Time Scale
```python
# Speed up game (useful for faster tests)
await game.set_time_scale(2.0)  # 2x speed

# Slow motion
await game.set_time_scale(0.5)  # Half speed

# Get current scale
scale = await game.get_time_scale()
```

## Test Examples

### Testing Player Movement
```python
@pytest.mark.asyncio
async def test_player_moves_right(game):
    initial = await game.get_property("/root/Main/Player", "position")

    await game.hold_action("move_right", duration=0.3)

    final = await game.get_property("/root/Main/Player", "position")
    assert final["x"] > initial["x"]
```

### Testing Jump Physics
```python
@pytest.mark.asyncio
async def test_player_jumps(game):
    # Wait for grounded
    async def is_grounded():
        return await game.call("/root/Main/Player", "is_grounded")
    await game.wait_for(is_grounded, timeout=3.0)

    initial_y = await game.call("/root/Main/Player", "get_position_y")

    await game.press_action("jump")
    await asyncio.sleep(0.15)

    mid_y = await game.call("/root/Main/Player", "get_position_y")
    assert mid_y < initial_y  # Y is inverted in Godot
```

### Testing Game State
```python
@pytest.mark.asyncio
async def test_pause_menu(game):
    # Verify initially hidden
    visible = await game.get_property("/root/Main/HUD/PauseMenu", "visible")
    assert visible is False

    # Pause with action
    await game.press_action("pause")

    # Verify menu visible
    visible = await game.get_property("/root/Main/HUD/PauseMenu", "visible")
    assert visible is True
```

### Visual Regression Test
```python
@pytest.mark.asyncio
async def test_level_appearance(game):
    await asyncio.sleep(0.2)  # Wait for stable render

    await game.assert_screenshot(
        "screenshots/level1_start.png",
        threshold=0.95
    )
```

## Game API Reference

### Player Methods
| Method | Returns | Description |
|--------|---------|-------------|
| `get_position_x()` | float | Current X position |
| `get_position_y()` | float | Current Y position |
| `get_velocity_x()` | float | Current X velocity |
| `get_velocity_y()` | float | Current Y velocity |
| `is_grounded()` | bool | On floor? |
| `is_jumping()` | bool | Moving upward? |
| `is_falling()` | bool | Moving downward? |
| `get_state()` | String | "idle"/"running"/"jumping"/"falling"/"dead" |
| `get_coins()` | int | Coins collected |
| `set_position_for_test(x, y)` | void | Teleport player |

### Game Methods
| Method | Returns | Description |
|--------|---------|-------------|
| `get_score()` | int | Current score |
| `get_total_coins()` | int | Total coins in level |
| `get_remaining_coins()` | int | Coins left to collect |
| `is_level_complete()` | bool | All coins collected? |
| `is_paused()` | bool | Game paused? |
| `get_level_name()` | String | Current level name |
| `get_player_state()` | String | Player state |
| `restart_level()` | void | Restart level |

### Input Actions
| Action | Keys | Description |
|--------|------|-------------|
| `move_left` | A, Left Arrow | Move left |
| `move_right` | D, Right Arrow | Move right |
| `jump` | Space, W, Up Arrow | Jump |
| `pause` | Escape | Toggle pause |
| `restart` | R | Restart level |

### Signals
| Signal | Args | Description |
|--------|------|-------------|
| `jumped` | - | Player jumped |
| `landed` | - | Player landed |
| `collected` | item_name: String | Item collected |
| `died` | - | Player died |
| `game_paused` | - | Game paused |
| `game_resumed` | - | Game resumed |
| `level_completed` | level_name: String | Level finished |
| `score_changed` | new_score: int | Score updated |
