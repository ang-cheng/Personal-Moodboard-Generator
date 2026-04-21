"""
Image loader service for the Personal Moodboard Generator backend.

This module downloads images from URLs and decodes them into OpenCV arrays.
OpenCV stores color images in BGR channel order, so loaded images are returned
as BGR NumPy arrays.
"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np
import requests
from requests.exceptions import RequestException, Timeout

from config import Config
from utils.errors import ExternalServiceError, ImageProcessingError, ValidationError


class ImageLoader:
    """Service for loading images from URLs."""

    def __init__(self, timeout: int | None = None):
        """Initialize the loader with a request timeout."""
        self.timeout = timeout or Config.EXTERNAL_API_TIMEOUT
        self.max_size = Config.MAX_IMAGE_SIZE
        self.min_size = Config.MIN_IMAGE_SIZE

    def load_image_from_url(self, image_url: str) -> np.ndarray:
        """
        Download and decode an image from a URL.

        Args:
            image_url: Direct URL to an image file.

        Returns:
            OpenCV image array in BGR format.

        Raises:
            ValidationError: If the URL is missing or invalid.
            ExternalServiceError: If the image bytes cannot be downloaded.
            ImageProcessingError: If OpenCV cannot decode the image.
        """
        if not isinstance(image_url, str) or not image_url.strip():
            raise ValidationError("Image URL must be a non-empty string.")

        try:
            response = requests.get(image_url, timeout=self.timeout)
            response.raise_for_status()
        except Timeout:
            raise ExternalServiceError(
                f"Timed out while downloading image: {image_url}",
                error_code="IMAGE_DOWNLOAD_TIMEOUT",
            )
        except RequestException as exc:
            raise ExternalServiceError(
                f"Failed to download image {image_url}: {str(exc)}",
                error_code="IMAGE_DOWNLOAD_FAILED",
            )

        # Convert raw bytes into a 1D uint8 array. cv2.imdecode expects this
        # encoded byte buffer, not the final height x width x channels image.
        image_bytes = np.frombuffer(response.content, dtype=np.uint8)

        if image_bytes.size == 0:
            raise ImageProcessingError(
                f"Downloaded image is empty: {image_url}",
                error_code="EMPTY_IMAGE",
            )

        image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)

        if image is None:
            raise ImageProcessingError(
                f"Could not decode image data from URL: {image_url}",
                error_code="IMAGE_DECODE_FAILED",
            )

        self._validate_image_array(image)
        return image

    def batch_load_images(self, image_records: list[dict]) -> list[dict[str, Any]]:
        """
        Load many images from normalized metadata records.

        Each input record should contain at least an ``image_url`` value. Broken
        records or images are skipped so one bad image does not stop the batch.

        Args:
            image_records: Normalized image metadata dictionaries.

        Returns:
            List of image bundles with id, image_url, metadata, and image keys.
        """
        loaded_images: list[dict[str, Any]] = []

        if not isinstance(image_records, list):
            raise ValidationError("image_records must be a list of dictionaries.")

        for record in image_records:
            if not isinstance(record, dict):
                continue

            image_url = record.get("image_url")
            if not image_url:
                continue

            try:
                image = self.load_image_from_url(image_url)
            except (ExternalServiceError, ImageProcessingError, ValidationError):
                # Skip images that are missing, unavailable, or not decodable.
                # Batch callers can still use the images that loaded correctly.
                continue

            loaded_images.append(
                {
                    "id": record.get("id"),
                    "image_url": image_url,
                    "metadata": record,
                    "image": image,
                }
            )

        return loaded_images

    def _validate_image_array(self, image: np.ndarray) -> None:
        """
        Check that a decoded image is usable for feature extraction.

        Args:
            image: OpenCV image array.

        Raises:
            ImageProcessingError: If the image is malformed or too small.
        """
        if image.ndim != 3 or image.shape[2] != 3:
            raise ImageProcessingError(
                "Image must have three color channels.",
                error_code="INVALID_IMAGE_CHANNELS",
            )

        height, width = image.shape[:2]
        if width < self.min_size or height < self.min_size:
            raise ImageProcessingError(
                f"Image is too small. Minimum size: {self.min_size}x{self.min_size}px, "
                f"got {width}x{height}px.",
                error_code="IMAGE_TOO_SMALL",
            )

    def resize_image(
        self,
        image: np.ndarray,
        max_dimension: int | None = None,
    ) -> np.ndarray:
        """
        Resize an OpenCV image while maintaining its aspect ratio.

        Args:
            image: OpenCV image array.
            max_dimension: Maximum width or height. Uses config default if None.

        Returns:
            Resized OpenCV image array.
        """
        if max_dimension is None:
            max_dimension = self.max_size

        height, width = image.shape[:2]
        largest_dimension = max(width, height)

        if largest_dimension <= max_dimension:
            return image

        scale = max_dimension / largest_dimension
        new_size = (int(width * scale), int(height * scale))
        return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)

    def convert_to_rgb(self, image: np.ndarray) -> np.ndarray:
        """
        Convert an OpenCV BGR image to RGB.

        Feature extraction code commonly expects RGB arrays, while OpenCV loads
        images as BGR. This helper makes that conversion explicit.
        """
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    def image_to_array(self, image: np.ndarray) -> np.ndarray:
        """
        Return an image as a NumPy uint8 array.

        This method keeps older calling code readable now that the loader already
        works with NumPy arrays.
        """
        return np.asarray(image, dtype=np.uint8)
