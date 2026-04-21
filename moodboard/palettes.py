"""Mood keyword palettes used by the generator."""

# Hand-picked colors for each mood.
MOOD_PALETTES = {
    "calm": ["#D8E2DC", "#FFE5D9", "#FFCAD4", "#F4ACB7", "#9D8189"],
    "cozy": ["#F4E1C1", "#DDB892", "#B08968", "#7F5539", "#9C6644"],
    "energetic": ["#FFB703", "#FB8500", "#EF476F", "#06D6A0", "#118AB2"],
    "focus": ["#0B132B", "#1C2541", "#3A506B", "#5BC0BE", "#F5F5F5"],
    "dreamy": ["#CDB4DB", "#FFC8DD", "#FFAFCC", "#BDE0FE", "#A2D2FF"],
    "earthy": ["#606C38", "#283618", "#FEFAE0", "#DDA15E", "#BC6C25"],
    "bold": ["#111111", "#F72585", "#7209B7", "#3A0CA3", "#4CC9F0"],
}

# Use this when no mood matches.
DEFAULT_PALETTE = ["#2B2D42", "#8D99AE", "#EDF2F4", "#EF233C", "#D90429"]

# Keep these short and easy to read.
MOOD_KEYWORDS = {
    "calm": {"calm", "peaceful", "soft", "quiet", "gentle", "serene"},
    "cozy": {"cozy", "warm", "home", "comfort", "autumn", "snug"},
    "energetic": {"energetic", "excited", "bright", "dance", "active", "sunny"},
    "focus": {"focus", "study", "minimal", "clear", "work", "productive"},
    "dreamy": {"dreamy", "romantic", "pastel", "cloud", "ethereal", "whimsical"},
    "earthy": {"earthy", "forest", "natural", "grounded", "organic", "botanical"},
    "bold": {"bold", "dramatic", "neon", "edgy", "confident", "electric"},
}
