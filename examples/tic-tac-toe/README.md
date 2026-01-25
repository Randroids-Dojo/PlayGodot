# Tic-Tac-Toe Example

A complete working example demonstrating PlayGodot for testing a simple Tic-Tac-Toe game.

## Structure

```
tic-tac-toe/
├── godot/                  # Godot 4.x project
│   ├── project.godot       # Project configuration
│   ├── main.tscn           # Main scene
│   └── main.gd             # Game logic
├── tests/                  # Python tests
│   ├── conftest.py         # Pytest fixtures
│   └── test_game.py        # Game tests
└── README.md
```

## The Game

A simple 3x3 Tic-Tac-Toe game with:
- X goes first
- Click cells to place marks
- Win detection (rows, columns, diagonals)
- Draw detection
- Restart button

### Game API

The game exposes these methods for testing:

```gdscript
get_board() -> Array[String]      # Get current board state
get_current_player() -> String    # "X" or "O"
get_winner() -> String            # "X", "O", "Draw", or ""
is_game_active() -> bool          # True if game in progress
make_move(index: int) -> bool     # Programmatic move
get_cell_text(index: int) -> String
```

### Signals

```gdscript
signal game_over(winner: String)
signal turn_changed(player: String)
```

## Running Tests

1. Install dependencies:
   ```bash
   cd /path/to/PlayGodot/python
   pip install -e ".[dev]"
   ```

2. Run the tests:
   ```bash
   cd /path/to/PlayGodot/examples/tic-tac-toe
   pytest tests/ -v
   ```

## Test Examples

### Basic game state

```python
@pytest.mark.asyncio
async def test_game_starts_with_empty_board(game):
    board = await game.call("/root/Main", "get_board")
    assert board == ["", "", "", "", "", "", "", "", ""]
```

### Clicking cells

```python
@pytest.mark.asyncio
async def test_clicking_cell_makes_move(game):
    await game.click("/root/Main/Board/Cell4")
    cell_text = await game.call("/root/Main", "get_cell_text", [4])
    assert cell_text == "X"
```

### Win detection

```python
@pytest.mark.asyncio
async def test_x_wins_top_row(game):
    await game.click("/root/Main/Board/Cell0")  # X
    await game.click("/root/Main/Board/Cell3")  # O
    await game.click("/root/Main/Board/Cell1")  # X
    await game.click("/root/Main/Board/Cell4")  # O
    await game.click("/root/Main/Board/Cell2")  # X wins

    winner = await game.call("/root/Main", "get_winner")
    assert winner == "X"
```

## What This Example Demonstrates

- **Launching games** - `Godot.launch()` starts the game headlessly
- **Waiting for nodes** - `wait_for_node()` ensures scene is ready
- **Clicking UI** - `click()` simulates mouse input on buttons
- **Calling methods** - `call()` invokes game methods directly
- **Reading properties** - `get_property()` reads node properties
- **Pytest fixtures** - Clean setup/teardown for each test
