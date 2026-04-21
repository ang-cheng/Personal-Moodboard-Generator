"""
Data schemas module for the Personal Moodboard Generator backend.

This module defines data structures and schemas used throughout the application
for request/response validation and data transfer.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Color:
    """Represents a color with RGB values and hexadecimal representation."""
    
    r: int  # Red channel (0-255)
    g: int  # Green channel (0-255)
    b: int  # Blue channel (0-255)
    
    def to_hex(self) -> str:
        """Convert color to hexadecimal representation."""
        # Keep tiny values like 7 as "07".
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert color to dictionary."""
        # Include the numbers and the hex color.
        return {
            "r": self.r,
            "g": self.g,
            "b": self.b,
            "hex": self.to_hex(),
        }


@dataclass
class ImageFeatures:
    """Represents extracted features from an image."""
    
    image_url: str
    dominant_colors: List[Color] = field(default_factory=list)
    average_color: Optional[Color] = None
    brightness: float = 0.0  # 0.0 (dark) to 1.0 (bright)
    saturation: float = 0.0  # 0.0 (grayscale) to 1.0 (saturated)
    mood: Optional[str] = None  # e.g., "warm", "cool", "vibrant"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert image features to dictionary."""
        # Turn color objects into plain data.
        return {
            "image_url": self.image_url,
            "dominant_colors": [c.to_dict() for c in self.dominant_colors],
            "average_color": self.average_color.to_dict() if self.average_color else None,
            "brightness": self.brightness,
            "saturation": self.saturation,
            "mood": self.mood,
        }


@dataclass
class Moodboard:
    """Represents a generated moodboard."""
    
    id: str
    title: str
    description: Optional[str]
    colors: List[Color]
    images: List[str]  # URLs of images in the moodboard
    features: List[ImageFeatures] = field(default_factory=list)
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert moodboard to dictionary."""
        # Use names the frontend already knows.
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "colors": [c.to_dict() for c in self.colors],
            "images": self.images,
            "features": [f.to_dict() for f in self.features],
            "created_at": self.created_at,
        }


@dataclass
class GenerateMoodboardRequest:
    """Request schema for moodboard generation."""
    
    query: str  # Search query for images
    num_images: int = 5  # Number of images to fetch
    num_colors: int = 5  # Number of dominant colors to extract
    include_features: bool = True  # Whether to extract detailed features
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary."""
        # Some code wants a plain dictionary.
        return {
            "query": self.query,
            "num_images": self.num_images,
            "num_colors": self.num_colors,
            "include_features": self.include_features,
        }


@dataclass
class PreviewFeaturesRequest:
    """Request schema for feature preview."""
    
    image_url: str  # URL of the image to analyze
    extract_colors: bool = True
    extract_mood: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary."""
        # Keep the preview options together.
        return {
            "image_url": self.image_url,
            "extract_colors": self.extract_colors,
            "extract_mood": self.extract_mood,
        }
