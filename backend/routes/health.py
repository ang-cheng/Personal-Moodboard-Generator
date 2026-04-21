"""
Health check routes for the Personal Moodboard Generator backend.

This module provides endpoints for monitoring application health status.
"""

from flask import Blueprint
from utils.response import success_response

# Create health blueprint
health_bp = Blueprint("health", __name__, url_prefix="/api/health")


@health_bp.route("", methods=["GET"])
def get_health():
    """
    Health check endpoint.
    
    Returns:
        JSON response with health status.
        
    Example response:
        {
            "ok": true,
            "data": {
                "status": "healthy"
            }
        }
    """
    return success_response({"status": "healthy"})
