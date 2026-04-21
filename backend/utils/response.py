"""
Response utility module for the Personal Moodboard Generator backend.

This module provides standardized response formatting for consistent API responses
across all endpoints.
"""

from typing import Any, Optional


def success_response(data: Any, meta: Optional[dict] = None, status_code: int = 200) -> tuple:
    """
    Create a standardized success response.

    Args:
        data: The response data payload.
        meta: Optional metadata about the response, such as counts or timing.
        status_code: HTTP status code (default: 200).

    Returns:
        Tuple of (response_dict, status_code) for Flask response.
    """
    body = {
        "ok": True,
        "data": data,
    }

    if meta is not None:
        body["meta"] = meta

    return body, status_code


def error_response(code: str, message: str, status_code: int) -> tuple:
    """
    Create a standardized error response.

    Args:
        code: Stable machine-readable error code.
        message: Human-readable message for debugging or display.
        status_code: HTTP status code.

    Returns:
        Tuple of (response_dict, status_code) for Flask response.
    """
    return (
        {
            "ok": False,
            "error": {
                "code": code,
                "message": message,
            },
        },
        status_code,
    )


def not_implemented_response(message: str = "Not yet implemented") -> tuple:
    """
    Create a response for not-yet-implemented endpoints.
    
    Args:
        message: Optional custom message.
    
    Returns:
        Tuple of (response_dict, status_code) for Flask response.
    """
    return error_response("NOT_IMPLEMENTED", message, 501)
