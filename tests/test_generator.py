from moodboard.generator import MoodboardGenerator
from moodboard.palettes import DEFAULT_PALETTE, MOOD_PALETTES


def test_analyze_prompt_detects_known_mood() -> None:
    generator = MoodboardGenerator()

    profile = generator.analyze_prompt("A calm quiet morning with gentle light")

    assert profile.dominant_mood == "calm"
    assert profile.palette == MOOD_PALETTES["calm"]
    assert "calm" in profile.keywords


def test_analyze_prompt_uses_default_palette_for_custom_prompt() -> None:
    generator = MoodboardGenerator()

    profile = generator.analyze_prompt("museum marble espresso deadline")

    assert profile.dominant_mood == "custom"
    assert profile.palette == DEFAULT_PALETTE


def test_save_metadata_writes_profile_json(tmp_path) -> None:
    generator = MoodboardGenerator(output_dir=tmp_path)
    profile = generator.analyze_prompt("bold neon confident studio")
    image_path = tmp_path / "board.png"

    metadata_path = generator.save_metadata(profile, image_path)

    assert metadata_path.exists()
    assert '"dominant_mood": "bold"' in metadata_path.read_text(encoding="utf-8")
