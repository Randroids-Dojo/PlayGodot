"""Pytest fixtures for platformer tests.

Demonstrates proper test setup patterns for PlayGodot.
"""

import asyncio
from pathlib import Path

import pytest
import pytest_asyncio

from playgodot import Godot


# Get the path to the Godot project
GODOT_PROJECT = Path(__file__).parent.parent / "godot"


@pytest_asyncio.fixture
async def game():
    """Launch the platformer game and provide a Godot instance.

    This fixture:
    - Launches Godot in headless mode
    - Waits for the main scene to be ready
    - Yields the game instance for testing
    - Cleans up after the test
    """
    async with Godot.launch(
        GODOT_PROJECT,
        headless=True,
        resolution=(800, 600),
        timeout=30.0,
    ) as g:
        # Wait for the main scene and player to be ready
        await g.wait_for_node("/root/Main")
        await g.wait_for_node("/root/Main/Player")

        # Small delay to ensure physics is initialized
        await asyncio.sleep(0.1)

        yield g


@pytest_asyncio.fixture
async def game_with_player_grounded(game):
    """Fixture that ensures player starts on the ground.

    Waits for the player to land before yielding.
    """
    # Wait until player is grounded
    async def is_grounded():
        return await game.call("/root/Main/Player", "is_grounded")

    await game.wait_for(is_grounded, timeout=5.0)
    return game


@pytest_asyncio.fixture
async def fresh_game():
    """Launch a fresh game instance for each test.

    Use this when you need complete isolation between tests.
    """
    async with Godot.launch(
        GODOT_PROJECT,
        headless=True,
        resolution=(800, 600),
    ) as g:
        await g.wait_for_node("/root/Main")
        await g.wait_for_node("/root/Main/Player")
        await asyncio.sleep(0.1)
        yield g
