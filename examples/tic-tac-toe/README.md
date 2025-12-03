# Tic-Tac-Toe Example

This example demonstrates how to use PlayGodot to test a simple Tic-Tac-Toe game.

## Structure

```
tic-tac-toe/
├── godot/              # Godot project
│   ├── project.godot
│   ├── scenes/
│   │   └── main.tscn
│   └── scripts/
│       └── game.gd
├── tests/              # Python tests
│   ├── conftest.py
│   └── test_game.py
└── README.md
```

## Running Tests

1. Install PlayGodot:
   ```bash
   pip install playgodot pytest pytest-asyncio
   ```

2. Run the tests:
   ```bash
   pytest tests/ -v
   ```

## Example Test

```python
import pytest
from playgodot import Godot

@pytest.fixture
async def game():
    async with Godot.launch("godot/") as g:
        await g.wait_for_node("/root/Main")
        yield g

@pytest.mark.asyncio
async def test_x_wins_diagonal(game):
    """Test that X can win with a diagonal."""
    # X moves
    await game.click("/root/Main/Board/Cell0")  # Top-left
    await game.click("/root/Main/Board/Cell3")  # O moves middle-left
    await game.click("/root/Main/Board/Cell4")  # X moves center
    await game.click("/root/Main/Board/Cell6")  # O moves bottom-left
    await game.click("/root/Main/Board/Cell8")  # X moves bottom-right (wins)

    # Check for win
    result = await game.call("/root/Main", "get_winner")
    assert result == "X"
```

## What This Example Demonstrates

- Launching a Godot project from tests
- Waiting for nodes to exist
- Clicking on game elements
- Calling game methods to verify state
- Using pytest fixtures for setup/teardown
