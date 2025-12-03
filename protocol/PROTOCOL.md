# PlayGodot Protocol Specification

PlayGodot uses **JSON-RPC 2.0** over **WebSocket** for communication between external clients (Python, etc.) and the Godot game.

## Connection

- Default port: `9999`
- Protocol: WebSocket
- URL format: `ws://localhost:9999`

The port can be configured via:
- Command line: `--playgodot-port 8888`
- Environment variable: `PLAYGODOT_PORT=8888`

## Message Format

### Request

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "method_name",
  "params": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

- `jsonrpc`: Always "2.0"
- `id`: Unique request identifier (integer or string)
- `method`: The RPC method to call
- `params`: Optional method parameters (object)

### Success Response

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "key": "value"
  }
}
```

### Error Response

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32000,
    "message": "Error description"
  }
}
```

## Error Codes

| Code | Meaning |
|------|---------|
| -32700 | Parse error - Invalid JSON |
| -32600 | Invalid Request - Missing required fields |
| -32601 | Method not found |
| -32602 | Invalid params |
| -32000 | Server error - Node not found |
| -32001 | Server error - Timeout |

## Methods

### Node Operations

#### get_node

Get information about a node.

**Params:**
- `path` (string, required): Node path (e.g., "/root/Main/Player")

**Result:**
```json
{
  "path": "/root/Main/Player",
  "name": "Player",
  "class": "CharacterBody2D",
  "position": {"x": 100, "y": 200},
  "visible": true
}
```

#### get_property

Get a property value from a node.

**Params:**
- `path` (string, required): Node path
- `property` (string, required): Property name

**Result:**
```json
{
  "value": 100
}
```

#### set_property

Set a property value on a node.

**Params:**
- `path` (string, required): Node path
- `property` (string, required): Property name
- `value` (any, required): New value

**Result:**
```json
{
  "success": true
}
```

#### call_method

Call a method on a node.

**Params:**
- `path` (string, required): Node path
- `method` (string, required): Method name
- `args` (array, optional): Method arguments

**Result:**
```json
{
  "value": "return_value"
}
```

#### node_exists

Check if a node exists.

**Params:**
- `path` (string, required): Node path

**Result:**
```json
{
  "exists": true
}
```

#### query_nodes

Query nodes matching a pattern.

**Params:**
- `pattern` (string, required): Node path pattern (supports * wildcard)

**Result:**
```json
{
  "nodes": [
    {"path": "/root/Main/Enemy1", "name": "Enemy1", "class": "CharacterBody2D"},
    {"path": "/root/Main/Enemy2", "name": "Enemy2", "class": "CharacterBody2D"}
  ]
}
```

#### count_nodes

Count nodes matching a pattern.

**Params:**
- `pattern` (string, required): Node path pattern

**Result:**
```json
{
  "count": 5
}
```

#### get_children

Get children of a node.

**Params:**
- `path` (string, required): Parent node path

**Result:**
```json
{
  "children": [
    {"path": "/root/Main/Child1", "name": "Child1", "class": "Node2D"},
    {"path": "/root/Main/Child2", "name": "Child2", "class": "Sprite2D"}
  ]
}
```

### Input Operations

#### click

Simulate a mouse click at coordinates.

**Params:**
- `x` (number, required): X coordinate
- `y` (number, required): Y coordinate
- `button` (string, optional): "left" (default), "right", or "middle"

**Result:**
```json
{
  "clicked": true,
  "position": {"x": 100, "y": 200}
}
```

#### click_node

Simulate a mouse click on a node.

**Params:**
- `path` (string, required): Node path
- `button` (string, optional): Mouse button

**Result:**
```json
{
  "clicked": true,
  "position": {"x": 150, "y": 250}
}
```

#### double_click

Simulate a double-click at coordinates.

**Params:**
- `x` (number, required): X coordinate
- `y` (number, required): Y coordinate

**Result:**
```json
{
  "double_clicked": true
}
```

#### move_mouse

Move the mouse to coordinates.

**Params:**
- `x` (number, required): X coordinate
- `y` (number, required): Y coordinate

**Result:**
```json
{
  "position": {"x": 100, "y": 200}
}
```

#### drag

Simulate a drag operation.

**Params:**
- `from_x` (number, required): Starting X
- `from_y` (number, required): Starting Y
- `to_x` (number, required): Ending X
- `to_y` (number, required): Ending Y
- `duration` (number, optional): Duration in seconds (default: 0.5)

**Result:**
```json
{
  "dragged": true
}
```

#### press_key

Simulate a key press.

**Params:**
- `key` (string, required): Key name (e.g., "space", "enter", "a")
- `modifiers` (array, optional): Modifier keys (e.g., ["ctrl", "shift"])

**Result:**
```json
{
  "pressed": "space"
}
```

#### type_text

Type a string of text.

**Params:**
- `text` (string, required): Text to type
- `delay` (number, optional): Delay between keystrokes in seconds (default: 0.05)

**Result:**
```json
{
  "typed": "Hello, World!"
}
```

#### press_action

Press an input action (as defined in Input Map).

**Params:**
- `action` (string, required): Action name

**Result:**
```json
{
  "pressed": "jump"
}
```

#### hold_action

Hold an input action for a duration.

**Params:**
- `action` (string, required): Action name
- `duration` (number, required): Duration in seconds

**Result:**
```json
{
  "held": "run",
  "duration": 2.0
}
```

#### tap

Simulate a touch tap.

**Params:**
- `x` (number, required): X coordinate
- `y` (number, required): Y coordinate

**Result:**
```json
{
  "tapped": true,
  "position": {"x": 100, "y": 200}
}
```

#### swipe

Simulate a swipe gesture.

**Params:**
- `from_x` (number, required): Starting X
- `from_y` (number, required): Starting Y
- `to_x` (number, required): Ending X
- `to_y` (number, required): Ending Y
- `duration` (number, optional): Duration in seconds (default: 0.3)

**Result:**
```json
{
  "swiped": true
}
```

#### pinch

Simulate a pinch gesture.

**Params:**
- `center_x` (number, required): Center X coordinate
- `center_y` (number, required): Center Y coordinate
- `scale` (number, required): Scale factor (< 1 for pinch in, > 1 for pinch out)
- `duration` (number, optional): Duration in seconds (default: 0.3)

**Result:**
```json
{
  "pinched": true,
  "scale": 0.5
}
```

### Screenshot Operations

#### screenshot

Capture a screenshot.

**Params:**
- `node` (string, optional): Node path to capture (captures full viewport if not specified)

**Result:**
```json
{
  "data": "base64_encoded_png_data",
  "width": 1920,
  "height": 1080,
  "format": "png"
}
```

### Waiting Operations

#### wait_signal

Wait for a signal to be emitted.

**Params:**
- `signal` (string, required): Signal name
- `source` (string, optional): Source node path
- `timeout` (number, optional): Timeout in milliseconds (default: 30000)

**Result:**
```json
{
  "signal": "game_over",
  "args": []
}
```

#### wait_frames

Wait for a number of frames.

**Params:**
- `count` (integer, required): Number of frames

**Result:**
```json
{
  "frames": 60
}
```

#### wait_seconds

Wait for a number of seconds (game time).

**Params:**
- `seconds` (number, required): Seconds to wait

**Result:**
```json
{
  "seconds": 2.0
}
```

### Scene Operations

#### get_current_scene

Get the current scene path.

**Params:** None

**Result:**
```json
{
  "path": "res://scenes/main.tscn"
}
```

#### change_scene

Change to a different scene.

**Params:**
- `path` (string, required): Scene resource path

**Result:**
```json
{
  "success": true
}
```

#### reload_scene

Reload the current scene.

**Params:** None

**Result:**
```json
{
  "success": true
}
```

#### get_tree

Get the scene tree structure.

**Params:** None

**Result:**
```json
{
  "path": "/root",
  "name": "root",
  "class": "Window",
  "children": [
    {
      "path": "/root/Main",
      "name": "Main",
      "class": "Node2D",
      "children": []
    }
  ]
}
```

### Game State Operations

#### pause

Pause the game.

**Params:** None

**Result:**
```json
{
  "paused": true
}
```

#### unpause

Unpause the game.

**Params:** None

**Result:**
```json
{
  "paused": false
}
```

#### set_time_scale

Set the game time scale.

**Params:**
- `scale` (number, required): Time scale (1.0 = normal)

**Result:**
```json
{
  "time_scale": 0.5
}
```

## Type Serialization

### Vector2
```json
{"x": 100.0, "y": 200.0}
```

### Vector3
```json
{"x": 1.0, "y": 2.0, "z": 3.0}
```

### Color
```json
{"r": 1.0, "g": 0.5, "b": 0.0, "a": 1.0}
```

### Node References
Serialized as their path string:
```json
"/root/Main/Player"
```

## Example Session

```
Client -> Server:
{"jsonrpc":"2.0","id":1,"method":"get_node","params":{"path":"/root/Main/Player"}}

Server -> Client:
{"jsonrpc":"2.0","id":1,"result":{"path":"/root/Main/Player","name":"Player","class":"CharacterBody2D","position":{"x":100,"y":200},"visible":true}}

Client -> Server:
{"jsonrpc":"2.0","id":2,"method":"click_node","params":{"path":"/root/Main/UI/StartButton"}}

Server -> Client:
{"jsonrpc":"2.0","id":2,"result":{"clicked":true,"position":{"x":960,"y":540}}}

Client -> Server:
{"jsonrpc":"2.0","id":3,"method":"screenshot","params":{}}

Server -> Client:
{"jsonrpc":"2.0","id":3,"result":{"data":"iVBORw0KGgo...","width":1920,"height":1080,"format":"png"}}
```
