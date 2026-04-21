"""Legacy FastAPI backend for generating and serving moodboards."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from moodboard.generator import MoodboardGenerator

# Older generated PNGs and JSON files live here.
OUTPUT_DIR = Path("output")

app = FastAPI(title="Personal Moodboard Generator API")
app.add_middleware(
    CORSMiddleware,
    # Let the older local frontend URLs work.
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
# Serve generated files so the browser can display them.
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")


class MoodboardRequest(BaseModel):
    """Incoming request body for a new moodboard."""

    prompt: str = Field(min_length=3, max_length=280)


class MoodboardResponse(BaseModel):
    """API response describing the generated moodboard."""

    dominant_mood: str
    keywords: list[str]
    palette: list[str]
    image_url: str
    metadata_url: str


@app.get("/api/health")
def health_check() -> dict[str, str]:
    """Return a small readiness response for the frontend."""
    return {"status": "ok"}


@app.post("/api/moodboards", response_model=MoodboardResponse)
def create_moodboard(request: MoodboardRequest) -> MoodboardResponse:
    """Generate a moodboard image and return URLs the frontend can display."""
    # This route uses the older PNG renderer.
    generator = MoodboardGenerator(output_dir=OUTPUT_DIR)
    image_path, metadata_path, profile = generator.create(request.prompt)

    return MoodboardResponse(
        dominant_mood=profile.dominant_mood,
        keywords=profile.keywords,
        palette=profile.palette,
        image_url=f"/output/{image_path.name}",
        metadata_url=f"/output/{metadata_path.name}",
    )
