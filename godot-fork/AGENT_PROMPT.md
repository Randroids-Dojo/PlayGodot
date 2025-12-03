# Godot Fork Setup: Native Automation Support

## Context

You are setting up a Godot Engine fork (`Randroids-Dojo/godot`) to add native automation capabilities. This fork will enable external tools to control and test Godot games without requiring an addon - similar to how Chrome DevTools Protocol enables Playwright to automate browsers.

The companion project **PlayGodot** (`Randroids-Dojo/PlayGodot`) is a Python client that will use these native automation features to test Godot games.

## Repository State

- Fork: `Randroids-Dojo/godot` (forked from `godotengine/godot`)
- Branch: `automation` (already created, based on `master`)
- Reference: `Randroids-Dojo/PlayGodot` contains workflow templates in `godot-fork/workflows/`

## Tasks

### 1. Set Up CI Workflows

Copy these workflows from PlayGodot to the Godot fork's `.github/workflows/`:

**From:** `Randroids-Dojo/PlayGodot/godot-fork/workflows/`
**To:** `Randroids-Dojo/godot/.github/workflows/`

Files:
- `sync-upstream.yml` - Nightly rebase on `godotengine/godot:master`
- `build-automation.yml` - Build Godot with automation features for Linux/Windows/macOS

Commit message: `Add CI workflows for automation fork`

### 2. Implement Automation Protocol (Phase 1)

Extend Godot's existing debugger to handle automation commands. This builds on the existing `EngineDebugger` infrastructure.

#### Files to Modify

**`core/debugger/remote_debugger.h`**

Add to the `RemoteDebugger` class private section:

```cpp
// Automation support
void _process_automation_message(const String &p_msg, const Array &p_data);
void _send_scene_tree();
void _send_node_info(const String &p_path);
void _send_property(const String &p_path, const String &p_property);
void _set_property(const String &p_path, const String &p_property, const Variant &p_value);
void _call_method(const String &p_path, const String &p_method, const Array &p_args);
Dictionary _serialize_node(Node *p_node);
```

**`core/debugger/remote_debugger.cpp`**

Add these method implementations:

```cpp
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
        msg.push_back(Variant());
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

    // Add position/visibility for common node types
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

    // Recurse children
    Array children;
    for (int i = 0; i < p_node->get_child_count(); i++) {
        children.push_back(_serialize_node(p_node->get_child(i)));
    }
    data["children"] = children;

    return data;
}
```

**`core/debugger/engine_debugger.cpp`**

In `EngineDebugger::initialize()`, register the automation message capture:

```cpp
// Add after other register_message_capture calls:
register_message_capture("automation", EngineDebugger::Capture(nullptr,
    [](void *, const String &p_msg, const Array &p_data, bool &r_captured) {
        RemoteDebugger *rd = dynamic_cast<RemoteDebugger *>(get_singleton());
        if (rd) {
            rd->_process_automation_message(p_msg, p_data);
            r_captured = true;
        }
        return true;
    }));
```

You may need to add includes:
```cpp
#include "scene/main/scene_tree.h"
#include "scene/main/node.h"
#include "scene/2d/node_2d.h"
#include "scene/3d/node_3d.h"
#include "scene/gui/control.h"
```

### 3. Commit the Changes

```bash
git add core/debugger/
git commit -m "Add automation protocol to debugger

Extend RemoteDebugger with automation commands:
- automation:get_tree - Get full scene tree
- automation:get_node - Get node info by path
- automation:get_property - Get node property
- automation:set_property - Set node property
- automation:call_method - Call node method

This enables external tools like PlayGodot to control
Godot games via the existing debugger infrastructure."

git push origin automation
```

### 4. Verify Build

The CI should automatically build. You can also build locally:

```bash
# Install dependencies (Ubuntu)
sudo apt-get install build-essential scons pkg-config \
    libx11-dev libxcursor-dev libxinerama-dev libgl1-mesa-dev \
    libglu1-mesa-dev libasound2-dev libpulse-dev libfreetype6-dev \
    libssl-dev libudev-dev libxi-dev libxrandr-dev

# Build
scons platform=linuxbsd target=editor -j$(nproc)
```

## Success Criteria

1. ✅ Workflows are in `.github/workflows/`
2. ✅ `sync-upstream.yml` runs nightly and rebases on upstream
3. ✅ `build-automation.yml` builds Godot successfully
4. ✅ Automation protocol code compiles without errors
5. ✅ CI uploads build artifacts

## Future Phases (Not This Task)

- Phase 2: Input injection (`Input::inject_event()`)
- Phase 3: Screenshot capture in headless mode
- Phase 4: Signal subscription from external process

## Reference

- PlayGodot repo: https://github.com/Randroids-Dojo/PlayGodot
- Godot debugger docs: https://docs.godotengine.org/en/stable/tutorials/scripting/debug/overview_of_debugging_tools.html
- Existing debugger code: `core/debugger/remote_debugger.cpp`
