const API_BASE_URL = "http://127.0.0.1:8000";

const form = document.querySelector("#moodboard-form");
const promptInput = document.querySelector("#prompt");
const button = document.querySelector("#generate-button");
const statusText = document.querySelector("#status");
const emptyState = document.querySelector("#empty-state");
const result = document.querySelector("#result");
const image = document.querySelector("#moodboard-image");
const dominantMood = document.querySelector("#dominant-mood");
const palette = document.querySelector("#palette");
const keywords = document.querySelector("#keywords");

function setStatus(message) {
  statusText.textContent = message;
}

function renderPalette(colors) {
  palette.replaceChildren(
    ...colors.map((color) => {
      const swatch = document.createElement("span");
      swatch.className = "swatch";
      swatch.style.background = color;
      swatch.title = color;
      return swatch;
    }),
  );
}

function renderKeywords(words) {
  keywords.replaceChildren(
    ...words.map((word) => {
      const chip = document.createElement("span");
      chip.className = "keyword";
      chip.textContent = word;
      return chip;
    }),
  );
}

function showResult(data) {
  image.src = `${API_BASE_URL}${data.image_url}`;
  dominantMood.textContent = data.dominant_mood;
  renderPalette(data.palette);
  renderKeywords(data.keywords);
  emptyState.classList.add("hidden");
  result.classList.remove("hidden");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  button.disabled = true;
  setStatus("Generating...");

  try {
    const response = await fetch(`${API_BASE_URL}/api/moodboards`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: promptInput.value.trim() }),
    });

    if (!response.ok) {
      throw new Error("The backend could not generate a moodboard.");
    }

    const data = await response.json();
    showResult(data);
    setStatus("Done");
  } catch (error) {
    setStatus(error.message);
  } finally {
    button.disabled = false;
  }
});
