"""Tests demonstrating visual testing and screenshots.

Showcases:
- screenshot() - Take screenshots
- compare_screenshot() - Compare images
- assert_screenshot() - Visual regression testing
"""

import asyncio
from pathlib import Path

import pytest


SCREENSHOTS_DIR = Path(__file__).parent.parent / "screenshots"


@pytest.mark.asyncio
async def test_take_screenshot(game):
    """Take a screenshot of the game.

    Demonstrates: screenshot() basic usage
    """
    # Take a screenshot and get raw bytes
    png_data = await game.screenshot()

    assert png_data is not None, "Should return screenshot data"
    assert len(png_data) > 0, "Screenshot should have content"
    # PNG files start with specific bytes
    assert png_data[:4] == b"\x89PNG", "Should be valid PNG data"


@pytest.mark.asyncio
async def test_save_screenshot(game, tmp_path):
    """Save a screenshot to a file.

    Demonstrates: screenshot() with path parameter
    """
    screenshot_path = tmp_path / "test_screenshot.png"

    # Take and save screenshot
    png_data = await game.screenshot(path=str(screenshot_path))

    assert screenshot_path.exists(), "Screenshot file should be created"
    assert screenshot_path.stat().st_size > 0, "Screenshot should have content"

    # Verify file matches returned data
    with open(screenshot_path, "rb") as f:
        file_data = f.read()
    assert file_data == png_data, "File should match returned bytes"


@pytest.mark.asyncio
async def test_screenshot_after_movement(game):
    """Take screenshot after player movement.

    Demonstrates: Screenshot timing with game state
    """
    # Move player
    await game.hold_action("move_right", duration=0.3)
    await asyncio.sleep(0.1)

    # Screenshot should capture new position
    png_data = await game.screenshot()
    assert png_data is not None
    assert len(png_data) > 1000, "Screenshot should have significant content"


@pytest.mark.asyncio
async def test_compare_screenshots_identical(game, tmp_path):
    """Compare two identical screenshots.

    Demonstrates: compare_screenshot() with high similarity
    """
    # Take two screenshots without moving
    screenshot1 = await game.screenshot()
    await asyncio.sleep(0.05)
    screenshot2 = await game.screenshot()

    # Compare them - should be very similar
    similarity = await game.compare_screenshot(screenshot1, screenshot2)

    assert similarity > 0.95, f"Identical screenshots should be >95% similar, got {similarity}"


@pytest.mark.asyncio
async def test_compare_screenshots_different(game, tmp_path):
    """Compare screenshots before and after movement.

    Demonstrates: compare_screenshot() detecting differences
    """
    # Screenshot before movement
    before = await game.screenshot()

    # Move player significantly
    await game.hold_action("move_right", duration=0.5)
    await asyncio.sleep(0.1)

    # Screenshot after movement
    after = await game.screenshot()

    # Compare - should be different (player moved)
    similarity = await game.compare_screenshot(before, after)

    # They should be somewhat similar (same level) but not identical
    assert similarity < 0.99, "Screenshots after movement should differ"
    assert similarity > 0.5, "Screenshots should still be mostly similar (same level)"


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires reference screenshot - run once to generate")
async def test_assert_screenshot_matches_reference(game):
    """Assert screenshot matches a reference image.

    Demonstrates: assert_screenshot() for visual regression

    To use this test:
    1. Run test_generate_reference_screenshot first to create reference
    2. Remove the skip marker
    3. Run this test to verify against reference
    """
    # Wait for stable state
    await asyncio.sleep(0.2)

    reference_path = SCREENSHOTS_DIR / "level1_start.png"

    # This will raise AssertionError if similarity < threshold
    await game.assert_screenshot(
        str(reference_path),
        threshold=0.95,  # 95% similarity required
    )


@pytest.mark.asyncio
async def test_generate_reference_screenshot(game, tmp_path):
    """Generate a reference screenshot for visual regression.

    Demonstrates: Creating baseline images

    This test saves a reference screenshot that can be used
    for visual regression testing.
    """
    # Wait for game to stabilize
    await asyncio.sleep(0.3)

    # Ensure screenshots directory exists
    SCREENSHOTS_DIR.mkdir(exist_ok=True)

    reference_path = SCREENSHOTS_DIR / "level1_start.png"

    # Save reference screenshot
    await game.screenshot(path=str(reference_path))

    # Verify it was saved
    if reference_path.exists():
        print(f"Reference screenshot saved to: {reference_path}")
        assert reference_path.stat().st_size > 0


@pytest.mark.asyncio
async def test_screenshot_shows_ui(game):
    """Verify UI elements are captured in screenshots.

    Demonstrates: Screenshot content verification
    """
    # The screenshot should include the HUD
    # We can't easily verify content without image analysis,
    # but we can verify the screenshot has reasonable size

    png_data = await game.screenshot()

    # A screenshot with UI should have decent file size
    # (compressed PNG of 800x600 with graphics)
    assert len(png_data) > 5000, "Screenshot should include visible content"


@pytest.mark.asyncio
async def test_screenshot_paused_game(game):
    """Take screenshot while game is paused.

    Demonstrates: Screenshots work during pause
    """
    # Pause the game
    await game.pause()
    await asyncio.sleep(0.1)

    # Should still be able to take screenshots
    png_data = await game.screenshot()
    assert png_data is not None
    assert len(png_data) > 0

    # Pause menu should be visible in screenshot
    # (We can't verify content, but screenshot should work)

    await game.unpause()


@pytest.mark.asyncio
async def test_multiple_screenshots_sequence(game, tmp_path):
    """Take a sequence of screenshots during gameplay.

    Demonstrates: Screenshot sequences for debugging
    """
    screenshots = []

    # Take screenshots during a jump sequence
    async def is_grounded():
        return await game.call("/root/Main/Player", "is_grounded")

    await game.wait_for(is_grounded, timeout=3.0)

    # Before jump
    screenshots.append(await game.screenshot())

    # Jump
    await game.press_action("jump")

    # During jump (multiple frames)
    for i in range(3):
        await asyncio.sleep(0.1)
        screenshots.append(await game.screenshot())

    # All screenshots should be valid
    for i, ss in enumerate(screenshots):
        assert ss is not None, f"Screenshot {i} should not be None"
        assert len(ss) > 0, f"Screenshot {i} should have content"

    # Screenshots should be different (player at different heights)
    similarity = await game.compare_screenshot(screenshots[0], screenshots[2])
    assert similarity < 0.99, "Screenshots during jump should differ"
