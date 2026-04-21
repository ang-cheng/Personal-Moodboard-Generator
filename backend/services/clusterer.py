"""
Clustering service for moodboard items.

This module groups images by their extracted feature vectors. The feature
vectors are created earlier in the pipeline by ``FeatureExtractor`` and should
represent each image's dominant colors.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np
from sklearn.cluster import KMeans

from utils.errors import ImageProcessingError, ValidationError


class Clusterer:
    """
    Cluster moodboard image items with scikit-learn KMeans.

    Args:
        random_state: Seed used by KMeans so clustering is reproducible in
            tests and classroom demos.
    """

    def __init__(self, random_state: int = 42, images_per_moodboard: int = 6):
        """Store clustering configuration."""
        # Each card should show the same number of images.
        self.random_state = random_state
        self.images_per_moodboard = images_per_moodboard

    def cluster_items(self, items: list[dict], num_clusters: int) -> list[dict]:
        """
        Group image items into moodboard clusters.

        Each input item should already contain:
        - id
        - image_url
        - metadata
        - feature_vector
        - dominant_hex_colors

        Args:
            items: Image items with extracted features.
            num_clusters: Requested number of clusters.

        Returns:
            List of normalized cluster dictionaries.
        """
        if not isinstance(items, list):
            raise ValidationError("items must be a list of dictionaries.")

        if num_clusters < 1:
            raise ValidationError("num_clusters must be at least 1.")

        valid_items = self._get_valid_items(items)
        if not valid_items:
            return []

        # Do not make more groups than images.
        cluster_count = min(num_clusters, len(valid_items))

        try:
            # Put each image's colors into one row.
            feature_matrix = np.array(
                [item["feature_vector"] for item in valid_items],
                dtype=np.float32,
            )

            labels = self._cluster_feature_matrix(feature_matrix, cluster_count)
            return self._build_cluster_response(
                valid_items,
                labels,
                cluster_count,
            )

        except Exception as exc:
            raise ImageProcessingError(f"Failed to cluster items: {str(exc)}")

    def _get_valid_items(self, items: list[dict]) -> list[dict]:
        """
        Keep only items that have the fields needed for clustering.

        Invalid records are skipped so one bad image does not break the whole
        moodboard generation process.
        """
        valid_items: list[dict] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            feature_vector = item.get("feature_vector")
            if not feature_vector:
                continue

            try:
                # Keep only number rows.
                numeric_vector = [float(value) for value in feature_vector]
            except (TypeError, ValueError):
                continue

            valid_item = dict(item)
            valid_item["feature_vector"] = numeric_vector
            valid_items.append(valid_item)

        return valid_items

    def _cluster_feature_matrix(
        self,
        feature_matrix: np.ndarray,
        cluster_count: int,
    ) -> np.ndarray:
        """
        Run KMeans and return one cluster label for each input row.

        If there is only one cluster, every item belongs to cluster 0 and we can
        avoid calling KMeans entirely.
        """
        if cluster_count == 1:
            return np.zeros(feature_matrix.shape[0], dtype=int)

        kmeans = KMeans(
            n_clusters=cluster_count,
            random_state=self.random_state,
            n_init=10,
        )
        return kmeans.fit_predict(feature_matrix)

    def _build_cluster_response(
        self,
        items: list[dict],
        labels: np.ndarray,
        cluster_count: int,
    ) -> list[dict]:
        """
        Convert KMeans labels into the normalized API-friendly response shape.
        """
        clusters: list[dict] = []

        for cluster_index in range(cluster_count):
            cluster_items = [
                item
                for item, label in zip(items, labels)
                if int(label) == cluster_index
            ]

            if not cluster_items:
                continue

            # Add images to short groups so the cards look even.
            display_items = self._fill_cluster_items(cluster_items, items)

            clusters.append(
                {
                    "id": f"cluster_{cluster_index}",
                    "title": f"Moodboard {len(clusters) + 1}",
                    "summary": {
                        "dominant_hex_colors": self._summarize_hex_colors(
                            cluster_items
                        ),
                    },
                    "images": [
                        self._normalize_image_item(item, f"cluster_{cluster_index}")
                        for item in display_items
                    ],
                }
            )

        return clusters

    def _fill_cluster_items(
        self,
        cluster_items: list[dict],
        all_items: list[dict],
    ) -> list[dict]:
        """
        Return enough images for a full moodboard card when possible.

        KMeans clusters are naturally uneven, so a cluster may only contain a
        few images. The UI expects eight images per moodboard, so short clusters
        are topped up with other loaded images while avoiding duplicates inside
        a single card.
        """
        display_items = list(cluster_items[: self.images_per_moodboard])
        seen_ids = {item.get("id") for item in display_items}

        for item in all_items:
            if len(display_items) >= self.images_per_moodboard:
                break

            item_id = item.get("id")
            if item_id in seen_ids:
                continue

            # These extras are just for the card preview.
            display_items.append(item)
            seen_ids.add(item_id)

        return display_items

    def _summarize_hex_colors(self, items: list[dict], limit: int = 5) -> list[str]:
        """
        Pick the most common dominant hex colors in a cluster.

        This gives the frontend a quick palette for the whole moodboard cluster.
        """
        all_colors: list[str] = []

        for item in items:
            colors = item.get("dominant_hex_colors") or []
            all_colors.extend(str(color) for color in colors)

        color_counts = Counter(all_colors)
        return [color for color, _count in color_counts.most_common(limit)]

    def _normalize_image_item(self, item: dict, cluster_id: str) -> dict[str, Any]:
        """
        Keep the image fields expected by downstream code and the frontend.
        """
        metadata = item.get("metadata", {})

        return {
            "id": item.get("id"),
            "image_url": item.get("image_url"),
            "thumbnail_url": metadata.get("thumbnail_url") or item.get("image_url"),
            "alt_text": metadata.get("alt_text") or "Moodboard image",
            "cluster_id": cluster_id,
            "metadata": metadata,
            "feature_vector": item.get("feature_vector", []),
            "dominant_hex_colors": item.get("dominant_hex_colors", []),
        }


class ColorClusterer(Clusterer):
    """
    Small compatibility wrapper for older project code.

    New code should use ``Clusterer.cluster_items``. The older moodboard
    generator imported ``ColorClusterer`` for palette generation, so this keeps
    that import from breaking during the migration.
    """

    def generate_palette(self, all_colors: list[Any], palette_size: int = 5) -> list[Any]:
        """
        Return a simple de-duplicated color palette from older ``Color`` objects.

        This method is intentionally small because item clustering is now the
        main responsibility of this module.
        """
        palette: list[Any] = []
        seen: set[tuple[Any, Any, Any]] = set()

        for color in all_colors:
            color_key = (
                getattr(color, "r", None),
                getattr(color, "g", None),
                getattr(color, "b", None),
            )

            if color_key in seen:
                continue

            seen.add(color_key)
            palette.append(color)

            if len(palette) >= palette_size:
                break

        return palette
