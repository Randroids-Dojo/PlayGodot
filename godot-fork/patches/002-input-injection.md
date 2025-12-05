# Patch 002: Input Injection

This document describes the changes to add input injection support to Godot's automation protocol.

## Overview

Extend the automation protocol to support injecting input events, allowing external tools to:
- Simulate mouse clicks and movement
- Simulate keyboard input
- Simulate touch events
- Trigger game actions

## Files Modified

### core/debugger/remote_debugger.h

```cpp
// Add to RemoteDebugger class private section (after existing automation methods):

	// Input injection for automation
	void _inject_mouse_button(const Vector2 &p_position, int p_button, bool p_pressed);
	void _inject_mouse_motion(const Vector2 &p_position, const Vector2 &p_relative);
	void _inject_key(int p_keycode, bool p_pressed, bool p_physical = false);
	void _inject_touch(int p_index, const Vector2 &p_position, bool p_pressed);
	void _inject_action(const String &p_action, bool p_pressed, float p_strength = 1.0f);
```

### core/debugger/remote_debugger.cpp

Add include for input events:

```cpp
#include "core/input/input_event.h"
```

Extend `_automation_capture()` to handle input commands:

```cpp
} else if (p_cmd == "mouse_button") {
    // mouse_button: [x, y, button_index, pressed]
    ERR_FAIL_COND_V(p_data.size() < 4, ERR_INVALID_DATA);
    Vector2 pos(p_data[0], p_data[1]);
    _inject_mouse_button(pos, p_data[2], p_data[3]);
} else if (p_cmd == "mouse_motion") {
    // mouse_motion: [x, y, relative_x, relative_y]
    ERR_FAIL_COND_V(p_data.size() < 4, ERR_INVALID_DATA);
    Vector2 pos(p_data[0], p_data[1]);
    Vector2 rel(p_data[2], p_data[3]);
    _inject_mouse_motion(pos, rel);
} else if (p_cmd == "key") {
    // key: [keycode, pressed, physical?]
    ERR_FAIL_COND_V(p_data.size() < 2, ERR_INVALID_DATA);
    bool physical = p_data.size() > 2 ? (bool)p_data[2] : false;
    _inject_key(p_data[0], p_data[1], physical);
} else if (p_cmd == "touch") {
    // touch: [index, x, y, pressed]
    ERR_FAIL_COND_V(p_data.size() < 4, ERR_INVALID_DATA);
    Vector2 pos(p_data[1], p_data[2]);
    _inject_touch(p_data[0], pos, p_data[3]);
} else if (p_cmd == "action") {
    // action: [action_name, pressed, strength?]
    ERR_FAIL_COND_V(p_data.size() < 2, ERR_INVALID_DATA);
    float strength = p_data.size() > 2 ? (float)p_data[2] : 1.0f;
    _inject_action(p_data[0], p_data[1], strength);
}
```

Add implementation methods:

```cpp
void RemoteDebugger::_inject_mouse_button(const Vector2 &p_position, int p_button, bool p_pressed) {
    Input *input = Input::get_singleton();
    ERR_FAIL_NULL(input);

    Ref<InputEventMouseButton> ev;
    ev.instantiate();
    ev->set_device(InputEvent::DEVICE_ID_EMULATION);
    ev->set_position(p_position);
    ev->set_global_position(p_position);
    ev->set_button_index((MouseButton)p_button);
    ev->set_pressed(p_pressed);

    input->parse_input_event(ev);

    Array msg;
    msg.push_back(true);
    EngineDebugger::get_singleton()->send_message("automation:input_result", msg);
}

void RemoteDebugger::_inject_mouse_motion(const Vector2 &p_position, const Vector2 &p_relative) {
    Input *input = Input::get_singleton();
    ERR_FAIL_NULL(input);

    Ref<InputEventMouseMotion> ev;
    ev.instantiate();
    ev->set_device(InputEvent::DEVICE_ID_EMULATION);
    ev->set_position(p_position);
    ev->set_global_position(p_position);
    ev->set_relative(p_relative);

    input->parse_input_event(ev);

    Array msg;
    msg.push_back(true);
    EngineDebugger::get_singleton()->send_message("automation:input_result", msg);
}

void RemoteDebugger::_inject_key(int p_keycode, bool p_pressed, bool p_physical) {
    Input *input = Input::get_singleton();
    ERR_FAIL_NULL(input);

    Ref<InputEventKey> ev;
    ev.instantiate();
    ev->set_device(InputEvent::DEVICE_ID_EMULATION);
    ev->set_pressed(p_pressed);

    if (p_physical) {
        ev->set_physical_keycode((Key)p_keycode);
    } else {
        ev->set_keycode((Key)p_keycode);
    }

    input->parse_input_event(ev);

    Array msg;
    msg.push_back(true);
    EngineDebugger::get_singleton()->send_message("automation:input_result", msg);
}

void RemoteDebugger::_inject_touch(int p_index, const Vector2 &p_position, bool p_pressed) {
    Input *input = Input::get_singleton();
    ERR_FAIL_NULL(input);

    Ref<InputEventScreenTouch> ev;
    ev.instantiate();
    ev->set_device(InputEvent::DEVICE_ID_EMULATION);
    ev->set_index(p_index);
    ev->set_position(p_position);
    ev->set_pressed(p_pressed);

    input->parse_input_event(ev);

    Array msg;
    msg.push_back(true);
    EngineDebugger::get_singleton()->send_message("automation:input_result", msg);
}

void RemoteDebugger::_inject_action(const String &p_action, bool p_pressed, float p_strength) {
    Input *input = Input::get_singleton();
    ERR_FAIL_NULL(input);

    if (p_pressed) {
        input->action_press(p_action, p_strength);
    } else {
        input->action_release(p_action);
    }

    Array msg;
    msg.push_back(true);
    EngineDebugger::get_singleton()->send_message("automation:input_result", msg);
}
```

## Automation Commands

### Mouse Button
```
automation:mouse_button [x, y, button_index, pressed]
```
- `x`, `y`: Screen coordinates
- `button_index`: 1=left, 2=right, 3=middle
- `pressed`: true for press, false for release

### Mouse Motion
```
automation:mouse_motion [x, y, relative_x, relative_y]
```
- `x`, `y`: New absolute position
- `relative_x`, `relative_y`: Movement delta

### Key
```
automation:key [keycode, pressed, physical?]
```
- `keycode`: Key constant (see `core/os/keyboard.h`)
- `pressed`: true for press, false for release
- `physical`: (optional) true to use physical keycode

### Touch
```
automation:touch [index, x, y, pressed]
```
- `index`: Touch point index (0-9)
- `x`, `y`: Screen coordinates
- `pressed`: true for touch down, false for touch up

### Action
```
automation:action [action_name, pressed, strength?]
```
- `action_name`: Name of the input action (e.g., "ui_accept", "jump")
- `pressed`: true for press, false for release
- `strength`: (optional) Action strength 0.0-1.0, defaults to 1.0

## Response

All input commands respond with:
```
automation:input_result [success]
```

## Testing

After applying this patch:

```python
# Example: Click at position (100, 200)
await godot.send_command("automation:mouse_button", [100, 200, 1, True])   # press
await godot.send_command("automation:mouse_button", [100, 200, 1, False])  # release

# Example: Press the spacebar
await godot.send_command("automation:key", [32, True])   # Key.SPACE = 32
await godot.send_command("automation:key", [32, False])

# Example: Trigger the "jump" action
await godot.send_command("automation:action", ["jump", True, 1.0])
await godot.send_command("automation:action", ["jump", False])
```

## Next Patches

- `003-screenshot-capture.md` - Headless screenshot support
- `004-signal-subscription.md` - Subscribe to signals from external process
