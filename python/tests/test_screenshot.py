"""Tests for screenshot comparison features."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import io

# Skip all tests in this module if PIL is not available
pytest.importorskip("PIL", reason="Pillow is required for screenshot tests")


# Create a simple test image
def create_test_png(width: int = 10, height: int = 10, color: tuple = (255, 0, 0, 255)) -> bytes:
    """Create a simple test PNG image."""
    from PIL import Image
    img = Image.new("RGBA", (width, height), color)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


class TestCompareScreenshot:
    """Tests for compare_screenshot method."""

    @pytest.mark.asyncio
    async def test_compare_identical_images(self, mock_godot, mock_client) -> None:
        """Identical images should return 1.0 similarity."""
        png_data = create_test_png(10, 10, (255, 0, 0, 255))
        mock_client.send.return_value = {"data": png_data}

        # Compare image with itself (via bytes)
        similarity = await mock_godot.compare_screenshot(png_data, png_data)
        assert similarity == 1.0

    @pytest.mark.asyncio
    async def test_compare_different_images(self, mock_godot, mock_client) -> None:
        """Different images should return lower similarity."""
        red_png = create_test_png(10, 10, (255, 0, 0, 255))
        blue_png = create_test_png(10, 10, (0, 0, 255, 255))
        mock_client.send.return_value = {"data": blue_png}

        similarity = await mock_godot.compare_screenshot(red_png, blue_png)
        assert 0.0 < similarity < 1.0

    @pytest.mark.asyncio
    async def test_compare_takes_screenshot_if_actual_none(self, mock_godot, mock_client) -> None:
        """Should take a new screenshot if actual is None."""
        png_data = create_test_png()
        mock_client.send.return_value = {"data": png_data}

        await mock_godot.compare_screenshot(png_data)
        mock_client.send.assert_called()

    @pytest.mark.asyncio
    async def test_compare_different_dimensions_raises(self, mock_godot, mock_client) -> None:
        """Different image sizes should raise ValueError."""
        small_png = create_test_png(10, 10)
        large_png = create_test_png(20, 20)
        mock_client.send.return_value = {"data": large_png}

        with pytest.raises(ValueError) as exc:
            await mock_godot.compare_screenshot(small_png, large_png)
        assert "dimensions don't match" in str(exc.value)

    @pytest.mark.asyncio
    async def test_compare_file_not_found(self, mock_godot, mock_client) -> None:
        """Non-existent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            await mock_godot.compare_screenshot("/nonexistent/image.png")

    @pytest.mark.asyncio
    async def test_compare_from_file(self, mock_godot, mock_client, tmp_path) -> None:
        """Should load expected image from file path."""
        png_data = create_test_png()
        expected_file = tmp_path / "expected.png"
        expected_file.write_bytes(png_data)
        mock_client.send.return_value = {"data": png_data}

        similarity = await mock_godot.compare_screenshot(str(expected_file), png_data)
        assert similarity == 1.0


class TestAssertScreenshot:
    """Tests for assert_screenshot method."""

    @pytest.mark.asyncio
    async def test_assert_passes_when_similar(self, mock_godot, mock_client, tmp_path) -> None:
        """Should pass when similarity is above threshold."""
        png_data = create_test_png()
        reference_file = tmp_path / "reference.png"
        reference_file.write_bytes(png_data)
        mock_client.send.return_value = {"data": png_data}

        # Should not raise
        await mock_godot.assert_screenshot(str(reference_file))

    @pytest.mark.asyncio
    async def test_assert_fails_below_threshold(self, mock_godot, mock_client, tmp_path) -> None:
        """Should raise AssertionError when similarity is below threshold."""
        red_png = create_test_png(10, 10, (255, 0, 0, 255))
        blue_png = create_test_png(10, 10, (0, 0, 255, 255))
        reference_file = tmp_path / "reference.png"
        reference_file.write_bytes(red_png)
        mock_client.send.return_value = {"data": blue_png}

        with pytest.raises(AssertionError) as exc:
            await mock_godot.assert_screenshot(str(reference_file), threshold=0.99)
        assert "below threshold" in str(exc.value)

    @pytest.mark.asyncio
    async def test_assert_saves_actual_on_failure(self, mock_godot, mock_client, tmp_path) -> None:
        """Should save actual screenshot when assertion fails."""
        red_png = create_test_png(10, 10, (255, 0, 0, 255))
        blue_png = create_test_png(10, 10, (0, 0, 255, 255))
        reference_file = tmp_path / "reference.png"
        reference_file.write_bytes(red_png)
        mock_client.send.return_value = {"data": blue_png}

        with pytest.raises(AssertionError):
            await mock_godot.assert_screenshot(str(reference_file), threshold=0.99)

        actual_file = tmp_path / "reference.actual.png"
        assert actual_file.exists()
        assert actual_file.read_bytes() == blue_png

    @pytest.mark.asyncio
    async def test_assert_custom_threshold(self, mock_godot, mock_client, tmp_path) -> None:
        """Should respect custom threshold."""
        # Create slightly different images
        png1 = create_test_png(10, 10, (255, 0, 0, 255))
        png2 = create_test_png(10, 10, (250, 5, 5, 255))  # Very similar
        reference_file = tmp_path / "reference.png"
        reference_file.write_bytes(png1)
        mock_client.send.return_value = {"data": png2}

        # Should pass with low threshold
        await mock_godot.assert_screenshot(str(reference_file), threshold=0.9)


class TestCalculateImageSimilarity:
    """Tests for _calculate_image_similarity method."""

    def test_identical_images_return_1(self, mock_godot) -> None:
        """Identical images should return 1.0."""
        from PIL import Image
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        similarity = mock_godot._calculate_image_similarity(img, img)
        assert similarity == 1.0

    def test_completely_different_images(self, mock_godot) -> None:
        """Completely different images should return low similarity."""
        from PIL import Image
        white = Image.new("RGBA", (10, 10), (255, 255, 255, 255))
        black = Image.new("RGBA", (10, 10), (0, 0, 0, 255))
        similarity = mock_godot._calculate_image_similarity(white, black)
        assert similarity < 0.5

    def test_similarity_between_0_and_1(self, mock_godot) -> None:
        """Similarity should always be between 0 and 1."""
        from PIL import Image
        img1 = Image.new("RGBA", (10, 10), (100, 100, 100, 255))
        img2 = Image.new("RGBA", (10, 10), (150, 150, 150, 255))
        similarity = mock_godot._calculate_image_similarity(img1, img2)
        assert 0.0 <= similarity <= 1.0


class TestSaveDiffImage:
    """Tests for _save_diff_image method."""

    @pytest.mark.asyncio
    async def test_saves_diff_image(self, mock_godot, tmp_path) -> None:
        """Should save a diff image highlighting differences."""
        red_png = create_test_png(10, 10, (255, 0, 0, 255))
        blue_png = create_test_png(10, 10, (0, 0, 255, 255))

        reference_file = tmp_path / "reference.png"
        reference_file.write_bytes(red_png)
        diff_file = tmp_path / "diff.png"

        await mock_godot._save_diff_image(str(reference_file), blue_png, str(diff_file))

        assert diff_file.exists()
        # Verify it's a valid PNG
        from PIL import Image
        img = Image.open(diff_file)
        assert img.size == (10, 10)
