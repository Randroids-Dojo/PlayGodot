# PlayGodot Python Client

Python client library for PlayGodot - external automation and testing framework for Godot Engine games.

## Installation

```bash
pip install playgodot
```

For screenshot comparison support:

```bash
pip install playgodot[image]
```

## Quick Start

```python
import asyncio
from playgodot import Godot

async def test_game():
    async with Godot.launch("path/to/project") as game:
        # Wait for game to be ready
        await game.wait_for_node("/root/Main")

        # Interact with the game
        await game.click("/root/Main/UI/StartButton")
        await game.wait_for_signal("game_started")

        # Take a screenshot
        await game.screenshot("game_started.png")

asyncio.run(test_game())
```

## Documentation

See the [main README](../README.md) for full documentation.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy playgodot

# Linting
ruff check playgodot
```
