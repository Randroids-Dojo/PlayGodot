# PlayGodot API Reference

Complete API documentation for the PlayGodot Python client.

## Godot Class

The main class for automating Godot games.

### Launching & Connecting

#### `Godot.launch(project_path, **options)` (async context manager)

Launch a Godot project and connect to it.

**Parameters:**
- `project_path` (str | Path): Path to the Godot project directory
- `headless` (bool): Run without window (default: True)
- `resolution` (tuple[int, int]): Window size as (width, height)
- `port` (int): Debugger port (default: 6007)
- `timeout` (float): Connection timeout in seconds (default: 30.0)
- `godot_path` (str): Path to Godot executable (auto-detected if not provided)
- `verbose` (bool): Enable verbose logging (default: False)

**Example:**
```python
async with Godot.launch("my_game/", headless=True, resolution=(1920, 1080)) as game:
    await game.wait_for_node("/root/Main")
```

#### `Godot.connect(host, port, timeout)` (async)

Connect to an already-running Godot game.

**Parameters:**
- `host` (str): Host address (default: "localhost")
- `port` (int): Debugger port (default: 6007)
- `timeout` (float): Connection timeout in seconds (default: 30.0)

**Returns:** `Godot` instance

**Example:**
```python
game = await Godot.connect("localhost", 6007)
```

#### `disconnect()` (async)

Disconnect from the game and terminate the process if launched.

---

### Node Operations

#### `get_node(path)` (async)

Get a node by path.

**Parameters:**
- `path` (str): Node path (e.g., "/root/Main/Player")

**Returns:** `Node` wrapper

**Raises:** `NodeNotFoundError` if node doesn't exist

**Example:**
```python
player = await game.get_node("/root/Main/Player")
```

#### `get_property(path, property_name)` (async)

Get a property value from a node.

**Returns:** The property value (type varies)

**Example:**
```python
health = await game.get_property("/root/Main/Player", "health")
position = await game.get_property("/root/Main/Player", "position")
# position = {"x": 100, "y": 200}
```

#### `set_property(path, property_name, value)` (async)

Set a property value on a node.

**Example:**
```python
await game.set_property("/root/Main/Player", "health", 100)
await game.set_property("/root/Main/Player", "position", {"x": 50, "y": 100})
```

#### `call(path, method, args=None)` (async)

Call a method on a node.

**Parameters:**
- `path` (str): Node path
- `method` (str): Method name
- `args` (list): Optional arguments

**Returns:** Return value from the method

**Example:**
```python
score = await game.call("/root/Main/Game", "get_score")
await game.call("/root/Main/Game", "add_points", [100])
```

#### `node_exists(path)` (async)

Check if a node exists.

**Returns:** `bool`

#### `query_nodes(pattern)` (async)

Query nodes matching a pattern.

**Parameters:**
- `pattern` (str): Path pattern with `*` wildcard

**Returns:** `list[Node]`

**Example:**
```python
enemies = await game.query_nodes("/root/Main/Enemies/*")
```

#### `count_nodes(pattern)` (async)

Count nodes matching a pattern.

**Returns:** `int`

---

### Input Simulation

#### Mouse Input

##### `click(path_or_x, y=None)` (async)

Click on a node or at coordinates.

**Examples:**
```python
await game.click("/root/Main/UI/Button")  # Click node
await game.click(100, 200)  # Click coordinates
```

##### `click_position(x, y)` (async)

Click at specific coordinates.

##### `double_click(path_or_x, y=None)` (async)

Double-click on a node or at coordinates.

##### `right_click(path_or_x, y=None)` (async)

Right-click on a node or at coordinates.

##### `drag(from_path, to_path, duration=0.5)` (async)

Drag from one node to another.

**Example:**
```python
await game.drag("/root/Main/Item", "/root/Main/Inventory/Slot1")
```

##### `move_mouse(x, y)` (async)

Move the mouse to coordinates.

#### Keyboard Input

##### `press_key(key)` (async)

Press a key.

**Parameters:**
- `key` (str): Key name or combination (e.g., "space", "ctrl+s", "enter")

**Examples:**
```python
await game.press_key("space")
await game.press_key("ctrl+s")
await game.press_key("enter")
```

##### `type_text(text)` (async)

Type a string of text.

**Example:**
```python
await game.type_text("Hello, World!")
```

#### Action Input

##### `press_action(action)` (async)

Press an input action (as defined in Input Map).

**Example:**
```python
await game.press_action("jump")
```

##### `hold_action(action, duration)` (async)

Hold an input action for a duration.

**Example:**
```python
await game.hold_action("run", 2.0)
```

#### Touch Input

##### `tap(x, y)` (async)

Simulate a touch tap.

##### `swipe(from_x, from_y, to_x, to_y)` (async)

Simulate a swipe gesture.

##### `pinch(center, scale)` (async)

Simulate a pinch gesture.

**Parameters:**
- `center` (tuple[float, float]): Center coordinates
- `scale` (float): Scale factor (< 1 for pinch in, > 1 for pinch out)

---

### Waiting

#### `wait_for_node(path, timeout=5.0)` (async)

Wait for a node to exist.

**Returns:** `Node` when found

**Raises:** `TimeoutError` if not found within timeout

#### `wait_for_visible(path, timeout=5.0)` (async)

Wait for a node to be visible.

#### `wait_for_signal(signal_name, source=None, timeout=30.0)` (async)

Wait for a signal to be emitted.

**Parameters:**
- `signal_name` (str): Signal name
- `source` (str): Optional source node path
- `timeout` (float): Timeout in seconds

**Returns:** `dict` with signal data

**Example:**
```python
await game.wait_for_signal("game_over")
await game.wait_for_signal("health_changed", source="/root/Main/Player")
```

#### `wait_for(condition, timeout=10.0, interval=0.1)` (async)

Wait for a condition to be truthy.

**Parameters:**
- `condition` (callable): Function that returns truthy when satisfied
- `timeout` (float): Timeout in seconds
- `interval` (float): Polling interval

**Example:**
```python
await game.wait_for(
    lambda: game.get_property("/root/Main/Player", "health") < 50,
    timeout=10.0
)
```

---

### Screenshots

#### `screenshot(path=None, node=None)` (async)

Capture a screenshot.

**Parameters:**
- `path` (str): Optional file path to save
- `node` (str): Optional node path to capture

**Returns:** `bytes` (PNG data)

**Example:**
```python
await game.screenshot("screenshot.png")
data = await game.screenshot()  # Returns bytes
```

#### `compare_screenshot(expected, actual=None)` (async)

Compare current screenshot to an expected reference image.

**Parameters:**
- `expected` (str | bytes): Path to reference image file or raw PNG bytes
- `actual` (bytes | None): Optional current screenshot bytes. If None, takes a new screenshot.

**Returns:** `float` similarity score (0.0-1.0, where 1.0 is identical)

**Example:**
```python
similarity = await game.compare_screenshot("reference.png")
if similarity < 0.99:
    print("Screenshot differs from reference")
```

#### `assert_screenshot(reference, threshold=0.99, save_diff=None)` (async)

Assert current screenshot matches a reference image within a similarity threshold.

**Parameters:**
- `reference` (str): Path to the reference image file
- `threshold` (float): Minimum required similarity (0.0-1.0, default 0.99)
- `save_diff` (str | None): Optional path to save difference image on failure

**Raises:** `AssertionError` if similarity is below threshold

**Example:**
```python
# Assert with default 99% threshold
await game.assert_screenshot("expected_menu.png")

# Assert with custom threshold and save diff on failure
await game.assert_screenshot(
    "expected_game.png",
    threshold=0.95,
    save_diff="diff_output.png"
)
```

---

### Scene Management

#### `get_current_scene()` (async)

Get the current scene info.

**Returns:** `dict` with `path` and `name` keys

#### `change_scene(scene_path)` (async)

Change to a different scene.

**Example:**
```python
await game.change_scene("res://scenes/level2.tscn")
```

#### `reload_scene()` (async)

Reload the current scene.

#### `get_tree()` (async)

Get the scene tree structure.

**Returns:** `dict` with hierarchical tree data

---

### Game State

#### `pause()` (async)

Pause the game.

#### `unpause()` (async)

Unpause the game.

#### `is_paused()` (async)

Check if the game is paused.

**Returns:** `bool`

#### `get_time_scale()` (async)

Get the current game time scale.

**Returns:** `float`

#### `set_time_scale(scale)` (async)

Set the game time scale.

**Example:**
```python
await game.set_time_scale(0.5)  # Half speed
await game.set_time_scale(2.0)  # Double speed
```

---

## Node Class

Wrapper for a Godot node with convenient property and method access.

### Properties

- `path` (str): The node path
- `class_name` (str): The node's class name
- `name` (str): The node's name

### Methods

#### `get_property(property_name)` (async)

Get a property value.

#### `set_property(property_name, value)` (async)

Set a property value.

#### `call(method, args=None)` (async)

Call a method.

#### `click()` (async)

Click on the node.

#### `is_visible()` (async)

Check if the node is visible.

#### `get_children()` (async)

Get all child nodes.

**Returns:** `list[Node]`

---

## Exceptions

### `PlayGodotError`

Base exception for all PlayGodot errors.

### `ConnectionError`

Raised when connection to Godot fails.

### `TimeoutError`

Raised when an operation times out.

### `NodeNotFoundError`

Raised when a node cannot be found.

**Properties:**
- `path` (str): The path that was not found

### `CommandError`

Raised when a command fails on the Godot side.

**Properties:**
- `method` (str): The failed method
- `code` (int): Error code
