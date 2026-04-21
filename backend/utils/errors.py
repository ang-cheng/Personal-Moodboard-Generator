"""
Custom exception classes for the Flask backend.

Each exception carries an HTTP status code and a machine-readable error code.
The Flask app uses these fields to return consistent JSON errors.
"""


class MoodboardGeneratorError(Exception):
    """Base class for application errors that should become JSON responses."""

    def __init__(self, message, status_code=500, error_code="INTERNAL_ERROR"):
        """
        Create an application error.

        Args:
            message: Human-readable error message.
            status_code: HTTP status code to return.
            error_code: Stable machine-readable code for clients.
        """
        # Keep the details on the error.
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(MoodboardGeneratorError):
    """Raised when a request body or parameter is invalid."""

    def __init__(self, message, error_code="VALIDATION_ERROR"):
        super().__init__(message, status_code=400, error_code=error_code)


class UpstreamAPIError(MoodboardGeneratorError):
    """Raised when an upstream API, such as Unsplash, fails."""

    def __init__(self, message, error_code="UPSTREAM_API_ERROR"):
        super().__init__(message, status_code=502, error_code=error_code)


class ImageProcessingError(MoodboardGeneratorError):
    """Raised when an image cannot be loaded, decoded, or analyzed."""

    def __init__(self, message, error_code="IMAGE_PROCESSING_ERROR"):
        super().__init__(message, status_code=400, error_code=error_code)


class ClusteringError(MoodboardGeneratorError):
    """Raised when feature vectors cannot be clustered."""

    def __init__(self, message, error_code="CLUSTERING_ERROR"):
        super().__init__(message, status_code=500, error_code=error_code)


class NotFoundError(MoodboardGeneratorError):
    """Raised when a requested resource is not found."""

    def __init__(self, message, error_code="NOT_FOUND"):
        super().__init__(message, status_code=404, error_code=error_code)


# Older code still uses this name.
ExternalServiceError = UpstreamAPIError
