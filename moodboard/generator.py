"""Core moodboard generation logic."""

from __future__ import annotations

import json
import re
import textwrap
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from moodboard.palettes import DEFAULT_PALETTE, MOOD_KEYWORDS, MOOD_PALETTES


@dataclass(frozen=True)
class MoodProfile:
    """A structured interpretation of a user's free-form mood prompt."""

    prompt: str
    dominant_mood: str
    keywords: list[str]
    palette: list[str]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation of the profile."""
        return {
            "prompt": self.prompt,
            "dominant_mood": self.dominant_mood,
            "keywords": self.keywords,
            "palette": self.palette,
        }


class MoodboardGenerator:
    """Create color-forward moodboards from short text prompts."""

    def __init__(self, output_dir: str | Path = "output") -> None:
        """Configure where generated image and metadata files should be saved."""
        self.output_dir = Path(output_dir)

    def analyze_prompt(self, prompt: str) -> MoodProfile:
        """Infer a dominant mood, supporting keywords, and palette from text."""
        words = re.findall(r"[a-zA-Z']+", prompt.lower())
        word_counts = Counter(words)

        mood_scores = {
            mood: sum(word_counts[word] for word in keywords)
            for mood, keywords in MOOD_KEYWORDS.items()
        }
        dominant_mood, score = max(mood_scores.items(), key=lambda item: item[1])

        if score == 0:
            dominant_mood = "custom"
            palette = DEFAULT_PALETTE
        else:
            palette = MOOD_PALETTES[dominant_mood]

        keywords = [word for word, _ in word_counts.most_common(8)]
        return MoodProfile(
            prompt=prompt,
            dominant_mood=dominant_mood,
            keywords=keywords,
            palette=palette,
        )

    def render(self, profile: MoodProfile, filename: str | None = None) -> Path:
        """Render a moodboard PNG and return the saved image path."""
        from PIL import Image, ImageDraw

        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = filename or f"{profile.dominant_mood}-{int(time.time())}.png"
        image_path = self.output_dir / filename

        board_width = 1200
        board_height = 800
        image = Image.new("RGB", (board_width, board_height), profile.palette[0])
        draw = ImageDraw.Draw(image)
        font_title = self._load_font(size=52)
        font_body = self._load_font(size=28)
        font_small = self._load_font(size=20)

        self._draw_palette(draw, profile.palette, board_width)
        self._draw_title(draw, profile, font_title, font_body)
        self._draw_keyword_tiles(draw, profile.keywords, profile.palette, font_small)

        image.save(image_path)
        return image_path

    def save_metadata(self, profile: MoodProfile, image_path: Path) -> Path:
        """Persist the generation details beside the rendered image."""
        metadata_path = image_path.with_suffix(".json")
        metadata = profile.to_dict() | {
            "image_path": str(image_path),
            "created_at_unix": int(time.time()),
        }
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return metadata_path

    def create(self, prompt: str) -> tuple[Path, Path, MoodProfile]:
        """Analyze a prompt, render a board, and save its metadata."""
        profile = self.analyze_prompt(prompt)
        image_path = self.render(profile)
        metadata_path = self.save_metadata(profile, image_path)
        return image_path, metadata_path, profile

    @staticmethod
    def _load_font(size: int) -> Any:
        """Load a common system font, falling back to Pillow's default font."""
        from PIL import ImageFont

        try:
            return ImageFont.truetype("Arial.ttf", size=size)
        except OSError:
            return ImageFont.load_default()

    @staticmethod
    def _draw_palette(draw: Any, palette: list[str], width: int) -> None:
        """Draw the large color-strip background."""
        stripe_width = width // len(palette)
        for index, color in enumerate(palette):
            x0 = index * stripe_width
            x1 = width if index == len(palette) - 1 else (index + 1) * stripe_width
            draw.rectangle((x0, 0, x1, 800), fill=color)

    @staticmethod
    def _draw_title(
        draw: Any,
        profile: MoodProfile,
        font_title: Any,
        font_body: Any,
    ) -> None:
        """Draw the main mood label and wrapped original prompt."""
        panel = (70, 90, 1130, 385)
        draw.rounded_rectangle(panel, radius=24, fill="#FFFFFF")
        draw.text((110, 130), profile.dominant_mood.title(), fill="#111111", font=font_title)

        wrapped_prompt = textwrap.fill(profile.prompt, width=58)
        draw.multiline_text(
            (110, 220),
            wrapped_prompt,
            fill="#333333",
            font=font_body,
            spacing=10,
        )

    @staticmethod
    def _draw_keyword_tiles(
        draw: Any,
        keywords: list[str],
        palette: list[str],
        font: Any,
    ) -> None:
        """Draw keyword chips to show how the prompt was interpreted."""
        if not keywords:
            keywords = ["mood", "board"]

        x = 95
        y = 470
        for index, keyword in enumerate(keywords[:8]):
            color = palette[index % len(palette)]
            tile = (x, y, x + 230, y + 95)
            draw.rounded_rectangle(tile, radius=18, fill="#FFFFFF")
            draw.rectangle((x, y, x + 18, y + 95), fill=color)
            draw.text((x + 36, y + 34), keyword.title(), fill="#111111", font=font)

            x += 270
            if x > 930:
                x = 95
                y += 130
