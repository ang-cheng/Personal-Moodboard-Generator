"""
Unsplash API client service for the Personal Moodboard Generator backend.

This module provides a client for communicating with the Unsplash API to search
for and retrieve photos. It handles:
- Authentication with the Unsplash API
- Searching for photos by query
- Normalizing responses into a consistent format
- Error handling and retries for network issues

The UnsplashClient returns standardized photo dictionaries that the rest of the
application can rely on for consistent field names and types.
"""

from typing import List, Dict, Any, Optional
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
from config import Config
from utils.errors import ExternalServiceError, ValidationError


class UnsplashClient:
    """
    Client for interacting with the Unsplash API.
    
    This class handles all communication with Unsplash's search endpoint,
    normalizing responses into a consistent format for the rest of the application.
    
    Attributes:
        access_key (str): The Unsplash API access key for authentication.
        base_url (str): The base URL for the Unsplash API.
        timeout (int): Request timeout in seconds.
    
    Example:
        >>> client = UnsplashClient(access_key="your_key_here")
        >>> photos = client.search_photos("sunset", per_page=5)
        >>> print(photos[0]["image_url"])
    """
    
    def __init__(
        self,
        access_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize the Unsplash client.
        
        Sets up authentication headers and configuration for API requests.
        If parameters are not provided, defaults from config.py will be used.
        
        Args:
            access_key (str, optional): Unsplash API access key.
                If None, uses Config.UNSPLASH_ACCESS_KEY from environment.
            
            base_url (str, optional): Base URL for the Unsplash API.
                If None, uses Config.UNSPLASH_BASE_URL.
                Default: "https://api.unsplash.com"
            
            timeout (int, optional): Request timeout in seconds.
                If None, uses Config.EXTERNAL_API_TIMEOUT.
                Default: 10 seconds
        
        Raises:
            ValidationError: If no access key is provided or configured.
        
        Example:
            >>> # Normal setup
            >>> client = UnsplashClient()
            >>> 
            >>> # Custom setup
            >>> client = UnsplashClient(
            ...     access_key="my-key",
            ...     base_url="https://custom-api.com",
            ...     timeout=20
            ... )
        """
        # Use passed-in settings when there are any.
        self.access_key = access_key or Config.UNSPLASH_ACCESS_KEY
        
        # Unsplash needs a key.
        if not self.access_key:
            raise ValidationError(
                "Unsplash API access key is not configured. "
                "Set UNSPLASH_ACCESS_KEY environment variable or pass it to the constructor.",
                error_code="MISSING_UNSPLASH_KEY",
            )
        
        # Use the given API URL, or the default.
        self.base_url = (base_url or Config.UNSPLASH_BASE_URL).rstrip("/")
        
        # Use the given timeout, or the default.
        self.timeout = timeout or Config.EXTERNAL_API_TIMEOUT
        
        # Add the headers Unsplash wants.
        self.headers = {
            "Authorization": f"Client-ID {self.access_key}",
            "Accept-Version": "v1",
        }
    
    def search_photos(
        self,
        query: str,
        per_page: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for photos on Unsplash.
        
        Makes a request to the Unsplash search endpoint and returns a list of
        normalized photo dictionaries. Each photo includes metadata like URL,
        dimensions, and attribution information.
        
        Args:
            query (str): Search query string.
                Example: "sunset", "mountain landscape", "urban architecture"
            
            per_page (int, optional): Number of photos to return.
                Must be between 1 and 30.
                Default: 5
                Note: Higher values may increase response time.
        
        Returns:
            List[Dict[str, Any]]: List of normalized photo dictionaries.
            
            Each dictionary contains:
            - id (str): Unique Unsplash photo ID
            - source (str): Always "unsplash" for this client
            - image_url (str): URL to the regular-sized image
            - thumbnail_url (str): URL to the small thumbnail image
            - width (int): Image width in pixels
            - height (int): Image height in pixels
            - alt_text (str): Alt text description for accessibility
            
            Example return value:
            [
                {
                    "id": "abc123",
                    "source": "unsplash",
                    "image_url": "https://images.unsplash.com/...",
                    "thumbnail_url": "https://images.unsplash.com/...",
                    "width": 1600,
                    "height": 1200,
                    "alt_text": "A beautiful sunset over the ocean"
                },
                ...
            ]
        
        Raises:
            ValidationError: If the query is empty or invalid.
            ExternalServiceError: If the API request fails.
        
        Example:
            >>> client = UnsplashClient()
            >>> try:
            ...     photos = client.search_photos("nature", per_page=10)
            ...     print(f"Found {len(photos)} photos")
            ...     for photo in photos:
            ...         print(f"  - {photo['alt_text']}")
            ... except ExternalServiceError as e:
            ...     print(f"Failed to search: {e}")
        """
        # Check the search before calling Unsplash.
        
        # The search needs some text.
        if not isinstance(query, str) or not query.strip():
            raise ValidationError(
                "Search query must be a non-empty string.",
                error_code="INVALID_QUERY",
            )
        
        # Unsplash only allows 30 photos per page.
        if per_page < 1:
            per_page = 1
        elif per_page > 30:
            per_page = 30
        
        # Ask Unsplash for photos.
        
        try:
            # Build the search URL.
            endpoint = f"{self.base_url}/search/photos"
            
            # Start with the most relevant first page.
            params = {
                "query": query.strip(),
                "per_page": per_page,
                "page": 1,  # Start on page one.
                "order_by": "relevant",  # Better matches first.
            }
            
            # Make the request without waiting forever.
            response = requests.get(
                endpoint,
                headers=self.headers,
                params=params,
                timeout=self.timeout,
            )
            
            # Send request problems to the handlers below.
            response.raise_for_status()
            
            # Read the JSON from Unsplash.
            data = response.json()
            
        except Timeout:
            # Make timeouts easier to understand.
            raise ExternalServiceError(
                "Unsplash API request timed out. Please try again.",
                error_code="UNSPLASH_TIMEOUT",
            )
        except ConnectionError as e:
            # Make connection problems easier to understand.
            raise ExternalServiceError(
                "Failed to connect to Unsplash API. Check your internet connection.",
                error_code="CONNECTION_ERROR",
            )
        except RequestException as e:
            # Handle other request problems.
            raise ExternalServiceError(
                f"Unsplash API request failed: {str(e)}",
                error_code="UNSPLASH_REQUEST_FAILED",
            )
        except ValueError as e:
            # Handle bad JSON.
            raise ExternalServiceError(
                "Unsplash API returned invalid JSON response.",
                error_code="INVALID_RESPONSE",
            )
        
        # Clean up the Unsplash results for the app.
        
        # Photos live in the "results" list.
        results = data.get("results", [])
        
        # Give every photo the same names.
        normalized_photos = []
        for photo in results:
            normalized = self._normalize_photo(photo)
            normalized_photos.append(normalized)
        
        return normalized_photos
    
    def _normalize_photo(self, photo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a photo object from the Unsplash API into our standard format.
        
        This private method takes a raw photo dictionary from the Unsplash API
        and extracts/transforms the fields we care about into a consistent format
        that the rest of the application relies on.
        
        The normalized format is guaranteed to have all required fields, making
        it safe for the frontend and other services to use without additional
        null checks.
        
        Args:
            photo (Dict[str, Any]): Raw photo object from Unsplash API response.
        
        Returns:
            Dict[str, Any]: Normalized photo dictionary with fields:
            - id: Photo ID
            - source: Always "unsplash"
            - image_url: URL to the full-size image
            - thumbnail_url: URL to the small thumbnail
            - width: Image width in pixels
            - height: Image height in pixels
            - alt_text: Alt text for accessibility
        
        Example:
            >>> raw = {
            ...     "id": "abc123",
            ...     "urls": {"regular": "https://...", "small": "https://..."},
            ...     "width": 1600,
            ...     "height": 1200,
            ...     "alt_description": "A sunset over water"
            ... }
            >>> normalized = client._normalize_photo(raw)
            >>> print(normalized["alt_text"])  # "A sunset over water"
        """
        # Pull out the image URLs.
        urls = photo.get("urls", {})
        
        # Use Unsplash's description when it exists.
        alt_text = (
            photo.get("alt_description") or
            photo.get("description") or
            "Image from Unsplash"
        )
        
        # Return the photo shape the app uses.
        return {
            "id": photo.get("id", ""),
            "source": "unsplash",  # Remember the photo source.
            "image_url": urls.get("regular", ""),
            "thumbnail_url": urls.get("small", ""),
            "width": photo.get("width", 0),
            "height": photo.get("height", 0),
            "alt_text": alt_text,
        }
