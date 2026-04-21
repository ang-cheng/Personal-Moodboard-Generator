"""
Moodboard generator service.

This module is the orchestration layer for the backend moodboard workflow. It
does not do image search, image loading, feature extraction, or clustering by
itself. Instead, it coordinates those smaller services in a clear sequence:

1. Search for image metadata.
2. Load usable images.
3. Extract visual features.
4. Cluster the feature vectors into moodboards.

The methods return plain dictionaries so Flask routes can pass them directly to
``jsonify`` for the ``/api/moodboards/generate`` and
``/api/moodboards/preview-features`` endpoints.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from typing import Any

from utils.errors import MoodboardGeneratorError, ValidationError


class MoodboardGenerator:
    """
    Coordinate search, loading, feature extraction, and clustering services.

    Args:
        unsplash_client: Service with ``search_photos(query, per_page)``.
        image_loader: Service with ``batch_load_images(image_records)``.
        feature_extractor: Service with ``extract_features(image)``.
        clusterer: Service with ``cluster_items(items, num_clusters)``.
    """

    def __init__(
        self,
        unsplash_client: Any,
        image_loader: Any,
        feature_extractor: Any,
        clusterer: Any,
    ):
        """Store the service dependencies supplied by the application."""
        self.unsplash_client = unsplash_client
        self.image_loader = image_loader
        self.feature_extractor = feature_extractor
        self.clusterer = clusterer

    def preview_features(
        self,
        query: str,
        num_images: int,
        feature_mode: str = "dominant_colors",
    ) -> dict:
        """
        Search images and preview extracted features without clustering.

        This method is shaped for ``POST /api/moodboards/preview-features``.
        It is useful when a frontend wants to show which images were found and
        what color features were extracted before generating final moodboards.

        Args:
            query: Search text for Unsplash.
            num_images: Number of image results to request.
            feature_mode: Feature extraction strategy. Currently supports
                ``"dominant_colors"``.

        Returns:
            API-ready dictionary containing the query, timing, and image feature
            records.
        """
        start_time = time.perf_counter()
        self._validate_request(query, num_images)
        self._validate_feature_mode(feature_mode)

        try:
            image_records = self._search_images(query, num_images)
            loaded_images = self.image_loader.batch_load_images(image_records)
            featured_items, skipped_counts = self._extract_feature_items(
                loaded_images,
                feature_mode=feature_mode,
                allow_empty=True,
            )

            return self._json_ready(
                {
                    "query": query.strip(),
                    "feature_mode": feature_mode,
                    "num_images_requested": num_images,
                    "num_images_found": len(image_records),
                    "num_images_loaded": len(loaded_images),
                    "num_images_with_features": len(featured_items),
                    "skipped": skipped_counts,
                    "processing_time_seconds": self._elapsed_seconds(start_time),
                    "images": featured_items,
                }
            )

        except (MoodboardGeneratorError, ValidationError):
            raise
        except Exception as exc:
            raise MoodboardGeneratorError(
                f"Feature preview failed: {str(exc)}",
                status_code=500,
            )

    def generate_moodboards(
        self,
        query: str,
        num_images: int,
        num_clusters: int,
        feature_mode: str = "dominant_colors",
    ) -> dict:
        """
        Search images, extract features, and cluster them into moodboards.

        This method is shaped for ``POST /api/moodboards/generate``.

        Args:
            query: Search text for Unsplash.
            num_images: Number of image results to request.
            num_clusters: Desired number of moodboard clusters.
            feature_mode: Feature extraction strategy. Currently supports
                ``"dominant_colors"``.

        Returns:
            API-ready dictionary containing the query, timing, and generated
            moodboard clusters.
        """
        start_time = time.perf_counter()
        self._validate_request(query, num_images)
        self._validate_num_clusters(num_clusters)
        self._validate_feature_mode(feature_mode)

        try:
            image_records = self._search_images(query, num_images)
            loaded_images = self.image_loader.batch_load_images(image_records)
            featured_items, skipped_counts = self._extract_feature_items(
                loaded_images,
                feature_mode=feature_mode,
                allow_empty=True,
            )
            moodboards = self.clusterer.cluster_items(featured_items, num_clusters)

            return self._json_ready(
                {
                    "query": query.strip(),
                    "feature_mode": feature_mode,
                    "num_images_requested": num_images,
                    "num_images_found": len(image_records),
                    "num_images_loaded": len(loaded_images),
                    "num_images_clustered": len(featured_items),
                    "requested_num_clusters": num_clusters,
                    "num_clusters": len(moodboards),
                    "skipped": skipped_counts,
                    "processing_time_seconds": self._elapsed_seconds(start_time),
                    "moodboards": moodboards,
                }
            )

        except (MoodboardGeneratorError, ValidationError):
            raise
        except Exception as exc:
            raise MoodboardGeneratorError(
                f"Moodboard generation failed: {str(exc)}",
                status_code=500,
            )

    def _search_images(self, query: str, num_images: int) -> list[dict]:
        """
        Search Unsplash and return normalized image metadata records.
        """
        image_records = self.unsplash_client.search_photos(
            query.strip(),
            per_page=num_images,
        )

        return image_records or []

    def _extract_feature_items(
        self,
        loaded_images: list[dict],
        feature_mode: str,
        allow_empty: bool = False,
    ) -> tuple[list[dict], dict[str, int]]:
        """
        Convert loaded image bundles into cluster-ready feature items.

        ``ImageLoader`` bundles include a NumPy image array, which cannot be sent
        directly in an API response. This method extracts features and then keeps
        only JSON-friendly fields.
        """
        featured_items: list[dict] = []
        skipped_reasons: Counter[str] = Counter()

        for bundle in loaded_images:
            try:
                features = self.feature_extractor.extract_features(
                    bundle["image"],
                    feature_mode=feature_mode,
                )
            except Exception:
                # A single bad image should not stop the whole batch.
                skipped_reasons["feature_extraction_failed"] += 1
                continue

            featured_items.append(
                {
                    "id": bundle.get("id"),
                    "image_url": bundle.get("image_url"),
                    "metadata": bundle.get("metadata", {}),
                    "feature_vector": features.get("feature_vector", []),
                    "dominant_hex_colors": features.get("dominant_hex_colors", []),
                }
            )

        if not featured_items and not allow_empty:
            raise MoodboardGeneratorError(
                "No valid image features could be extracted.",
                status_code=422,
                error_code="NO_FEATURES_EXTRACTED",
            )

        return featured_items, dict(skipped_reasons)

    def _validate_request(self, query: str, num_images: int) -> None:
        """Validate fields shared by preview and generate requests."""
        if not isinstance(query, str) or not query.strip():
            raise ValidationError("query must be a non-empty string.")

        if not isinstance(num_images, int) or num_images < 1:
            raise ValidationError("num_images must be a positive integer.")

    def _validate_num_clusters(self, num_clusters: int) -> None:
        """Validate the requested number of moodboard clusters."""
        if not isinstance(num_clusters, int) or num_clusters < 1:
            raise ValidationError("num_clusters must be a positive integer.")

    def _validate_feature_mode(self, feature_mode: str) -> None:
        """
        Validate feature mode before running expensive image work.

        The extractor currently implements dominant-color vectors, so the
        generator makes that contract explicit at the API boundary.
        """
        if feature_mode != "dominant_colors":
            raise ValidationError(
                f"Unsupported feature_mode: {feature_mode}",
                error_code="UNSUPPORTED_FEATURE_MODE",
            )

    def _elapsed_seconds(self, start_time: float) -> float:
        """Return elapsed processing time rounded for readable API output."""
        return round(time.perf_counter() - start_time, 4)

    def _json_ready(self, payload: dict) -> dict:
        """
        Return a JSON-safe copy of a response payload.

        The service should only emit plain Python data. The json round-trip is a
        simple guardrail that catches accidental NumPy values or other objects
        before Flask tries to serialize the response.
        """
        return json.loads(json.dumps(payload))
