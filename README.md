# Personal Moodboard Generator

Personal Moodboard Generator is a small web app and Python CLI that turns a free-form mood prompt into a visual moodboard. It analyzes the prompt, chooses a matching color palette, renders a PNG with Pillow, and saves a JSON metadata file with the interpreted mood.

## Course Requirement Checklist

- At least one class definition: `MoodProfile` and `MoodboardGenerator` in `moodboard/generator.py`.
- First-party packages: uses `argparse`, `collections`, `dataclasses`, `json`, `pathlib`, `re`, `textwrap`, and `time`.
- Third-party packages: uses `FastAPI` and `uvicorn` for the backend, `Pillow` for image rendering, and `rich` for CLI output.
- Documented code: modules, classes, and public functions include docstrings, with inline comments avoided unless the code genuinely needs them.
- README: this file includes installation, usage, and code structure notes.

## Installation

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Install the package in editable mode:

   ```bash
   pip install -e .
   ```

## Start The Backend And Frontend

Open two terminal windows from the project root.

Terminal 1 starts the backend API:

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

The backend runs at:

```text
http://127.0.0.1:8000
```

Terminal 2 starts the frontend:

```bash
python3 -m http.server 8001 --directory frontend
```

Open the frontend in your browser:

```text
http://127.0.0.1:8001
```

The frontend sends prompts to `POST /api/moodboards`, then displays the generated image served from the backend's `/output` route.

## CLI Usage

Generate a moodboard from a prompt:

```bash
moodboard "calm quiet morning with gentle light" --output-dir output
```

The app writes two files:

- `output/<mood>-<timestamp>.png`: the rendered moodboard image.
- `output/<mood>-<timestamp>.json`: metadata describing the prompt, detected mood, keywords, palette, and creation time.

You can also run the CLI as a module:

```bash
python -m moodboard.cli "bold neon confident studio"
```

## Project Structure

```text
moodboard/
  __init__.py       Package exports.
  cli.py            Command-line interface using argparse and rich.
  generator.py      Mood analysis, image rendering, and metadata saving.
  palettes.py       Mood keyword dictionaries and color palettes.
backend/
  main.py           FastAPI backend exposing moodboard generation endpoints.
frontend/
  index.html        Browser UI.
  app.js            Frontend API calls and rendering.
  styles.css        Frontend layout and styling.
tests/
  test_generator.py Unit tests for prompt analysis and metadata output.
```

## How The Code Works

`MoodboardGenerator.analyze_prompt()` tokenizes the user's prompt and counts words with `collections.Counter`. It compares the words against mood keyword sets in `moodboard/palettes.py`, chooses the highest-scoring mood, and returns a `MoodProfile` object.

`MoodboardGenerator.render()` uses Pillow to create a color-strip background, draw the detected mood, wrap the original prompt, and add keyword tiles. `save_metadata()` writes a JSON sidecar file so each generated image can be traced back to its inputs.

## Tests

Run the test suite with:

```bash
pytest
```
