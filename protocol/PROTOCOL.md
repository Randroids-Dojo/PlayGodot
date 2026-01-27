# PlayGodot Protocol Specification

PlayGodot uses **Godot's native RemoteDebugger TCP protocol** with **binary Variant serialization** for communication between external clients (Python, etc.) and the Godot game.

## Overview

PlayGodot connects to a custom Godot fork's extended RemoteDebugger interface. This means:

- **No in-game addon required** - Automation is built into the custom Godot fork
- **Native binary protocol** - Efficient Variant serialization
- **Full engine access** - Same interface used by Godot's editor debugger

> **Note:** PlayGodot requires the custom Godot fork from [Randroids-Dojo/godot](https://github.com/Randroids-Dojo/godot) (automation branch). Standard Godot releases do not include the automation commands.

## Connection

- Default port: `6007`
- Protocol: TCP
- Connection flow: PlayGodot starts a TCP server, then launches Godot with `--remote-debug tcp://host:port`

### Connection Sequence

```
1. PlayGodot starts TCP server on port 6007
2. PlayGodot launches Godot with: godot --remote-debug tcp://localhost:6007 --path /project
3. Godot connects to PlayGodot as a client
4. PlayGodot captures Godot's thread ID from the first received message
5. PlayGodot sends commands using Godot's thread ID
```

The port can be configured via the `port` parameter when launching:

```python
async with Godot.launch("project/", port=6008) as game:
    ...
```

## Message Format

All messages use Godot's native Variant binary encoding.

### Wire Format

```
[4 bytes: size]  - Little-endian uint32, size of variant data
[N bytes: data]  - Encoded Variant (always an Array)
```

### Message Structure

Each message is a Variant Array with 3 elements:

```
Array[
    String: message_name,    # e.g., "automation:get_tree"
    int: thread_id,          # Godot's main thread ID
    Array: data              # Command parameters or response data
]
```

### Example Message (Hex)

A `get_tree` command might look like:

```
04 00 00 00              # Size: 4 bytes (header only for this example)
1C 00 00 00              # Variant header: ARRAY type (28)
03 00 00 00              # Array length: 3 elements
04 00 00 00              # STRING header
14 00 00 00              # String length: 20 bytes
61 75 74 6F 6D 61 74 69  # "automati"
6F 6E 3A 67 65 74 5F 74  # "on:get_t"
72 65 65 00              # "ree" + padding
02 00 00 00              # INT header
01 00 00 00              # Thread ID: 1
1C 00 00 00              # ARRAY header (data array)
00 00 00 00              # Empty array
```

## Variant Encoding

PlayGodot uses Godot's native binary Variant format from `core/io/marshalls.cpp`.

### Type IDs

| ID | Type | Python Equivalent |
|----|------|-------------------|
| 0 | NIL | `None` |
| 1 | BOOL | `bool` |
| 2 | INT | `int` |
| 3 | FLOAT | `float` |
| 4 | STRING | `str` |
| 5 | VECTOR2 | `dict` with x, y |
| 20 | COLOR | `dict` with r, g, b, a |
| 27 | DICTIONARY | `dict` |
| 28 | ARRAY | `list` |
| 29 | PACKED_BYTE_ARRAY | `bytes` |

### Encoding Rules

**Header Format:**
```
[4 bytes: header]
  - Byte 0: Variant::Type enum value
  - Bit 16: 64-bit flag (for INT and FLOAT)
```

**String Encoding:**
```
[4 bytes: header]       # Type 4 (STRING)
[4 bytes: length]       # UTF-8 byte length
[N bytes: UTF-8 data]   # String content
[0-3 bytes: padding]    # Pad to 4-byte boundary
```

**Array Encoding:**
```
[4 bytes: header]       # Type 28 (ARRAY)
[4 bytes: count]        # Number of elements
[...]: encoded elements # Each element is a full Variant
```

**Integer Encoding:**
```
32-bit (if -2^31 <= value <= 2^31-1):
  [4 bytes: header]     # Type 2 (INT)
  [4 bytes: value]      # Signed int32

64-bit (otherwise):
  [4 bytes: header]     # Type 2 | (1 << 16) = 0x10002
  [8 bytes: value]      # Signed int64
```

## Automation Commands

Commands are sent as `automation:<command>` with a data array containing parameters.

### Node Operations

#### get_tree

Get the scene tree structure.

**Request:** `automation:get_tree` → `[]`

**Response:** `automation:tree` → `[tree_dict]`

```python
# tree_dict structure:
{
    "name": "root",
    "path": "/root",
    "class": "Window",
    "children": [...]
}
```

#### get_node

Get information about a node.

**Request:** `automation:get_node` → `[path]`

**Response:** `automation:node` → `[node_dict | null]`

```python
# node_dict structure:
{
    "path": "/root/Main/Player",
    "name": "Player",
    "class": "CharacterBody2D"
}
```

#### get_property

Get a property value from a node.

**Request:** `automation:get_property` → `[path, property_name]`

**Response:** `automation:property` → `[path, property_name, value]`

#### set_property

Set a property value on a node.

**Request:** `automation:set_property` → `[path, property_name, value]`

**Response:** `automation:set_result` → `[success_bool]`

#### call_method

Call a method on a node.

**Request:** `automation:call_method` → `[path, method_name, args_array]`

**Response:** `automation:call_result` → `[path, method_name, return_value]`

#### query_nodes

Query nodes matching a pattern.

**Request:** `automation:query_nodes` → `[pattern]`

**Response:** `automation:query_result` → `[paths_array]`

Pattern supports `*` wildcard: `/root/Main/Enemies/*`

#### count_nodes

Count nodes matching a pattern.

**Request:** `automation:count_nodes` → `[pattern]`

**Response:** `automation:count_result` → `[count_int]`

### Input Operations

#### mouse_button

Simulate a mouse button press/release.

**Request:** `automation:mouse_button` → `[x, y, button_index, pressed, double_click]`

- `x`, `y`: Screen coordinates (float)
- `button_index`: 1=left, 2=right, 3=middle
- `pressed`: true for press, false for release
- `double_click`: true for double-click event

**Response:** `automation:input_result` → `[success_bool]`

#### mouse_motion

Simulate mouse movement.

**Request:** `automation:mouse_motion` → `[x, y, rel_x, rel_y]`

**Response:** `automation:input_result` → `[success_bool]`

#### key

Simulate a key press/release.

**Request:** `automation:key` → `[keycode, pressed, physical]`

- `keycode`: Godot Key enum value
- `pressed`: true for press, false for release
- `physical`: true to use physical key location

**Response:** `automation:input_result` → `[success_bool]`

#### action

Simulate an input action.

**Request:** `automation:action` → `[action_name, pressed, strength]`

**Response:** `automation:input_result` → `[success_bool]`

#### touch

Simulate a touch event.

**Request:** `automation:touch` → `[index, x, y, pressed]`

**Response:** `automation:input_result` → `[success_bool]`

### Screenshot Operations

#### screenshot

Capture a screenshot.

**Request:** `automation:screenshot` → `[node_path_or_empty]`

**Response:** `automation:screenshot` → `[png_bytes]`

Returns raw PNG data as PackedByteArray.

### Scene Operations

#### get_current_scene

Get the current scene.

**Request:** `automation:get_current_scene` → `[]`

**Response:** `automation:current_scene` → `[scene_path, scene_name]`

#### change_scene

Change to a different scene.

**Request:** `automation:change_scene` → `[scene_path]`

**Response:** `automation:scene_changed` → `[success_bool]`

#### reload_scene

Reload the current scene.

**Request:** `automation:reload_scene` → `[]`

**Response:** `automation:scene_reloaded` → `[success_bool]`

### Game State Operations

#### pause

Pause or unpause the game.

**Request:** `automation:pause` → `[paused_bool]`

**Response:** `automation:pause_result` → `[current_paused_state]`

#### time_scale

Set the game time scale.

**Request:** `automation:time_scale` → `[scale_float]`

**Response:** `automation:time_scale_result` → `[current_scale]`

### Waiting Operations

#### wait_signal

Wait for a signal to be emitted.

**Request:** `automation:wait_signal` → `[signal_name, source_path, timeout_ms]`

- `signal_name`: Name of the signal to wait for
- `source_path`: Node path filter (empty string for any source)
- `timeout_ms`: Timeout in milliseconds

**Response:** `automation:wait_signal_result` → `[signal_name, args_array]`

## Example Session

```
# Python client starts TCP server on port 6007
# Python launches: godot --remote-debug tcp://localhost:6007 --path ./game

# Godot connects and sends initial debug messages
# Python captures thread_id from first message

# Python sends get_tree command:
→ ["automation:get_tree", 1, []]

# Godot responds with scene tree:
← ["automation:tree", 1, [{"name": "root", "path": "/root", "children": [...]}]]

# Python sends click command:
→ ["automation:mouse_button", 1, [960.0, 540.0, 1, true, false]]

# Godot responds:
← ["automation:input_result", 1, [true]]

# Python sends screenshot command:
→ ["automation:screenshot", 1, [""]]

# Godot responds with PNG data:
← ["automation:screenshot", 1, [<bytes: PNG data>]]
```

## Python Client Implementation

The `NativeClient` class in `playgodot/native_client.py` implements this protocol:

- `_params_to_data()`: Converts high-level API params to data arrays
- `_get_expected_response()`: Maps request commands to expected response names
- `_data_to_result()`: Converts response data arrays to Python dicts
- `_receive_loop()`: Background task that reads and dispatches responses

The `variant.py` module provides `encode_message()` and `decode_message()` for binary serialization.

## Comparison with WebSocket Approach

| Feature | Native Protocol | WebSocket (Addon) |
|---------|----------------|-------------------|
| Addon Required | No | Yes |
| Wire Format | Binary Variant | JSON-RPC |
| Port | 6007 (debugger) | 9999 (custom) |
| Setup | `--remote-debug` flag | Enable plugin |
| Efficiency | Higher | Lower |
