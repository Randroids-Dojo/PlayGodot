"""Pytest configuration for tic-tac-toe tests."""

import sys
from pathlib import Path

import pytest
import pytest_asyncio

# Add the Python client to the path
python_client = Path(__file__).parent.parent.parent.parent / "python"
sys.path.insert(0, str(python_client))

from playgodot import Godot


GODOT_PROJECT = Path(__file__).parent.parent / "godot"


@pytest_asyncio.fixture
async def game():
    """Fixture that launches the tic-tac-toe game and provides a connected client."""
    async with Godot.launch(str(GODOT_PROJECT), headless=True, timeout=30.0) as g:
        # Wait for the main scene to be ready
        await g.wait_for_node("/root/Main")
        yield g
