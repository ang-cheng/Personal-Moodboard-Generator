"""
Configuration module for the Personal Moodboard Generator backend.

This module loads configuration settings from environment variables using python-dotenv.
It provides a centralized place to manage all app configuration, making it easy to:
- Switch between development, production, and testing environments
- Set API keys and external service credentials
- Configure application behavior (number of images, clusters, timeouts, etc.)

Environment variables should be set in a .env file in the backend directory.
See .env.example for required and optional variables.
"""

import os
from dotenv import load_dotenv

# Load local settings from .env when it exists.
# This keeps secrets out of the code.
load_dotenv()


class Config:
    """
    Base configuration class with default settings common to all environments.
    
    Settings can be overridden by:
    1. Environment variables (highest priority)
    2. Environment-specific config classes (Development, Production, Testing)
    3. Default values defined here (lowest priority)
    """
    
    # Flask app settings.
    
    DEBUG = False
    """Enable/disable debug mode. When True, shows detailed error messages."""
    
    TESTING = False
    """Enable/disable testing mode. When True, disables error catching during request handling."""
    
    # Where the server runs.
    
    # Let Flask run on a different port when needed.
    PORT = int(os.getenv("PORT", 5000))
    """
    Port on which the Flask server will listen.
    
    Default: 5000
    Environment variable: PORT
    Example: PORT=8000
    """
    
    HOST = "0.0.0.0"
    """
    Host address on which the Flask server will listen.
    Use "0.0.0.0" to accept connections from any IP address.
    Use "127.0.0.1" to only accept local connections.
    """
    
    # Which setup we are using.
    
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    """
    Current Flask environment: development, production, or testing.
    
    Default: development
    Environment variable: FLASK_ENV
    """
    
    # API basics.
    
    API_VERSION = "v1"
    """API version string used in routes."""
    
    JSON_SORT_KEYS = False
    """Whether to sort JSON response keys alphabetically."""
    
    # Unsplash settings.
    
    # Unsplash needs this key to search for images.
    UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
    """
    Your Unsplash API access key for searching images.
    
    Get your key from: https://unsplash.com/oauth/applications
    
    Default: "" (empty - API calls will fail without this)
    Environment variable: UNSPLASH_ACCESS_KEY
    Example: UNSPLASH_ACCESS_KEY=abc123def456
    """
    
    UNSPLASH_BASE_URL = "https://api.unsplash.com"
    """Base URL for the Unsplash API (do not change unless using a proxy)."""
    
    # Image size settings.
    
    MAX_IMAGE_SIZE = 1024
    """Maximum dimension (width or height) for downloaded images in pixels."""
    
    MIN_IMAGE_SIZE = 256
    """Minimum dimension (width or height) for downloaded images in pixels."""
    
    # Moodboard defaults.
    
    # Use this when a request does not pick an image count.
    DEFAULT_NUM_IMAGES = int(os.getenv("DEFAULT_NUM_IMAGES", 5))
    """
    Default number of images to fetch when generating a moodboard.
    
    Default: 5
    Environment variable: DEFAULT_NUM_IMAGES
    Example: DEFAULT_NUM_IMAGES=10
    
    Note: Higher values take longer to process.
    """
    
    # Use this for palette detail.
    DEFAULT_NUM_CLUSTERS = int(os.getenv("DEFAULT_NUM_CLUSTERS", 5))
    """
    Default number of dominant colors to extract per image.
    
    Default: 5
    Environment variable: DEFAULT_NUM_CLUSTERS
    Example: DEFAULT_NUM_CLUSTERS=8
    
    Note: This is used for color palette generation.
    """
    
    # Waiting limits.
    
    EXTERNAL_API_TIMEOUT = 10
    """
    Timeout in seconds for external API calls (e.g., Unsplash API, image downloads).
    
    If an external service takes longer than this to respond, the request will fail.
    """
    
    # Logging.
    
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    """
    Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL.
    
    Default: INFO
    Environment variable: LOG_LEVEL
    """


class DevelopmentConfig(Config):
    """
    Development environment configuration.
    
    Use this for local development. Enables debug mode for detailed error messages.
    """
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """
    Production environment configuration.
    
    Use this when deploying to production. Disables debug mode for security.
    """
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """
    Testing environment configuration.
    
    Use this when running automated tests. Enables testing mode.
    """
    DEBUG = True
    TESTING = True


# Match each environment name with its settings.
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config(config_name=None):
    """
    Get the appropriate configuration object based on the environment.
    
    This function loads the right configuration class depending on:
    1. The config_name parameter (if provided)
    2. The FLASK_ENV environment variable
    3. Default to development configuration
    
    Args:
        config_name (str, optional): Name of the configuration to load.
                                     Options: "development", "production", "testing"
                                     If None, uses FLASK_ENV environment variable.
    
    Returns:
        Config: An instance of the appropriate configuration class.
    
    Example:
        >>> config = get_config()  # Uses FLASK_ENV env var
        >>> dev_config = get_config("development")  # Force development config
    """
    if config_name is None:
        # Use FLASK_ENV when nothing was passed in.
        config_name = os.getenv("FLASK_ENV", "development")
    
    # Unknown names use the local settings.
    config_class = config_by_name.get(config_name, config_by_name["default"])
    
    return config_class
