# Godot Fork for PlayGodot Automation

This directory contains resources for maintaining a Godot Engine fork with native automation support.

## Fork Setup

### 1. Create the Fork on GitHub

Go to https://github.com/godotengine/godot and click "Fork" to create `Randroids-Dojo/godot`.

### 2. Clone and Set Up Branches

```bash
# Clone your fork
git clone https://github.com/Randroids-Dojo/godot.git
cd godot

# Add upstream remote
git remote add upstream https://github.com/godotengine/godot.git

# Create automation branch from master
git checkout -b automation
git push -u origin automation
```

### 3. Copy Workflow Files

Copy these files to your fork's `.github/workflows/`:

- `sync-upstream.yml` - Nightly rebase on upstream
- `build-automation.yml` - Build Godot with automation features
- `playgodot-integration.yml` - Run PlayGodot tests against builds

```bash
cp /path/to/PlayGodot/godot-fork/workflows/*.yml .github/workflows/
git add .github/workflows/
git commit -m "Add CI workflows for automation fork"
git push
```

## Branch Strategy

```
godotengine/godot:master ─────────────────────────────►
                           ↓ nightly rebase
Randroids-Dojo/godot:automation ──●──●──●──●──●──────►
                                   └── our automation commits
```

## Implementation Status

The `automation` branch at [Randroids-Dojo/godot](https://github.com/Randroids-Dojo/godot/tree/automation) includes:

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Automation Protocol | ✅ Complete |
| 2 | Input Injection | ✅ Complete |
| 3 | Headless Screenshots | ⏳ Planned |

## Files Modified in Godot

### Phase 1: Automation Protocol ✅

```
core/debugger/
├── remote_debugger.cpp    # Automation message handlers implemented
├── remote_debugger.h      # Automation methods declared
└── (registered in RemoteDebugger constructor)
```

**Commands supported:**
- `automation:get_tree` - Get full scene tree
- `automation:get_node` - Get node by path
- `automation:get_property` - Get property value
- `automation:set_property` - Set property value
- `automation:call_method` - Call method on node

### Phase 2: Input Injection ✅

```
core/debugger/
├── remote_debugger.cpp    # Input injection methods added
└── remote_debugger.h      # Input injection methods declared
```

**Commands supported:**
- `automation:mouse_button` - Click at position
- `automation:mouse_motion` - Move mouse
- `automation:key` - Press/release keyboard key
- `automation:touch` - Touch screen input
- `automation:action` - Trigger game actions

### Phase 3: Headless Screenshots (Planned)

```
servers/rendering/
└── rendering_server_default.cpp  # Ensure headless capture works
```

## Building Locally

```bash
# Install dependencies (Ubuntu)
sudo apt-get install build-essential scons pkg-config \
    libx11-dev libxcursor-dev libxinerama-dev libgl1-mesa-dev \
    libglu1-mesa-dev libasound2-dev libpulse-dev libfreetype6-dev \
    libssl-dev libudev-dev libxi-dev libxrandr-dev

# Build editor (debug)
scons platform=linuxbsd target=editor -j$(nproc)

# Build template (for running games)
scons platform=linuxbsd target=template_debug -j$(nproc)

# Binaries output to bin/
ls bin/
# godot.linuxbsd.editor.x86_64
# godot.linuxbsd.template_debug.x86_64
```

## Testing with PlayGodot

Once built, test against the tic-tac-toe example:

```bash
export PATH="/path/to/godot/bin:$PATH"
cd /path/to/PlayGodot/examples/tic-tac-toe
pytest tests/ -v
```
