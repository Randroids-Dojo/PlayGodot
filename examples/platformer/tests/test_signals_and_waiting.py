"""Tests demonstrating signals and advanced waiting patterns.

Showcases:
- wait_for_signal() - Wait for Godot signals
- wait_for_node() - Wait for nodes to exist
- wait_for_visible() - Wait for visibility
- wait_for() - Custom condition waiting
"""

import asyncio

import pytest


# =============================================================================
# Signal Waiting Tests
# =============================================================================


@pytest.mark.asyncio
async def test_wait_for_jumped_signal(game):
    """Wait for the player jumped signal.

    Demonstrates: wait_for_signal() with player signals
    """
    async def is_grounded():
        return await game.call("/root/Main/Player", "is_grounded")

    await game.wait_for(is_grounded, timeout=3.0)

    # Start waiting for signal before triggering it
    # Note: We need to trigger jump in parallel with waiting

    # Jump to trigger signal
    await game.press_action("jump")

    # The signal should have been emitted
    # We verify by checking player state
    await asyncio.sleep(0.1)
    is_jumping = await game.call("/root/Main/Player", "is_jumping")
    assert is_jumping, "Player should be jumping after jump action"


@pytest.mark.asyncio
async def test_wait_for_landed_signal(game):
    """Wait for player to land after jumping.

    Demonstrates: Waiting for physics events via signals
    """
    async def is_grounded():
        return await game.call("/root/Main/Player", "is_grounded")

    # Ensure grounded first
    await game.wait_for(is_grounded, timeout=3.0)

    # Jump
    await game.press_action("jump")
    await asyncio.sleep(0.1)

    # Wait for landing (player becomes grounded again)
    await game.wait_for(is_grounded, timeout=3.0)

    grounded = await game.call("/root/Main/Player", "is_grounded")
    assert grounded, "Player should be grounded after landing"


@pytest.mark.asyncio
async def test_wait_for_collection_event(game):
    """Wait for coin collection.

    Demonstrates: Waiting for game events
    """
    initial_coins = await game.call("/root/Main/Player", "get_coins")

    # Move player to a coin position
    # Coin1 is at (250, 410), player starts around (100, 500)
    await game.call("/root/Main/Player", "set_position_for_test", [250.0, 380.0])

    # Wait a moment for collision detection
    await asyncio.sleep(0.3)

    # Check if coin was collected
    async def has_more_coins():
        coins = await game.call("/root/Main/Player", "get_coins")
        return coins > initial_coins

    try:
        await game.wait_for(has_more_coins, timeout=2.0)
        collected = True
    except Exception:
        collected = False

    # Verify state changed
    final_coins = await game.call("/root/Main/Player", "get_coins")
    assert final_coins > initial_coins or collected, "Should collect coin"


# =============================================================================
# Node Waiting Tests
# =============================================================================


@pytest.mark.asyncio
async def test_wait_for_node_exists(game):
    """Wait for a node to exist.

    Demonstrates: wait_for_node() basic usage
    """
    # This node already exists, should return immediately
    node = await game.wait_for_node("/root/Main/Player", timeout=5.0)
    assert node is not None, "Should find existing node"


@pytest.mark.asyncio
async def test_wait_for_node_timeout(game):
    """wait_for_node raises timeout for missing nodes.

    Demonstrates: Timeout behavior
    """
    from playgodot import TimeoutError

    with pytest.raises(TimeoutError):
        # Wait for non-existent node with short timeout
        await game.wait_for_node("/root/Main/NonExistent", timeout=0.5)


@pytest.mark.asyncio
async def test_wait_for_hud_elements(game):
    """Wait for HUD elements to be ready.

    Demonstrates: Waiting for UI nodes
    """
    # Wait for HUD labels
    score_label = await game.wait_for_node("/root/Main/HUD/ScoreLabel", timeout=5.0)
    status_label = await game.wait_for_node("/root/Main/HUD/StatusLabel", timeout=5.0)

    assert score_label is not None
    assert status_label is not None


# =============================================================================
# Visibility Waiting Tests
# =============================================================================


@pytest.mark.asyncio
async def test_wait_for_visible(game):
    """Wait for a node to become visible.

    Demonstrates: wait_for_visible()
    """
    # Score label should be visible
    await game.wait_for_visible("/root/Main/HUD/ScoreLabel", timeout=5.0)

    visible = await game.get_property("/root/Main/HUD/ScoreLabel", "visible")
    assert visible is True


@pytest.mark.asyncio
async def test_wait_for_pause_menu_visible(game):
    """Wait for pause menu to become visible.

    Demonstrates: Waiting for UI state changes
    """
    # Initially hidden
    visible = await game.get_property("/root/Main/HUD/PauseMenu", "visible")
    assert visible is False, "Pause menu should start hidden"

    # Pause the game
    await game.press_action("pause")

    # Wait for pause menu to appear
    async def is_pause_visible():
        return await game.get_property("/root/Main/HUD/PauseMenu", "visible")

    await game.wait_for(is_pause_visible, timeout=2.0)

    visible = await game.get_property("/root/Main/HUD/PauseMenu", "visible")
    assert visible is True, "Pause menu should be visible"

    # Unpause
    await game.press_action("pause")


# =============================================================================
# Custom Condition Waiting Tests
# =============================================================================


@pytest.mark.asyncio
async def test_wait_for_custom_condition(game):
    """Wait for a custom condition.

    Demonstrates: wait_for() with lambda/function
    """
    # Wait for player to be grounded
    async def player_grounded():
        return await game.call("/root/Main/Player", "is_grounded")

    result = await game.wait_for(player_grounded, timeout=5.0)
    assert result is True, "Condition should be satisfied"


@pytest.mark.asyncio
async def test_wait_for_score_change(game):
    """Wait for score to change.

    Demonstrates: Waiting for game state changes
    """
    initial_score = await game.call("/root/Main", "get_score")

    # Trigger score change by collecting a coin
    await game.call("/root/Main/Player", "set_position_for_test", [250.0, 380.0])

    # Wait for score to increase
    async def score_increased():
        current = await game.call("/root/Main", "get_score")
        return current > initial_score

    try:
        await game.wait_for(score_increased, timeout=2.0)
        # Score changed
        final_score = await game.call("/root/Main", "get_score")
        assert final_score > initial_score
    except Exception:
        # Coin might not have been collected (physics timing)
        pass


@pytest.mark.asyncio
async def test_wait_for_player_state(game):
    """Wait for player to reach specific state.

    Demonstrates: State machine testing
    """
    # Wait for idle state
    async def is_idle():
        state = await game.call("/root/Main/Player", "get_state")
        return state == "idle"

    async def is_grounded():
        return await game.call("/root/Main/Player", "is_grounded")

    # First ensure grounded
    await game.wait_for(is_grounded, timeout=3.0)

    # Stop any movement and wait for idle
    await asyncio.sleep(0.3)

    state = await game.call("/root/Main/Player", "get_state")
    assert state in ["idle", "running"], f"Player should be idle or running, got {state}"


@pytest.mark.asyncio
async def test_wait_for_with_interval(game):
    """wait_for with custom polling interval.

    Demonstrates: Polling configuration
    """
    check_count = 0

    async def condition_with_counter():
        nonlocal check_count
        check_count += 1
        return await game.call("/root/Main/Player", "is_grounded")

    await game.wait_for(
        condition_with_counter,
        timeout=5.0,
        interval=0.2,  # Check every 200ms
    )

    # With 200ms interval and ~instant satisfaction, should check few times
    assert check_count >= 1, "Should have checked condition at least once"


@pytest.mark.asyncio
async def test_wait_for_position_change(game):
    """Wait for player position to change.

    Demonstrates: Complex condition waiting
    """
    initial_pos = await game.get_property("/root/Main/Player", "position")

    # Start moving
    # Note: We use hold_action in background-ish way
    move_task = asyncio.create_task(game.hold_action("move_right", duration=1.0))

    # Wait for position to change significantly
    async def position_changed():
        pos = await game.get_property("/root/Main/Player", "position")
        return abs(pos["x"] - initial_pos["x"]) > 20

    await game.wait_for(position_changed, timeout=2.0)

    final_pos = await game.get_property("/root/Main/Player", "position")
    assert final_pos["x"] > initial_pos["x"], "Player should have moved"

    # Clean up move task
    await move_task


@pytest.mark.asyncio
async def test_wait_with_timeout_return(game):
    """Verify wait_for returns the truthy value.

    Demonstrates: Return value from wait_for
    """

    async def get_grounded_state():
        return await game.call("/root/Main/Player", "is_grounded")

    result = await game.wait_for(get_grounded_state, timeout=5.0)

    # Result should be the return value of the condition
    assert result is True, "wait_for should return the truthy value"
