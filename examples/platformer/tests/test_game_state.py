"""Tests demonstrating game state management and scene control.

Showcases:
- get_property() / set_property() - Property access
- call() - Method invocation
- get_current_scene() - Scene info
- reload_scene() - Scene reloading
- query_nodes() / count_nodes() - Node querying
- get_tree() - Scene tree inspection
- pause() / unpause() - Game pausing
- set_time_scale() - Time manipulation
"""

import asyncio

import pytest


# =============================================================================
# Property Access Tests
# =============================================================================


@pytest.mark.asyncio
async def test_read_player_position(game):
    """Read player position property.

    Demonstrates: get_property() with Vector2 values
    """
    position = await game.get_property("/root/Main/Player", "position")

    assert "x" in position, "Position should have x component"
    assert "y" in position, "Position should have y component"
    assert isinstance(position["x"], (int, float))
    assert isinstance(position["y"], (int, float))


@pytest.mark.asyncio
async def test_read_label_text(game):
    """Read UI label text.

    Demonstrates: get_property() with string values
    """
    score_text = await game.get_property("/root/Main/HUD/ScoreLabel", "text")
    assert "Score" in score_text, f"Score label should contain 'Score', got: {score_text}"


@pytest.mark.asyncio
async def test_set_property(game):
    """Set a property value on a node.

    Demonstrates: set_property()
    """
    # Set player position using the test API method
    await game.call("/root/Main/Player", "set_position_for_test", [200.0, 400.0])

    position = await game.get_property("/root/Main/Player", "position")
    assert abs(position["x"] - 200.0) < 1, "X position should be set"
    assert abs(position["y"] - 400.0) < 1, "Y position should be set"


@pytest.mark.asyncio
async def test_read_visibility(game):
    """Read node visibility.

    Demonstrates: get_property() with boolean values
    """
    # Pause menu should be hidden initially
    visible = await game.get_property("/root/Main/HUD/PauseMenu", "visible")
    assert visible is False, "Pause menu should be hidden initially"


# =============================================================================
# Node Querying Tests
# =============================================================================


@pytest.mark.asyncio
async def test_query_coins(game):
    """Query all coin nodes in the scene.

    Demonstrates: query_nodes() with patterns
    """
    # Query for coin nodes
    coins = await game.query_nodes("/root/Main/Coins/*")
    assert len(coins) >= 1, "Should find coin nodes"


@pytest.mark.asyncio
async def test_count_coins(game):
    """Count collectible coins.

    Demonstrates: count_nodes()
    """
    count = await game.count_nodes("/root/Main/Coins/*")
    assert count == 5, f"Should have 5 coins initially, got {count}"


@pytest.mark.asyncio
async def test_query_platforms(game):
    """Query platform nodes.

    Demonstrates: query_nodes() for level geometry
    """
    platforms = await game.query_nodes("/root/Main/Platforms/*")
    assert len(platforms) >= 3, "Should have multiple platforms"


@pytest.mark.asyncio
async def test_get_tree_structure(game):
    """Get the scene tree structure.

    Demonstrates: get_tree()
    """
    tree = await game.get_tree()
    assert tree is not None, "Should return tree structure"
    # Tree should contain our main nodes
    assert "Main" in str(tree) or "root" in str(tree).lower()


# =============================================================================
# Game State Tests
# =============================================================================


@pytest.mark.asyncio
async def test_initial_score(game):
    """Game starts with zero score.

    Demonstrates: call() for game state
    """
    score = await game.call("/root/Main", "get_score")
    assert score == 0, "Should start with 0 score"


@pytest.mark.asyncio
async def test_initial_coin_count(game):
    """Verify initial coin count.

    Demonstrates: Multiple call() invocations
    """
    total = await game.call("/root/Main", "get_total_coins")
    remaining = await game.call("/root/Main", "get_remaining_coins")

    assert total == 5, f"Should have 5 total coins, got {total}"
    assert remaining == total, "All coins should remain at start"


@pytest.mark.asyncio
async def test_player_state_api(game):
    """Player state API returns valid states.

    Demonstrates: String return values from call()
    """
    state = await game.call("/root/Main", "get_player_state")
    valid_states = ["idle", "running", "jumping", "falling", "dead"]
    assert state in valid_states, f"Invalid state: {state}"


@pytest.mark.asyncio
async def test_level_name(game):
    """Get current level name.

    Demonstrates: call() for metadata
    """
    name = await game.call("/root/Main", "get_level_name")
    assert name == "Level 1", f"Expected 'Level 1', got '{name}'"


# =============================================================================
# Scene Management Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_current_scene(game):
    """Get information about current scene.

    Demonstrates: get_current_scene()
    """
    scene = await game.get_current_scene()
    assert "path" in scene or "name" in scene, "Should return scene info"


@pytest.mark.asyncio
async def test_reload_scene(game):
    """Reload the current scene.

    Demonstrates: reload_scene()
    """
    # Collect a coin first
    await game.call("/root/Main/Player", "set_position_for_test", [250.0, 380.0])
    await asyncio.sleep(0.3)

    initial_remaining = await game.call("/root/Main", "get_remaining_coins")

    # Reload scene
    await game.reload_scene()
    await asyncio.sleep(0.5)

    # Wait for scene to be ready again
    await game.wait_for_node("/root/Main/Player")

    # Coins should be restored
    remaining = await game.call("/root/Main", "get_remaining_coins")
    assert remaining == 5, "Reload should restore all coins"


# =============================================================================
# Pause and Time Scale Tests
# =============================================================================


@pytest.mark.asyncio
async def test_pause_game(game):
    """Pause the game programmatically.

    Demonstrates: pause(), is_paused()
    """
    # Verify not paused initially
    paused = await game.is_paused()
    assert paused is False, "Should not be paused initially"

    # Pause the game
    await game.pause()

    paused = await game.is_paused()
    assert paused is True, "Game should be paused"

    # Unpause
    await game.unpause()

    paused = await game.is_paused()
    assert paused is False, "Game should be unpaused"


@pytest.mark.asyncio
async def test_pause_with_action(game):
    """Pause using the pause input action.

    Demonstrates: press_action() for pause
    """
    await game.press_action("pause")
    await asyncio.sleep(0.1)

    is_paused = await game.call("/root/Main", "is_paused")
    assert is_paused is True, "Pause action should pause game"

    # Unpause
    await game.press_action("pause")


@pytest.mark.asyncio
async def test_time_scale(game):
    """Manipulate game time scale.

    Demonstrates: set_time_scale(), get_time_scale()
    """
    # Get initial time scale
    initial_scale = await game.get_time_scale()
    assert initial_scale == 1.0, "Should start at normal speed"

    # Set to half speed
    await game.set_time_scale(0.5)
    scale = await game.get_time_scale()
    assert scale == 0.5, "Should be at half speed"

    # Set to double speed
    await game.set_time_scale(2.0)
    scale = await game.get_time_scale()
    assert scale == 2.0, "Should be at double speed"

    # Restore normal speed
    await game.set_time_scale(1.0)


@pytest.mark.asyncio
async def test_time_scale_affects_physics(game):
    """Time scale actually affects game physics.

    Demonstrates: Practical use of time scale
    """
    async def is_grounded():
        return await game.call("/root/Main/Player", "is_grounded")

    await game.wait_for(is_grounded, timeout=3.0)

    # Jump at double speed
    await game.set_time_scale(2.0)

    initial_y = await game.call("/root/Main/Player", "get_position_y")
    await game.press_action("jump")

    # With 2x speed, physics should be faster
    await asyncio.sleep(0.1)  # Half the normal time

    mid_y = await game.call("/root/Main/Player", "get_position_y")
    assert mid_y < initial_y, "Player should jump even with short wait at 2x speed"

    # Restore
    await game.set_time_scale(1.0)


# =============================================================================
# Group Querying Tests
# =============================================================================


@pytest.mark.asyncio
async def test_query_nodes_in_group(game):
    """Query nodes by group membership.

    Demonstrates: call() to get group members
    """
    coin_paths = await game.call("/root/Main", "get_nodes_in_group", ["coins"])
    assert len(coin_paths) == 5, f"Should have 5 coins in group, got {len(coin_paths)}"


@pytest.mark.asyncio
async def test_collectibles_group(game):
    """Query collectibles group.

    Demonstrates: Multiple groups on nodes
    """
    collectibles = await game.call("/root/Main", "get_nodes_in_group", ["collectibles"])
    assert len(collectibles) >= 5, "Coins should be in collectibles group"
