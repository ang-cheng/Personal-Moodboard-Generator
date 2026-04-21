const API_BASE_URL = window.MOODBOARD_API_BASE_URL || "http://127.0.0.1:5001";
const DEFAULT_NUM_IMAGES = 24;
const DEFAULT_NUM_CLUSTERS = 3;
const FEATURE_MODE = "dominant_colors";

// This is what the page is working with right now.
const state = {
  activeTab: "generate",
  currentBoardName: "",
  currentPrompt: "",
  isLoading: false,
  error: "",
  moodboards: [],
  selectedMoodboardId: null,
  editingMoodboardId: null,
  savedGalleryItems: [],
  processingTimeMs: null,
};

// Grab the page pieces we need.
const form = document.querySelector("#moodboard-form");
const composer = document.querySelector(".composer");
const boardNameInput = document.querySelector("#board-name");
const promptInput = document.querySelector("#prompt");
const button = document.querySelector("#generate-button");
const viewGalleryButton = document.querySelector("#view-gallery-button");
const createBoardButton = document.querySelector("#create-board-button");
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
  // Redraw the page after something changes.
  Object.assign(state, updates);
  render();
}

function createGalleryKey(moodboard, prompt = state.currentPrompt) {
  // Add the prompt so saved boards do not get mixed up.
  return `${prompt.trim().toLowerCase()}::${moodboard.id}`;
}

async function generateMoodboards(userPrompt) {
  // Ask for a few board options.
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

function saveMoodboard(galleryKey) {
  // Keep a copy of this board before a new prompt replaces it.
  const moodboard = state.moodboards.find((item) => createGalleryKey(item) === galleryKey);
  if (!moodboard) return;

  const alreadySaved = state.savedGalleryItems.some((item) => item.galleryKey === galleryKey);
  if (alreadySaved) {
    setState({ selectedMoodboardId: galleryKey, activeTab: "gallery" });
    return;
  }

  const fallbackName =
    moodboard.boardName || moodboard.title || state.currentBoardName || "Saved Moodboard";
  const customName = window.prompt("Name this saved moodboard", fallbackName);
  const savedTitle = customName?.trim() || fallbackName;

  setState({
    activeTab: "gallery",
    selectedMoodboardId: galleryKey,
    savedGalleryItems: [
      ...state.savedGalleryItems,
      {
        ...moodboard,
        galleryKey,
        sourcePrompt: state.currentPrompt,
        boardName: moodboard.boardName || state.currentBoardName,
        savedTitle,
        savedAt: new Date().toISOString(),
      },
    ],
  });
}

function renameSavedMoodboard(galleryKey) {
  setState({ editingMoodboardId: galleryKey, selectedMoodboardId: galleryKey });
}

function saveRenamedMoodboard(galleryKey, titleInput) {
  // Enter saves the new name, as long as it is not blank.
  const savedTitle = titleInput.value.trim();
  if (!savedTitle) return;

  setState({
    editingMoodboardId: null,
    savedGalleryItems: state.savedGalleryItems.map((item) =>
      item.galleryKey === galleryKey ? { ...item, savedTitle } : item,
    ),
    selectedMoodboardId: galleryKey,
  });
}

function cancelRenameMoodboard() {
  setState({ editingMoodboardId: null });
}

function unsaveMoodboard(galleryKey) {
  const moodboard = state.savedGalleryItems.find((item) => item.galleryKey === galleryKey);
  if (!moodboard) return;

  const title = moodboard.savedTitle || moodboard.title || "this moodboard";
  const shouldRemove = window.confirm(`Remove "${title}" from your gallery?`);
  if (!shouldRemove) return;

  setState({
    savedGalleryItems: state.savedGalleryItems.filter((item) => item.galleryKey !== galleryKey),
    editingMoodboardId:
      state.editingMoodboardId === galleryKey ? null : state.editingMoodboardId,
    selectedMoodboardId:
      state.selectedMoodboardId === galleryKey ? null : state.selectedMoodboardId,
  });
}

function switchTab(activeTab) {
  setState({ activeTab });
}

function render() {
  button.disabled = state.isLoading;

  // Mark the active tab for people using screen readers.
  generateTab.classList.toggle("active", state.activeTab === "generate");
  galleryTab.classList.toggle("active", state.activeTab === "gallery");
  generateTab.setAttribute("aria-selected", String(state.activeTab === "generate"));
  galleryTab.setAttribute("aria-selected", String(state.activeTab === "gallery"));
  composer.classList.toggle("hidden", state.activeTab === "gallery");

  renderMoodboardResults();
  renderSavedGallery();
}

function renderMoodboardResults() {
  // Decide what to show on the Generate tab.
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
        isSaved: state.savedGalleryItems.some(
          (item) => item.galleryKey === createGalleryKey(moodboard),
        ),
        onSave: saveMoodboard,
      }),
    ),
  );
}

function renderSavedGallery() {
  // For now, saved boards stay in this browser session.
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
  // New boards and saved boards use the same card.
  const card = document.createElement("article");
  card.className = "moodboard-card";
  const galleryKey = moodboard.galleryKey || createGalleryKey(moodboard);
  if (isCompact) {
    card.classList.add("gallery-card");
  }
  if (state.selectedMoodboardId === galleryKey) {
    card.classList.add("selected");
  }

  const header = document.createElement("div");
  header.className = "card-header";

  const currentTitle =
    moodboard.savedTitle || moodboard.boardName || moodboard.title || "Moodboard";
  const isEditing = state.editingMoodboardId === galleryKey;

  const titleArea = document.createElement("div");
  titleArea.className = "card-title-area";

  if (isEditing) {
    // Turn the title into a text box while renaming.
    const titleInput = document.createElement("input");
    titleInput.className = "rename-input";
    titleInput.value = currentTitle;
    titleInput.setAttribute("aria-label", "Moodboard name");

    titleInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        saveRenamedMoodboard(galleryKey, titleInput);
      }

      if (event.key === "Escape") {
        cancelRenameMoodboard();
      }
    });

    titleArea.append(titleInput);
    requestAnimationFrame(() => titleInput.focus());
  } else {
    const title = document.createElement("h3");
    title.textContent = currentTitle;
    titleArea.append(title);
  }

  const actions = document.createElement("div");
  actions.className = "card-actions";

  if (onSave) {
    const saveButton = document.createElement("button");
    saveButton.type = "button";
    saveButton.className = "save-button";
    saveButton.textContent = isSaved ? "Saved" : "Save to Gallery";
    saveButton.disabled = isSaved;
    saveButton.addEventListener("click", () => onSave(galleryKey));
    actions.append(saveButton);
  }

  if (onRename && !isEditing) {
    const renameButton = document.createElement("button");
    renameButton.type = "button";
    renameButton.className = "secondary-button";
    renameButton.textContent = "Rename";
    renameButton.addEventListener("click", () => onRename(galleryKey));
    actions.append(renameButton);
  }

  if (onUnsave) {
    const unsaveButton = document.createElement("button");
    unsaveButton.type = "button";
    unsaveButton.className = "danger-button";
    unsaveButton.textContent = "Unsave";
    unsaveButton.addEventListener("click", () => onUnsave(galleryKey));
    actions.append(unsaveButton);
  }

  header.append(titleArea, actions);

  const palette = createPalette(moodboard.summary?.dominant_hex_colors || []);
  const imageGrid = createImageGrid(moodboard.images || [], isCompact);

  card.append(header, palette, imageGrid);
  return card;
}

function createPalette(colors) {
  // Show the board colors as small squares.
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
  // Show six images so every card keeps the same shape.
  const grid = document.createElement("div");
  grid.className = "image-grid";
  if (isCompact) {
    grid.classList.add("compact-grid");
  }

  images.slice(0, 6).forEach((image) => {
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
viewGalleryButton.addEventListener("click", () => switchTab("gallery"));
createBoardButton.addEventListener("click", () => switchTab("generate"));

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  // The board name is just a label; the prompt finds the images.
  const userPrompt = promptInput.value.trim();
  const boardName = boardNameInput.value.trim();
  if (!userPrompt) return;

  setState({
    activeTab: "generate",
    currentBoardName: boardName,
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
      moodboards: (payload.data?.moodboards || []).map((moodboard) => ({
        ...moodboard,
        boardName,
      })),
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
