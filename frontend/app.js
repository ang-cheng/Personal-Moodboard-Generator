const API_BASE_URL = window.MOODBOARD_API_BASE_URL || "http://127.0.0.1:5001";
const DEFAULT_NUM_IMAGES = 24;
const DEFAULT_NUM_CLUSTERS = 3;
const FEATURE_MODE = "dominant_colors";

const state = {
  activeTab: "generate",
  currentPrompt: "",
  isLoading: false,
  error: "",
  moodboards: [],
  selectedMoodboardId: null,
  savedGalleryItems: [],
  processingTimeMs: null,
};

const form = document.querySelector("#moodboard-form");
const promptInput = document.querySelector("#prompt");
const button = document.querySelector("#generate-button");
const statusText = document.querySelector("#status");
const generateTab = document.querySelector("#generate-tab");
const galleryTab = document.querySelector("#gallery-tab");
const emptyState = document.querySelector("#empty-state");
const resultsSection = document.querySelector("#results-section");
const resultsMeta = document.querySelector("#results-meta");
const moodboardList = document.querySelector("#moodboard-list");
const gallerySection = document.querySelector("#gallery-section");
const galleryCount = document.querySelector("#gallery-count");
const savedGallery = document.querySelector("#saved-gallery");

function setState(updates) {
  Object.assign(state, updates);
  render();
}

function setStatus(message) {
  statusText.textContent = message;
}

async function generateMoodboards(userPrompt) {
  const response = await fetch(`${API_BASE_URL}/api/moodboards/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: userPrompt,
      num_images: DEFAULT_NUM_IMAGES,
      num_clusters: DEFAULT_NUM_CLUSTERS,
      feature_mode: FEATURE_MODE,
    }),
  });

  const payload = await response.json().catch(() => null);

  if (!response.ok || !payload?.ok) {
    const message =
      payload?.error?.message || "The backend could not generate moodboards.";
    throw new Error(message);
  }

  return payload;
}

function saveMoodboard(moodboardId) {
  const moodboard = state.moodboards.find((item) => item.id === moodboardId);
  if (!moodboard) return;

  const alreadySaved = state.savedGalleryItems.some((item) => item.id === moodboardId);
  if (alreadySaved) {
    setState({ selectedMoodboardId: moodboardId, activeTab: "gallery" });
    setStatus("Already saved");
    return;
  }

  const fallbackName = moodboard.title || "Saved Moodboard";
  const customName = window.prompt("Name this saved moodboard", fallbackName);
  const savedTitle = customName?.trim() || fallbackName;

  setState({
    activeTab: "gallery",
    selectedMoodboardId: moodboardId,
    savedGalleryItems: [
      ...state.savedGalleryItems,
      {
        ...moodboard,
        savedTitle,
        savedAt: new Date().toISOString(),
      },
    ],
  });
  setStatus("Saved to gallery");
}

function renameSavedMoodboard(moodboardId) {
  const moodboard = state.savedGalleryItems.find((item) => item.id === moodboardId);
  if (!moodboard) return;

  const currentName = moodboard.savedTitle || moodboard.title || "Saved Moodboard";
  const nextName = window.prompt("Rename this moodboard", currentName);
  if (nextName === null) return;

  const savedTitle = nextName.trim();
  if (!savedTitle) {
    setStatus("Name was not changed");
    return;
  }

  setState({
    savedGalleryItems: state.savedGalleryItems.map((item) =>
      item.id === moodboardId ? { ...item, savedTitle } : item,
    ),
    selectedMoodboardId: moodboardId,
  });
  setStatus("Renamed");
}

function unsaveMoodboard(moodboardId) {
  const moodboard = state.savedGalleryItems.find((item) => item.id === moodboardId);
  if (!moodboard) return;

  const title = moodboard.savedTitle || moodboard.title || "this moodboard";
  const shouldRemove = window.confirm(`Remove "${title}" from your gallery?`);
  if (!shouldRemove) return;

  setState({
    savedGalleryItems: state.savedGalleryItems.filter((item) => item.id !== moodboardId),
    selectedMoodboardId:
      state.selectedMoodboardId === moodboardId ? null : state.selectedMoodboardId,
  });
  setStatus("Removed from gallery");
}

function switchTab(activeTab) {
  setState({ activeTab });
}

function render() {
  button.disabled = state.isLoading;

  generateTab.classList.toggle("active", state.activeTab === "generate");
  galleryTab.classList.toggle("active", state.activeTab === "gallery");
  generateTab.setAttribute("aria-selected", String(state.activeTab === "generate"));
  galleryTab.setAttribute("aria-selected", String(state.activeTab === "gallery"));

  if (state.isLoading) {
    setStatus("Generating...");
  } else if (state.error) {
    setStatus(state.error);
  } else if (state.moodboards.length > 0) {
    setStatus("Done");
  }

  renderMoodboardResults();
  renderSavedGallery();
}

function renderMoodboardResults() {
  const hasMoodboards = state.moodboards.length > 0;
  const hasPrompt = state.currentPrompt.length > 0;
  const isGenerateTab = state.activeTab === "generate";

  emptyState.classList.toggle("hidden", !isGenerateTab || hasPrompt || state.isLoading);
  resultsSection.classList.toggle("hidden", !isGenerateTab || !hasPrompt);

  if (!hasPrompt) {
    moodboardList.replaceChildren();
    resultsMeta.textContent = "";
    return;
  }

  if (state.isLoading) {
    resultsMeta.textContent = `Generating options for "${state.currentPrompt}"...`;
    moodboardList.replaceChildren(createEmptyMessage("Working on your moodboards."));
    return;
  }

  if (!hasMoodboards) {
    resultsMeta.textContent = "No moodboards returned for this prompt.";
    moodboardList.replaceChildren(createEmptyMessage("No moodboards found."));
    return;
  }

  const timingText =
    state.processingTimeMs === null ? "" : ` in ${state.processingTimeMs} ms`;
  resultsMeta.textContent = `${state.moodboards.length} option${
    state.moodboards.length === 1 ? "" : "s"
  } for "${state.currentPrompt}"${timingText}`;

  moodboardList.replaceChildren(
    ...state.moodboards.map((moodboard) =>
      createMoodboardCard({
        moodboard,
        isSaved: state.savedGalleryItems.some((item) => item.id === moodboard.id),
        onSave: saveMoodboard,
      }),
    ),
  );
}

function renderSavedGallery() {
  const isGalleryTab = state.activeTab === "gallery";
  gallerySection.classList.toggle("hidden", !isGalleryTab);
  galleryCount.textContent = `${state.savedGalleryItems.length} saved`;

  if (!isGalleryTab) return;

  if (state.savedGalleryItems.length === 0) {
    savedGallery.replaceChildren(
      createEmptyMessage("Saved moodboards will appear here."),
    );
    return;
  }

  savedGallery.replaceChildren(
    ...state.savedGalleryItems.map((moodboard) =>
      createMoodboardCard({
        moodboard,
        isSaved: true,
        onSave: null,
        isCompact: true,
        onRename: renameSavedMoodboard,
        onUnsave: unsaveMoodboard,
      }),
    ),
  );
}

function createMoodboardCard({
  moodboard,
  isSaved,
  onSave,
  isCompact = false,
  onRename = null,
  onUnsave = null,
}) {
  const card = document.createElement("article");
  card.className = "moodboard-card";
  if (isCompact) {
    card.classList.add("gallery-card");
  }
  if (state.selectedMoodboardId === moodboard.id) {
    card.classList.add("selected");
  }

  const header = document.createElement("div");
  header.className = "card-header";

  const title = document.createElement("h3");
  title.textContent = moodboard.savedTitle || moodboard.title || "Moodboard";

  const actions = document.createElement("div");
  actions.className = "card-actions";

  if (onSave) {
    const saveButton = document.createElement("button");
    saveButton.type = "button";
    saveButton.className = "save-button";
    saveButton.textContent = isSaved ? "Saved" : "Save to Gallery";
    saveButton.disabled = isSaved;
    saveButton.addEventListener("click", () => onSave(moodboard.id));
    actions.append(saveButton);
  }

  if (onRename) {
    const renameButton = document.createElement("button");
    renameButton.type = "button";
    renameButton.className = "secondary-button";
    renameButton.textContent = "Rename";
    renameButton.addEventListener("click", () => onRename(moodboard.id));
    actions.append(renameButton);
  }

  if (onUnsave) {
    const unsaveButton = document.createElement("button");
    unsaveButton.type = "button";
    unsaveButton.className = "danger-button";
    unsaveButton.textContent = "Unsave";
    unsaveButton.addEventListener("click", () => onUnsave(moodboard.id));
    actions.append(unsaveButton);
  }

  header.append(title, actions);

  const palette = createPalette(moodboard.summary?.dominant_hex_colors || []);
  const imageGrid = createImageGrid(moodboard.images || [], isCompact);

  card.append(header, palette, imageGrid);
  return card;
}

function createPalette(colors) {
  const palette = document.createElement("div");
  palette.className = "palette";

  colors.forEach((color) => {
    const swatch = document.createElement("span");
    swatch.className = "swatch";
    swatch.style.background = color;
    swatch.title = color;
    palette.append(swatch);
  });

  return palette;
}

function createImageGrid(images, isCompact = false) {
  const grid = document.createElement("div");
  grid.className = "image-grid";
  if (isCompact) {
    grid.classList.add("compact-grid");
  }

  images.slice(0, isCompact ? 6 : 8).forEach((image) => {
    const img = document.createElement("img");
    img.src = image.thumbnail_url || image.image_url;
    img.alt = image.alt_text || "Moodboard image";
    img.loading = "lazy";
    grid.append(img);
  });

  if (images.length === 0) {
    grid.append(createEmptyMessage("No images in this moodboard."));
  }

  return grid;
}

function createEmptyMessage(message) {
  const element = document.createElement("p");
  element.className = "empty-message";
  element.textContent = message;
  return element;
}

generateTab.addEventListener("click", () => switchTab("generate"));
galleryTab.addEventListener("click", () => switchTab("gallery"));

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const userPrompt = promptInput.value.trim();
  if (!userPrompt) return;

  setState({
    activeTab: "generate",
    currentPrompt: userPrompt,
    isLoading: true,
    error: "",
    moodboards: [],
    selectedMoodboardId: null,
    processingTimeMs: null,
  });

  try {
    const payload = await generateMoodboards(userPrompt);

    setState({
      moodboards: payload.data?.moodboards || [],
      processingTimeMs: payload.meta?.processing_time_ms ?? null,
      isLoading: false,
    });
  } catch (error) {
    setState({
      error: error.message,
      moodboards: [],
      isLoading: false,
    });
  }
});

render();
