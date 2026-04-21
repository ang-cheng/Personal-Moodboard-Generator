"""
Main Flask application for the Personal Moodboard Generator backend.

This module initializes the Flask application, registers blueprints,
and configures error handling.
"""

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from config import get_config
from routes.health import health_bp
from routes.moodboards import moodboards_bp
from utils.errors import MoodboardGeneratorError
from utils.response import error_response


def create_app(config_name=None):
    """
    Create and configure the Flask application.
    
    Args:
        config_name: Configuration name (development, production, testing).
                     If None, uses FLASK_ENV environment variable.
    
    Returns:
        Configured Flask application instance.
    """
    # Get configuration
    config = get_config(config_name)
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(moodboards_bp)
    
    # Register error handlers
    register_error_handlers(app)
    register_cors_headers(app)
    
    return app


def register_cors_headers(app):
    """
    Add lightweight CORS headers for the static frontend during local development.

    This avoids adding another dependency while allowing the browser frontend to
    call the Flask API from a different localhost port.
    """

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response


def register_error_handlers(app):
    """
    Register global error handlers for the Flask application.
    
    Args:
        app: Flask application instance.
    """
    
    @app.errorhandler(MoodboardGeneratorError)
    def handle_moodboard_error(error):
        """Handle custom application errors."""
        body, status_code = error_response(
            error.error_code,
            error.message,
            error.status_code,
        )
        return jsonify(body), status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        """Handle Flask/Werkzeug HTTP errors such as 400 and 404."""
        code = "HTTP_ERROR"

        if error.code == 400:
            code = "BAD_REQUEST"
        elif error.code == 404:
            code = "NOT_FOUND"
        elif error.code == 405:
            code = "METHOD_NOT_ALLOWED"

        message = error.description or error.name or "HTTP error"
        body, status_code = error_response(code, message, error.code or 500)
        return jsonify(body), status_code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors without leaking internal details."""
        body, status_code = error_response(
            "INTERNAL_ERROR",
            "Internal server error",
            500,
        )
        return jsonify(body), status_code


if __name__ == "__main__":
    # Create the application with development configuration
    app = create_app()
    
    # Extract host and port from configuration
    host = app.config.get("HOST", "0.0.0.0")
    port = app.config.get("PORT", 5000)
    debug = app.config.get("DEBUG", False)
    
    # Run development server
    # Note: The debug parameter is set based on the Flask app's DEBUG setting
    app.run(host=host, port=port, debug=debug)
