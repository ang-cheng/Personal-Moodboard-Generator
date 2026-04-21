"""
Validators utility module for the Personal Moodboard Generator backend.

This module provides input validation functions for API parameters and payloads.
"""

import re
from typing import Any, List, Optional
from utils.errors import ValidationError


DEFAULT_NUM_IMAGES = 24
DEFAULT_NUM_CLUSTERS = 3
MIN_NUM_IMAGES = 1
MAX_NUM_IMAGES = 60
MIN_NUM_CLUSTERS = 1
MAX_NUM_CLUSTERS = 12
SUPPORTED_FEATURE_MODES = {"dominant_colors"}


def validate_string(
    value: Any,
    field_name: str,
    min_length: int = 1,
    max_length: Optional[int] = None,
    pattern: Optional[str] = None,
) -> str:
    """
    Validate a string input.
    
    Args:
        value: The value to validate.
        field_name: Name of the field for error messages.
        min_length: Minimum allowed string length.
        max_length: Maximum allowed string length (optional).
        pattern: Regex pattern for validation (optional).
    
    Returns:
        The validated string.
    
    Raises:
        ValidationError: If validation fails.
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string.")
    
    if len(value) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters.")
    
    if max_length and len(value) > max_length:
        raise ValidationError(f"{field_name} must not exceed {max_length} characters.")
    
    if pattern and not re.match(pattern, value):
        raise ValidationError(f"{field_name} format is invalid.")
    
    return value


def validate_integer(
    value: Any,
    field_name: str,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
) -> int:
    """
    Validate an integer input.
    
    Args:
        value: The value to validate.
        field_name: Name of the field for error messages.
        min_value: Minimum allowed value (optional).
        max_value: Maximum allowed value (optional).
    
    Returns:
        The validated integer.
    
    Raises:
        ValidationError: If validation fails.
    """
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValidationError(f"{field_name} must be an integer.")
    
    if min_value is not None and value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}.")
    
    if max_value is not None and value > max_value:
        raise ValidationError(f"{field_name} must not exceed {max_value}.")
    
    return value


def validate_choices(
    value: Any,
    field_name: str,
    allowed_choices: List[Any],
) -> Any:
    """
    Validate that a value is one of the allowed choices.
    
    Args:
        value: The value to validate.
        field_name: Name of the field for error messages.
        allowed_choices: List of allowed values.
    
    Returns:
        The validated value.
    
    Raises:
        ValidationError: If validation fails.
    """
    if value not in allowed_choices:
        raise ValidationError(
            f"{field_name} must be one of: {', '.join(map(str, allowed_choices))}."
        )
    
    return value


def validate_url(value: Any, field_name: str) -> str:
    """
    Validate a URL.
    
    Args:
        value: The value to validate.
        field_name: Name of the field for error messages.
    
    Returns:
        The validated URL.
    
    Raises:
        ValidationError: If validation fails.
    """
    url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return validate_string(value, field_name, pattern=url_pattern)


def validate_query(value: Any) -> str:
    """
    Validate the search query used to find source images.

    The query must be a non-empty string after trimming whitespace.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("query must be a non-empty string.")

    return value.strip()


def validate_num_images(value: Any = None) -> int:
    """
    Validate the requested number of images.

    If the client omits the value, we default to 24. The upper limit keeps API
    requests and image processing work reasonable for a classroom project.
    """
    if value is None:
        return DEFAULT_NUM_IMAGES

    num_images = validate_integer(
        value,
        "num_images",
        min_value=MIN_NUM_IMAGES,
        max_value=MAX_NUM_IMAGES,
    )
    return num_images


def validate_num_clusters(value: Any = None, num_images: Optional[int] = None) -> int:
    """
    Validate the requested number of moodboard clusters.

    If ``num_images`` is provided, the cluster count cannot exceed it because
    KMeans cannot create more clusters than there are images.
    """
    if value is None:
        num_clusters = DEFAULT_NUM_CLUSTERS
    else:
        num_clusters = validate_integer(
            value,
            "num_clusters",
            min_value=MIN_NUM_CLUSTERS,
            max_value=MAX_NUM_CLUSTERS,
        )

    if num_images is not None and num_clusters > num_images:
        raise ValidationError("num_clusters cannot exceed num_images.")

    return num_clusters


def validate_feature_mode(value: Any = None) -> str:
    """
    Validate feature extraction mode.

    The backend currently implements only dominant color features.
    """
    feature_mode = value or "dominant_colors"

    if feature_mode not in SUPPORTED_FEATURE_MODES:
        raise ValidationError(
            "feature_mode currently only supports 'dominant_colors'.",
            error_code="UNSUPPORTED_FEATURE_MODE",
        )

    return feature_mode


def validate_preview_features_payload(payload: Any) -> dict:
    """
    Validate request JSON for ``POST /api/moodboards/preview-features``.
    """
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object.")

    return {
        "query": validate_query(payload.get("query")),
        "num_images": validate_num_images(payload.get("num_images")),
        "feature_mode": validate_feature_mode(payload.get("feature_mode")),
    }


def validate_generate_moodboards_payload(payload: Any) -> dict:
    """
    Validate request JSON for ``POST /api/moodboards/generate``.
    """
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object.")

    num_images = validate_num_images(payload.get("num_images"))

    return {
        "query": validate_query(payload.get("query")),
        "num_images": num_images,
        "num_clusters": validate_num_clusters(
            payload.get("num_clusters"),
            num_images=num_images,
        ),
        "feature_mode": validate_feature_mode(payload.get("feature_mode")),
    }
