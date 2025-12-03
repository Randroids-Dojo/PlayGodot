# Patch 001: Automation Protocol

This document describes the first set of changes to add automation support to Godot's debugger.

## Overview

Extend the existing `RemoteDebugger` to handle automation commands, allowing external tools to:
- Query the scene tree
- Get/set node properties
- Call methods on nodes
- Capture screenshots

## Files Modified

### core/debugger/remote_debugger.h

```cpp
// Add to RemoteDebugger class private section:

private:
    // Automation support
    void _process_automation_message(const String &p_msg, const Array &p_data);
    void _send_scene_tree();
    void _send_node_info(const String &p_path);
    void _send_property(const String &p_path, const String &p_property);
    void _set_property(const String &p_path, const String &p_property, const Variant &p_value);
    void _call_method(const String &p_path, const String &p_method, const Array &p_args);
    Dictionary _serialize_node(Node *p_node);
```

### core/debugger/remote_debugger.cpp

```cpp
// Add to _process_messages() or create new handler:

void RemoteDebugger::_process_automation_message(const String &p_msg, const Array &p_data) {
    if (p_msg == "automation:get_tree") {
        _send_scene_tree();
    } else if (p_msg == "automation:get_node") {
        ERR_FAIL_COND(p_data.size() < 1);
        _send_node_info(p_data[0]);
    } else if (p_msg == "automation:get_property") {
        ERR_FAIL_COND(p_data.size() < 2);
        _send_property(p_data[0], p_data[1]);
    } else if (p_msg == "automation:set_property") {
        ERR_FAIL_COND(p_data.size() < 3);
        _set_property(p_data[0], p_data[1], p_data[2]);
    } else if (p_msg == "automation:call_method") {
        ERR_FAIL_COND(p_data.size() < 2);
        Array args = p_data.size() > 2 ? p_data[2] : Array();
        _call_method(p_data[0], p_data[1], args);
    }
}

void RemoteDebugger::_send_scene_tree() {
    SceneTree *tree = SceneTree::get_singleton();
    ERR_FAIL_NULL(tree);

    Node *root = tree->get_root();
    ERR_FAIL_NULL(root);

    Dictionary tree_data = _serialize_node(root);

    Array msg;
    msg.push_back(tree_data);
    EngineDebugger::get_singleton()->send_message("automation:tree", msg);
}

void RemoteDebugger::_send_node_info(const String &p_path) {
    SceneTree *tree = SceneTree::get_singleton();
    ERR_FAIL_NULL(tree);

    Node *node = tree->get_root()->get_node_or_null(NodePath(p_path));

    Array msg;
    if (node) {
        msg.push_back(_serialize_node(node));
    } else {
        msg.push_back(Variant()); // null
    }
    EngineDebugger::get_singleton()->send_message("automation:node", msg);
}

void RemoteDebugger::_send_property(const String &p_path, const String &p_property) {
    SceneTree *tree = SceneTree::get_singleton();
    ERR_FAIL_NULL(tree);

    Node *node = tree->get_root()->get_node_or_null(NodePath(p_path));

    Array msg;
    msg.push_back(p_path);
    msg.push_back(p_property);

    if (node) {
        msg.push_back(node->get(p_property));
    } else {
        msg.push_back(Variant());
    }
    EngineDebugger::get_singleton()->send_message("automation:property", msg);
}

void RemoteDebugger::_set_property(const String &p_path, const String &p_property, const Variant &p_value) {
    SceneTree *tree = SceneTree::get_singleton();
    ERR_FAIL_NULL(tree);

    Node *node = tree->get_root()->get_node_or_null(NodePath(p_path));

    bool success = false;
    if (node) {
        node->set(p_property, p_value);
        success = true;
    }

    Array msg;
    msg.push_back(success);
    EngineDebugger::get_singleton()->send_message("automation:set_result", msg);
}

void RemoteDebugger::_call_method(const String &p_path, const String &p_method, const Array &p_args) {
    SceneTree *tree = SceneTree::get_singleton();
    ERR_FAIL_NULL(tree);

    Node *node = tree->get_root()->get_node_or_null(NodePath(p_path));

    Array msg;
    msg.push_back(p_path);
    msg.push_back(p_method);

    if (node && node->has_method(p_method)) {
        Variant result = node->callv(p_method, p_args);
        msg.push_back(result);
    } else {
        msg.push_back(Variant());
    }
    EngineDebugger::get_singleton()->send_message("automation:call_result", msg);
}

Dictionary RemoteDebugger::_serialize_node(Node *p_node) {
    Dictionary data;
    data["name"] = p_node->get_name();
    data["path"] = String(p_node->get_path());
    data["class"] = p_node->get_class();

    // Add common properties
    if (Object::cast_to<Node2D>(p_node)) {
        Node2D *n2d = Object::cast_to<Node2D>(p_node);
        data["position"] = n2d->get_position();
        data["rotation"] = n2d->get_rotation();
        data["scale"] = n2d->get_scale();
        data["visible"] = n2d->is_visible();
    } else if (Object::cast_to<Control>(p_node)) {
        Control *ctrl = Object::cast_to<Control>(p_node);
        data["position"] = ctrl->get_position();
        data["size"] = ctrl->get_size();
        data["visible"] = ctrl->is_visible();
    } else if (Object::cast_to<Node3D>(p_node)) {
        Node3D *n3d = Object::cast_to<Node3D>(p_node);
        data["position"] = n3d->get_position();
        data["rotation"] = n3d->get_rotation();
        data["scale"] = n3d->get_scale();
        data["visible"] = n3d->is_visible();
    }

    // Add children
    Array children;
    for (int i = 0; i < p_node->get_child_count(); i++) {
        children.push_back(_serialize_node(p_node->get_child(i)));
    }
    data["children"] = children;

    return data;
}
```

### core/debugger/engine_debugger.cpp

```cpp
// Register the automation capture in EngineDebugger::initialize():

void EngineDebugger::initialize(...) {
    // ... existing code ...

    // Register automation message capture
    register_message_capture("automation", EngineDebugger::Capture(nullptr, [](void *, const String &p_msg, const Array &p_data, bool &r_captured) {
        if (remote_debugger) {
            remote_debugger->_process_automation_message(p_msg, p_data);
            r_captured = true;
        }
        return true;
    }));
}
```

## Command Line Flag

Add `--automation` flag to enable automation server on a specific port:

```cpp
// main/main.cpp
if (I->get() == "--automation") {
    // Enable automation mode
    Engine::get_singleton()->set_automation_enabled(true);
}

if (I->get() == "--automation-port") {
    // Next arg is port
    N = I->next();
    if (N) {
        Engine::get_singleton()->set_automation_port(N->get().to_int());
    }
}
```

## Testing

After applying this patch:

```bash
# Run game with automation enabled
godot --path /path/to/game --automation --automation-port 9999

# PlayGodot can now connect via the debugger protocol
# instead of requiring the addon
```

## Next Patches

- `002-input-injection.md` - Native input injection
- `003-screenshot-capture.md` - Headless screenshot support
- `004-signal-subscription.md` - Subscribe to signals from external process
