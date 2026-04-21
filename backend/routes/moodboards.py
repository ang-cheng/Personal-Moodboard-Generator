"""
Moodboard routes for the Personal Moodboard Generator backend.

The blueprint keeps HTTP concerns here:
- read JSON request bodies
- validate request fields
- call the MoodboardGenerator service
- return consistent JSON response envelopes
"""

from flask import Blueprint, jsonify, request

from services.clusterer import Clusterer
from services.feature_extractor import FeatureExtractor
from services.image_loader import ImageLoader
from services.moodboard_generator import MoodboardGenerator
from services.unsplash_client import UnsplashClient
from utils.response import success_response
from utils.validators import (
    validate_generate_moodboards_payload,
    validate_preview_features_payload,
)


moodboards_bp = Blueprint("moodboards", __name__, url_prefix="/api/moodboards")


def _get_json_body() -> dict:
    """
    Parse the JSON request body.

    ``silent=True`` prevents Flask from returning its own HTML/HTTP error. If
    the body is missing or invalid, the validator raises our JSON ValidationError.
    """
    return request.get_json(silent=True)


def _create_moodboard_generator() -> MoodboardGenerator:
    """
    Build the moodboard generator with its service dependencies.

    Keeping this in one helper makes the endpoint functions small and makes it
    easier to replace dependencies in tests later.
    """
    return MoodboardGenerator(
        unsplash_client=UnsplashClient(),
        image_loader=ImageLoader(),
        feature_extractor=FeatureExtractor(),
        clusterer=Clusterer(),
    )


@moodboards_bp.route("/generate", methods=["POST"])
def generate_moodboards():
    """
    Generate clustered moodboards from a search query.

    Expected JSON body:
        {
            "query": "cozy cabin",
            "num_images": 24,
            "num_clusters": 3,
            "feature_mode": "dominant_colors"
        }

    Success response shape:
        {
            "ok": true,
            "data": {
                "query": "...",
                "num_clusters": 3,
                "moodboards": [...]
            },
            "meta": {
                "processing_time_ms": 1234
            }
        }
    """
    payload = validate_generate_moodboards_payload(_get_json_body())
    # Make fresh helpers for this request.
    generator = _create_moodboard_generator()

    result = generator.generate_moodboards(
        query=payload["query"],
        num_images=payload["num_images"],
        num_clusters=payload["num_clusters"],
        feature_mode=payload["feature_mode"],
    )

    data = {
        # Send back only what the page needs.
        "query": result["query"],
        "num_clusters": result["num_clusters"],
        "moodboards": result["moodboards"],
    }

    meta = {}
    if "processing_time_seconds" in result:
        # Milliseconds look nicer on the page.
        meta["processing_time_ms"] = round(result["processing_time_seconds"] * 1000)

    body, status_code = success_response(data=data, meta=meta)
    return jsonify(body), status_code


@moodboards_bp.route("/preview-features", methods=["POST"])
def preview_features():
    """
    Preview image features for a search query without clustering.

    Expected JSON body:
        {
            "query": "cozy cabin",
            "num_images": 24,
            "feature_mode": "dominant_colors"
        }

    Success response shape:
        {
            "ok": true,
            "data": {
                "query": "...",
                "images": [...]
            }
        }
    """
    payload = validate_preview_features_payload(_get_json_body())
    # Preview uses the same helpers.
    generator = _create_moodboard_generator()

    result = generator.preview_features(
        query=payload["query"],
        num_images=payload["num_images"],
        feature_mode=payload["feature_mode"],
    )

    data = {
        "query": result["query"],
        "images": result["images"],
    }

    body, status_code = success_response(data=data)
    return jsonify(body), status_code
