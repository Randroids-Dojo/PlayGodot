"""Screenshot utilities."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playgodot.client import Client


class ScreenshotManager:
    """Handles screenshot capture and comparison."""

    def __init__(self, client: Client):
        self._client = client

    async def capture(self, path: str | Path | None = None, node: str | None = None) -> bytes:
        """Capture a screenshot.

        Args:
            path: Optional file path to save the screenshot.
            node: Optional node path to screenshot (just that node).

        Returns:
            The screenshot as PNG bytes.
        """
        params = {}
        if node:
            params["node"] = node

        result = await self._client.send("screenshot", params)
        image_data = base64.b64decode(result["data"])

        if path:
            Path(path).write_bytes(image_data)

        return image_data

    async def compare(
        self,
        expected_path: str | Path,
        actual_path: str | Path | None = None,
        threshold: float = 0.01,
    ) -> float:
        """Compare screenshots and return similarity score.

        Args:
            expected_path: Path to the expected/reference screenshot.
            actual_path: Path to the actual screenshot, or None to capture now.
            threshold: Acceptable difference threshold (0-1).

        Returns:
            Similarity score from 0 (completely different) to 1 (identical).
        """
        try:
            from PIL import Image
            import io
        except ImportError:
            raise ImportError(
                "Pillow is required for screenshot comparison. "
                "Install with: pip install playgodot[image]"
            )

        expected = Image.open(expected_path)

        if actual_path:
            actual = Image.open(actual_path)
        else:
            actual_bytes = await self.capture()
            actual = Image.open(io.BytesIO(actual_bytes))

        if expected.size != actual.size:
            return 0.0

        # Convert to same mode
        expected = expected.convert("RGB")
        actual = actual.convert("RGB")

        # Calculate pixel differences
        diff_pixels = 0
        total_pixels = expected.width * expected.height

        expected_data = expected.load()
        actual_data = actual.load()

        for y in range(expected.height):
            for x in range(expected.width):
                r1, g1, b1 = expected_data[x, y]
                r2, g2, b2 = actual_data[x, y]
                if abs(r1 - r2) > 5 or abs(g1 - g2) > 5 or abs(b1 - b2) > 5:
                    diff_pixels += 1

        similarity = 1.0 - (diff_pixels / total_pixels)
        return similarity

    async def assert_matches(
        self,
        reference_path: str | Path,
        threshold: float = 0.99,
        update: bool = False,
    ) -> None:
        """Assert that current screenshot matches reference.

        Args:
            reference_path: Path to the reference screenshot.
            threshold: Minimum similarity required (0-1).
            update: If True, update the reference if it doesn't exist.

        Raises:
            AssertionError: If screenshots don't match within threshold.
            FileNotFoundError: If reference doesn't exist and update is False.
        """
        reference_path = Path(reference_path)

        if not reference_path.exists():
            if update:
                reference_path.parent.mkdir(parents=True, exist_ok=True)
                await self.capture(reference_path)
                return
            else:
                raise FileNotFoundError(
                    f"Reference screenshot not found: {reference_path}"
                )

        similarity = await self.compare(reference_path)
        if similarity < threshold:
            raise AssertionError(
                f"Screenshot doesn't match reference. "
                f"Similarity: {similarity:.2%}, Required: {threshold:.2%}"
            )
