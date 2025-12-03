"""Tests for the Tic Tac Toe game using PlayGodot."""

import pytest


@pytest.mark.asyncio
async def test_game_starts_with_empty_board(game):
    """Game should start with an empty board."""
    board = await game.call("/root/Main", "get_board")
    assert board == ["", "", "", "", "", "", "", "", ""]


@pytest.mark.asyncio
async def test_game_starts_with_x_turn(game):
    """X should go first."""
    player = await game.call("/root/Main", "get_current_player")
    assert player == "X"


@pytest.mark.asyncio
async def test_game_is_active_on_start(game):
    """Game should be active when starting."""
    active = await game.call("/root/Main", "is_game_active")
    assert active is True


@pytest.mark.asyncio
async def test_clicking_cell_makes_move(game):
    """Clicking a cell should place the current player's mark."""
    # Click the center cell (Cell4)
    await game.click("/root/Main/Board/Cell4")

    # Check the board
    cell_text = await game.call("/root/Main", "get_cell_text", [4])
    assert cell_text == "X"


@pytest.mark.asyncio
async def test_players_alternate(game):
    """Players should alternate turns."""
    # X plays
    await game.click("/root/Main/Board/Cell0")
    player = await game.call("/root/Main", "get_current_player")
    assert player == "O"

    # O plays
    await game.click("/root/Main/Board/Cell1")
    player = await game.call("/root/Main", "get_current_player")
    assert player == "X"


@pytest.mark.asyncio
async def test_cannot_click_occupied_cell(game):
    """Clicking an occupied cell should not change it."""
    # X plays center
    await game.click("/root/Main/Board/Cell4")

    # O tries to play center (should fail)
    await game.click("/root/Main/Board/Cell4")

    # Cell should still be X
    cell_text = await game.call("/root/Main", "get_cell_text", [4])
    assert cell_text == "X"

    # Should still be O's turn
    player = await game.call("/root/Main", "get_current_player")
    assert player == "O"


@pytest.mark.asyncio
async def test_x_wins_top_row(game):
    """X should win with top row."""
    # X: 0, O: 3, X: 1, O: 4, X: 2 (wins)
    await game.click("/root/Main/Board/Cell0")  # X
    await game.click("/root/Main/Board/Cell3")  # O
    await game.click("/root/Main/Board/Cell1")  # X
    await game.click("/root/Main/Board/Cell4")  # O
    await game.click("/root/Main/Board/Cell2")  # X wins

    winner = await game.call("/root/Main", "get_winner")
    assert winner == "X"

    active = await game.call("/root/Main", "is_game_active")
    assert active is False


@pytest.mark.asyncio
async def test_o_wins_diagonal(game):
    """O should win with diagonal."""
    # X: 1, O: 0, X: 5, O: 4, X: 6, O: 8 (wins)
    await game.click("/root/Main/Board/Cell1")  # X
    await game.click("/root/Main/Board/Cell0")  # O
    await game.click("/root/Main/Board/Cell5")  # X
    await game.click("/root/Main/Board/Cell4")  # O
    await game.click("/root/Main/Board/Cell6")  # X
    await game.click("/root/Main/Board/Cell8")  # O wins

    winner = await game.call("/root/Main", "get_winner")
    assert winner == "O"


@pytest.mark.asyncio
async def test_draw_game(game):
    """Game should end in draw when board is full with no winner."""
    # Play a draw game:
    # X O X
    # X X O
    # O X O
    moves = [0, 1, 2, 4, 3, 5, 7, 6, 8]  # Results in draw
    for move in moves:
        await game.click(f"/root/Main/Board/Cell{move}")

    winner = await game.call("/root/Main", "get_winner")
    assert winner == "Draw"


@pytest.mark.asyncio
async def test_restart_button_resets_game(game):
    """Restart button should reset the game."""
    # Make some moves
    await game.click("/root/Main/Board/Cell0")
    await game.click("/root/Main/Board/Cell1")

    # Click restart
    await game.click("/root/Main/RestartButton")

    # Board should be empty
    board = await game.call("/root/Main", "get_board")
    assert board == ["", "", "", "", "", "", "", "", ""]

    # Should be X's turn
    player = await game.call("/root/Main", "get_current_player")
    assert player == "X"

    # Game should be active
    active = await game.call("/root/Main", "is_game_active")
    assert active is True


@pytest.mark.asyncio
async def test_game_over_signal_emitted(game):
    """game_over signal should be emitted when game ends."""
    # Play to X wins
    await game.click("/root/Main/Board/Cell0")  # X
    await game.click("/root/Main/Board/Cell3")  # O
    await game.click("/root/Main/Board/Cell1")  # X
    await game.click("/root/Main/Board/Cell4")  # O

    # This move will trigger game_over signal
    await game.click("/root/Main/Board/Cell2")  # X wins

    # Verify game ended
    winner = await game.call("/root/Main", "get_winner")
    assert winner == "X"


@pytest.mark.asyncio
async def test_make_move_api(game):
    """make_move API should work correctly."""
    result = await game.call("/root/Main", "make_move", [4])
    assert result is True

    cell_text = await game.call("/root/Main", "get_cell_text", [4])
    assert cell_text == "X"


@pytest.mark.asyncio
async def test_make_move_fails_on_occupied(game):
    """make_move should return false for occupied cell."""
    await game.call("/root/Main", "make_move", [4])
    result = await game.call("/root/Main", "make_move", [4])
    assert result is False


@pytest.mark.asyncio
async def test_status_label_shows_turn(game):
    """Status label should show current player's turn."""
    status = await game.get_property("/root/Main/StatusLabel", "text")
    assert "X" in status and "turn" in status


@pytest.mark.asyncio
async def test_status_label_shows_winner(game):
    """Status label should show winner when game ends."""
    # X wins
    await game.click("/root/Main/Board/Cell0")
    await game.click("/root/Main/Board/Cell3")
    await game.click("/root/Main/Board/Cell1")
    await game.click("/root/Main/Board/Cell4")
    await game.click("/root/Main/Board/Cell2")

    status = await game.get_property("/root/Main/StatusLabel", "text")
    assert "X" in status and "wins" in status
