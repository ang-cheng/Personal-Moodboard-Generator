# Personal Moodboard Generator

The Personal Moodboard Generator is a Python-based web application that turns a
short mood prompt into several possible visual moodboards. A user enters a query
such as "quiet coastal morning" or "bold neon city night," and the app searches
for real images, extracts visual color features, clusters the images into
distinct aesthetic directions, and displays multiple moodboard options in the
browser.

This project combines machine learning and web development. The backend uses
Flask, OpenCV, NumPy, and scikit-learn to retrieve and analyze images. The
frontend provides a lightweight Pinterest-inspired interface where users can
compare generated moodboards and save selected boards to a gallery.

## Project Overview

The goal of this project is to make visual brainstorming easier. Instead of
manually searching for many reference images and grouping them by style, users
can describe a feeling or theme and receive several curated moodboard options.

The full pipeline is:

1. The user enters a prompt in the frontend.
2. The frontend sends the prompt to the Flask backend.
3. The backend searches Unsplash for matching image metadata.
4. The backend downloads valid image URLs.
5. OpenCV decodes each image into an image array.
6. The feature extractor resizes images, converts BGR to RGB, and extracts
   dominant colors.
7. scikit-learn KMeans clusters images by their color feature vectors.
8. The backend returns multiple moodboards, one for each cluster.
9. The frontend displays all returned moodboard options.
10. The user saves one or more moodboards to the gallery.

## Features

- Prompt-based moodboard generation from a natural-language query.
- Multiple moodboard options returned from one prompt.
- Color-based image clustering using KMeans.
- Image loading and processing with OpenCV.
- Dominant color feature extraction with NumPy and scikit-learn.
- Save-to-gallery functionality on the frontend.
- Clean, lightweight UI inspired by Pinterest-style visual browsing.
- Consistent JSON API responses for success and error cases.
- Graceful handling of broken or invalid images.

## System Architecture

The project is separated into two main parts:

- Backend: Flask API and machine-learning/image-processing pipeline.
- Frontend: Static HTML, CSS, and JavaScript UI for user interaction.

The frontend communicates with the backend using HTTP requests. When the user
submits a prompt, the browser sends a JSON request to:

```text
POST /api/moodboards/generate
```

The backend returns JSON containing an array of moodboard options. The frontend
then renders each moodboard as a card with images and color swatches.

High-level data flow:

```text
Prompt
  -> Flask route
  -> Unsplash image search
  -> image download and OpenCV decode
  -> dominant color feature extraction
  -> KMeans clustering
  -> JSON moodboard response
  -> frontend moodboard grid
  -> saved gallery
```

## Backend Structure

The Flask backend lives in the `backend/` directory.

```text
backend/
  app.py
  config.py
  routes/
    health.py
    moodboards.py
  services/
    unsplash_client.py
    image_loader.py
    feature_extractor.py
    clusterer.py
    moodboard_generator.py
  models/
    schemas.py
  utils/
    errors.py
    response.py
    validators.py
```

### `backend/app.py`

Creates and configures the Flask application. It registers the API blueprints,
adds lightweight CORS headers for local frontend development, and sets up global
JSON error handlers.

### `backend/config.py`

Loads environment variables with `python-dotenv` and stores configuration values
such as the Unsplash API key, server port, and image-processing settings.

### `backend/routes/`

Contains Flask Blueprint route handlers.

- `health.py`: exposes `GET /api/health`.
- `moodboards.py`: exposes the moodboard generation and feature preview routes.

Routes are responsible for:

- parsing JSON request bodies
- validating user input
- calling the service layer
- returning consistent JSON responses

### `backend/services/`

Contains the main backend business logic.

- `unsplash_client.py`: calls the Unsplash API and normalizes image metadata.
- `image_loader.py`: downloads image bytes with `requests`, converts them into
  NumPy arrays, and decodes them with OpenCV.
- `feature_extractor.py`: extracts dominant RGB colors from OpenCV images using
  KMeans.
- `clusterer.py`: clusters image feature vectors into moodboard groups.
- `moodboard_generator.py`: orchestrates the full workflow from query to final
  moodboard response.

### `MoodboardGenerator`

`MoodboardGenerator` is the main backend coordinator class. It receives service
dependencies in its constructor:

- `unsplash_client`
- `image_loader`
- `feature_extractor`
- `clusterer`

Its two main methods are:

- `preview_features(query, num_images, feature_mode)`
- `generate_moodboards(query, num_images, num_clusters, feature_mode)`

This class keeps the route layer clean by combining the search, image loading,
feature extraction, and clustering steps in one readable workflow.

### `backend/models/`

Contains simple data schemas used by parts of the application. Earlier versions
of the project used dataclasses for color and moodboard metadata; the current
API primarily returns plain JSON-ready dictionaries.

### `backend/utils/`

Shared backend utilities.

- `errors.py`: custom exceptions such as `ValidationError`,
  `UpstreamAPIError`, `ImageProcessingError`, and `ClusteringError`.
- `response.py`: helpers for consistent success and error JSON responses.
- `validators.py`: request validation helpers for query, image count, cluster
  count, and feature mode.

## Frontend Structure

The frontend lives in the `frontend/` directory and is intentionally lightweight.

```text
frontend/
  index.html
  styles.css
  app.js
```

### `frontend/index.html`

Defines the main page structure:

- prompt input form
- generated moodboard results section
- saved gallery section

### `frontend/styles.css`

Styles the app layout, prompt panel, moodboard cards, image grids, color
swatches, loading/empty states, and saved gallery.

### `frontend/app.js`

Handles frontend state and API communication.

Frontend state includes:

- `currentPrompt`: the latest prompt submitted by the user
- `isLoading`: whether a request is currently running
- `error`: the current error message, if any
- `moodboards`: the array of moodboard options returned by the backend
- `selectedMoodboardId`: the most recently saved/selected moodboard
- `savedGalleryItems`: moodboards the user saved during the session
- `processingTimeMs`: backend processing time for the generation request

The UI is organized around these logical components:

- Prompt form
- Moodboard list/grid
- Moodboard card
- Saved gallery

## API Documentation

All backend responses use JSON. Successful responses use:

```json
{
  "ok": true,
  "data": {}
}
```

Error responses use:

```json
{
  "ok": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
}
```

### `GET /api/health`

Checks whether the backend is running.

Example response:

```json
{
  "ok": true,
  "data": {
    "status": "healthy"
  }
}
```

### `POST /api/moodboards/generate`

Generates multiple moodboards from a query.

Example request:

```json
{
  "query": "calm quiet morning with gentle light",
  "num_images": 24,
  "num_clusters": 3,
  "feature_mode": "dominant_colors"
}
```

Example response:

```json
{
  "ok": true,
  "data": {
    "query": "calm quiet morning with gentle light",
    "num_clusters": 3,
    "moodboards": [
      {
        "id": "cluster_0",
        "title": "Moodboard 1",
        "summary": {
          "dominant_hex_colors": ["#3B2F2F", "#D9C7A3", "#8B6F47"]
        },
        "images": [
          {
            "id": "img_1",
            "image_url": "https://example.com/image.jpg",
            "thumbnail_url": "https://example.com/thumb.jpg",
            "alt_text": "A calm morning landscape",
            "cluster_id": "cluster_0"
          }
        ]
      }
    ]
  },
  "meta": {
    "processing_time_ms": 1234
  }
}
```

The important part is that `moodboards` is an array. The frontend does not
assume there is only one result. It maps over the array and renders every
candidate moodboard returned by the backend.

If no valid moodboards can be generated, the backend still returns a valid
success shape with an empty list:

```json
{
  "ok": true,
  "data": {
    "query": "example query",
    "num_clusters": 0,
    "moodboards": []
  },
  "meta": {
    "processing_time_ms": 250
  }
}
```

### `POST /api/moodboards/preview-features`

Previews extracted image features without clustering them into moodboards.

Example request:

```json
{
  "query": "warm desert sunset",
  "num_images": 12,
  "feature_mode": "dominant_colors"
}
```

Example response:

```json
{
  "ok": true,
  "data": {
    "query": "warm desert sunset",
    "images": [
      {
        "id": "abc123",
        "image_url": "https://example.com/image.jpg",
        "metadata": {
          "source": "unsplash",
          "alt_text": "A desert at sunset"
        },
        "feature_vector": [0.84, 0.62, 0.38, 0.21, 0.14, 0.11],
        "dominant_hex_colors": ["#D69E61", "#36241C"]
      }
    ]
  }
}
```

## Installation Instructions

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd Personal-Moodboard-Generator
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

The root `requirements.txt` belongs to an earlier CLI/FastAPI version of the
project. For the current Flask moodboard web app, use `backend/requirements.txt`.

### 4. Create the environment file

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and add your Unsplash access key:

```text
UNSPLASH_ACCESS_KEY=your_actual_unsplash_access_key
```

You can get an Unsplash API key from:

```text
https://unsplash.com/oauth/applications
```

### 5. Run the backend server

From the project root:

```bash
source .venv/bin/activate
PYTHONPATH=backend python3 backend/app.py
```

By default, the Flask backend runs at:

```text
http://127.0.0.1:5000
```

### 6. Run the frontend

Open a second terminal from the project root:

```bash
python3 -m http.server 8001 --directory frontend
```

Open the frontend in your browser:

```text
http://127.0.0.1:8001
```

The frontend defaults to calling:

```text
http://127.0.0.1:5000
```

If needed, you can override the backend URL before loading `app.js` by defining
`window.MOODBOARD_API_BASE_URL`.

## Usage Instructions

1. Start the Flask backend.
2. Start the static frontend server.
3. Open the frontend in a browser.
4. Enter a mood prompt, such as:

   ```text
   dreamy botanical study room
   ```

5. Click **Generate**.
6. View the returned moodboard options.
7. Compare their image grids and dominant color swatches.
8. Click **Save to Gallery** on any moodboard you want to keep.
9. Saved moodboards appear in the gallery section below the generated results.

If no images are found or no images can be processed, the app should return a
valid response with no moodboards. The frontend displays an empty state instead
of crashing.

## Packages Used

### First-party Python packages

- `json`: ensures API payloads are JSON-safe.
- `time`: measures backend processing time.
- `collections`: counts dominant colors and summary values.
- `os`: reads environment variables in configuration.
- `typing`: documents expected data shapes in service code.

### Third-party Python packages

- `Flask`: web framework for API routes.
- `requests`: sends HTTP requests to Unsplash and image URLs.
- `python-dotenv`: loads local environment variables from `.env`.
- `numpy`: represents images and feature vectors as numeric arrays.
- `opencv-python`: decodes downloaded images and performs color conversion.
- `scikit-learn`: runs KMeans for dominant color extraction and clustering.

## Challenges and Design Decisions

### Image URLs vs. downloaded image data

Unsplash returns image URLs, but clustering requires pixel data. The backend
therefore downloads each image, converts the bytes into a NumPy buffer, and uses
OpenCV to decode the image. Broken or invalid image URLs are skipped so one bad
image does not fail the whole request.

### Feature extraction choices

The current feature mode is `dominant_colors`. Each image is resized for speed,
converted from OpenCV's BGR format to RGB, flattened into pixels, and analyzed
with KMeans. The resulting dominant colors become both:

- a numeric `feature_vector` for clustering
- human-readable `dominant_hex_colors` for the UI

### Clustering design

KMeans is used because it is understandable, deterministic with `random_state`,
and appropriate for grouping numeric feature vectors. The backend automatically
reduces the number of clusters if there are fewer valid images than requested.

### Consistent API responses

The backend uses helper functions and custom exceptions so every route returns
predictable JSON. This makes frontend error handling much simpler because the
browser can always look for either `ok: true` or `ok: false`.

### Moving from one moodboard to many

The frontend originally assumed one prompt produced one moodboard. The current
version treats the backend response as an array of options. State management now
tracks multiple returned moodboards, a selected moodboard id, and a saved gallery
array.

## Future Improvements

- Use deep learning embeddings for richer visual similarity.
- Add text embeddings so prompt meaning can influence clustering more directly.
- Store saved galleries in a backend database.
- Add user accounts and persistent saved moodboards.
- Let users choose the number of clusters from the UI.
- Add drag-and-drop editing for moodboard layouts.
- Improve accessibility for keyboard navigation and screen readers.
- Add automated tests for Flask routes and frontend rendering.

## Project Requirements Checklist

This project satisfies the CIS 1902 final project requirements:

- At least one class definition:
  - `MoodboardGenerator`
  - `ImageLoader`
  - `FeatureExtractor`
  - `Clusterer`
  - `UnsplashClient`
- First-party packages:
  - uses packages such as `json`, `time`, `collections`, `os`, and `typing`
- Third-party packages:
  - uses Flask, requests, python-dotenv, NumPy, OpenCV, and scikit-learn
- Well-documented code:
  - backend modules include docstrings
  - classes and public methods include explanations
  - comments explain non-obvious image-processing and clustering steps
- README:
  - includes project overview
  - explains architecture and data flow
  - documents API endpoints
  - provides installation and usage instructions
  - discusses packages, challenges, and future improvements

## Code Quality Notes

- The backend is separated into routes, services, models, and utilities.
- The route layer stays focused on HTTP concerns.
- The service layer handles external APIs, image processing, feature extraction,
  and clustering.
- The frontend is intentionally small and beginner-friendly.
- API responses are normalized so frontend code does not need many special cases.
- Invalid images are skipped during batch processing to keep the app resilient.

## Testing and Verification

Useful checks during development:

```bash
python3 -m compileall backend
```

If dependencies are installed, you can also run the Flask app and test:

```bash
curl http://127.0.0.1:5000/api/health
```

For the older CLI tests still present in the repository:

```bash
pytest
```
