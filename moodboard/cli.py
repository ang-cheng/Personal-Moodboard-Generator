"""Command-line interface for the moodboard generator."""

from __future__ import annotations

import argparse
from pathlib import Path

from rich.console import Console
from rich.table import Table

from moodboard.generator import MoodboardGenerator


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    # Keep the command line simple.
    parser = argparse.ArgumentParser(
        description="Generate a personalized moodboard image from a mood prompt."
    )
    parser.add_argument("prompt", help="A short description of the mood or vibe.")
    parser.add_argument(
        "-o",
        "--output-dir",
        default="output",
        help="Directory where the PNG and metadata JSON should be written.",
    )
    return parser


def main() -> None:
    """Run the command-line application."""
    args = build_parser().parse_args()
    # Treat the output folder like a path.
    generator = MoodboardGenerator(output_dir=Path(args.output_dir))
    image_path, metadata_path, profile = generator.create(args.prompt)

    console = Console()
    # Show a small summary when it finishes.
    table = Table(title="Moodboard Created")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Dominant mood", profile.dominant_mood)
    table.add_row("Keywords", ", ".join(profile.keywords) or "none")
    table.add_row("Palette", ", ".join(profile.palette))
    table.add_row("Image", str(image_path))
    table.add_row("Metadata", str(metadata_path))
    console.print(table)


if __name__ == "__main__":
    main()
