"""
Feature extractor service for moodboard clustering.

The main implemented feature mode is ``dominant_colors``. It turns an OpenCV
image into a compact numeric vector based on the image's most common colors.
That vector can then be used by clustering code to group visually similar
images together.
"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np
from sklearn.cluster import KMeans

from models.schemas import Color
from utils.errors import ImageProcessingError, ValidationError


class FeatureExtractor:
    """
    Extract numeric features from OpenCV images.

    Args:
        feature_mode: Which feature extraction strategy to use. Currently the
            supported mode is ``"dominant_colors"``.
        num_colors: Number of dominant colors to find with KMeans.
        resize_dimension: Maximum width or height used before clustering.
            Smaller images make KMeans much faster.
        random_state: Seed used by KMeans so results are deterministic enough
            for tests and demos.
    """

    def __init__(
        self,
        feature_mode: str = "dominant_colors",
        num_colors: int = 3,
        resize_dimension: int = 150,
        random_state: int = 42,
    ):
        """Store configuration for feature extraction."""
        if feature_mode != "dominant_colors":
            raise ValidationError(
                f"Unsupported feature mode: {feature_mode}",
                error_code="UNSUPPORTED_FEATURE_MODE",
            )

        self.feature_mode = feature_mode
        self.num_colors = num_colors
        self.resize_dimension = resize_dimension
        self.random_state = random_state

    def extract_features(self, image: np.ndarray, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Extract dominant-color features from one OpenCV image.

        Args:
            image: OpenCV image array in BGR format.

        Returns:
            Dictionary containing:
            - feature_vector: Flat list of RGB channel values, normalized to 0-1.
              For 3 colors, this has 9 numbers: [r, g, b, r, g, b, r, g, b].
            - dominant_hex_colors: Dominant colors as hex strings.
            - dominant_rgb_colors: Dominant colors as RGB integer lists.

        Raises:
            ImageProcessingError: If the image is invalid or extraction fails.
        """
        try:
            self._validate_image(image)

            # Let callers pick how many colors they want.
            requested_colors = kwargs.get("num_colors")
            if requested_colors is None and args:
                # Older code put the color count in the second spot.
                requested_colors = args[1] if len(args) > 1 else None

            num_colors = int(requested_colors or self.num_colors)

            small_image = self._resize_for_speed(image)

            # Put the colors in normal RGB order.
            rgb_image = cv2.cvtColor(small_image, cv2.COLOR_BGR2RGB)

            # Make one row for each pixel.
            pixels = rgb_image.reshape(-1, 3).astype(np.float32)
            dominant_rgb_colors = self._find_dominant_colors(pixels, num_colors)

            # Squish the color numbers down to 0-1.
            feature_vector = (dominant_rgb_colors.flatten() / 255.0).tolist()
            dominant_hex_colors = [
                self.rgb_to_hex(tuple(color)) for color in dominant_rgb_colors
            ]

            return {
                "feature_mode": self.feature_mode,
                "feature_vector": feature_vector,
                "dominant_hex_colors": dominant_hex_colors,
                "dominant_rgb_colors": dominant_rgb_colors.astype(int).tolist(),
            }

        except (ImageProcessingError, ValidationError):
            raise
        except Exception as exc:
            raise ImageProcessingError(f"Failed to extract features: {str(exc)}")

    def rgb_to_hex(self, rgb_tuple: tuple[int, int, int]) -> str:
        """
        Convert an RGB tuple into a hex color string.

        Example:
            ``(59, 47, 47)`` becomes ``"#3B2F2F"``.
        """
        red, green, blue = [int(value) for value in rgb_tuple]
        return f"#{red:02X}{green:02X}{blue:02X}"

    def extract_dominant_colors(
        self,
        image: np.ndarray,
        num_colors: int | None = None,
    ) -> list[Color]:
        """
        Return dominant colors as ``Color`` objects for existing project code.

        New clustering code should usually use ``extract_features`` because it
        includes the flat feature vector and hex colors together.
        """
        features = self.extract_features(image, num_colors=num_colors or self.num_colors)
        return [
            Color(r=color[0], g=color[1], b=color[2])
            for color in features["dominant_rgb_colors"]
        ]

    def _resize_for_speed(self, image: np.ndarray) -> np.ndarray:
        """
        Resize image to a modest maximum dimension while preserving aspect ratio.

        KMeans can be slow on large images because each pixel is a data point.
        A smaller copy still captures the overall palette while running quickly.
        """
        height, width = image.shape[:2]
        largest_dimension = max(width, height)

        if largest_dimension <= self.resize_dimension:
            return image

        scale = self.resize_dimension / largest_dimension
        new_size = (int(width * scale), int(height * scale))
        return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)

    def _find_dominant_colors(self, pixels: np.ndarray, num_colors: int) -> np.ndarray:
        """
        Use KMeans to find the most representative RGB colors.

        The cluster centers are the dominant colors. Sorting by cluster size
        makes the output stable and places the most common color first.
        """
        if num_colors < 1:
            raise ValidationError("num_colors must be at least 1.")

        unique_pixel_count = np.unique(pixels, axis=0).shape[0]
        # Do not ask for more colors than exist.
        cluster_count = min(num_colors, unique_pixel_count)

        kmeans = KMeans(
            n_clusters=cluster_count,
            random_state=self.random_state,
            n_init=10,
        )
        kmeans.fit(pixels)

        labels, counts = np.unique(kmeans.labels_, return_counts=True)
        labels_by_popularity = labels[np.argsort(-counts)]
        colors = kmeans.cluster_centers_[labels_by_popularity]

        return np.clip(np.rint(colors), 0, 255).astype(int)

    def _validate_image(self, image: np.ndarray) -> None:
        """
        Make sure the input looks like a color OpenCV image.

        OpenCV color images should have shape ``(height, width, 3)``.
        """
        if not isinstance(image, np.ndarray):
            raise ImageProcessingError("Image must be a NumPy array.")

        if image.size == 0:
            raise ImageProcessingError("Image array is empty.")

        if image.ndim != 3 or image.shape[2] != 3:
            raise ImageProcessingError(
                "Image must be a color image with 3 channels.",
                error_code="INVALID_IMAGE_SHAPE",
            )
