const importanceLabels = {
  1: "Irrelevante",
  2: "Opcional",
  3: "Importante",
  4: "Fundamental",
};

function renderStateBadge(isRelevant) {
  if (isRelevant) {
    return '<span class="inline-block rounded-full bg-guios-good px-3 py-1 text-xs font-medium text-guios-text">Relevante</span>';
  }
  return '<span class="inline-block rounded-full bg-guios-bad px-3 py-1 text-xs font-medium text-guios-text">No relevante</span>';
}

function normalizeText(value) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function applyFactorFilters() {
  const searchInput = document.getElementById("factor-search");
  const dimensionFilter = document.getElementById("dimension-filter");
  const stateFilter = document.getElementById("state-filter");
  const visibleCount = document.getElementById("visible-factor-count");

  if (!searchInput || !dimensionFilter || !stateFilter || !visibleCount) {
    return;
  }

  const searchText = normalizeText(searchInput.value.trim());
  const selectedDimension = dimensionFilter.value;
  const selectedState = stateFilter.value;
  let count = 0;

  document.querySelectorAll("[data-factor-row]").forEach((row) => {
    const factorName = normalizeText(row.dataset.factorName || "");
    const dimension = row.dataset.dimension || "";
    const searchableText = `${factorName} ${normalizeText(dimension)}`;
    const matchesSearch = !searchText || searchableText.includes(searchText);
    const matchesDimension = !selectedDimension || dimension === selectedDimension;
    const matchesState = !selectedState || row.dataset.state === selectedState;
    const isVisible = matchesSearch && matchesDimension && matchesState;

    row.classList.toggle("hidden", !isVisible);

    if (isVisible) {
      count += 1;
    }
  });

  visibleCount.textContent = count;
}

function updateRelativeImportance(select) {
  const row = select.closest("[data-factor-row]");
  const relativeCell = row.querySelector("[data-relative-cell]");
  const stateCell = row.querySelector("[data-state-cell]");
  const suggested = Number(row.dataset.suggested);
  const decision = Number(select.value);

  if (!decision) {
    relativeCell.textContent = "-";
    stateCell.innerHTML = renderStateBadge(false);
    row.dataset.state = "no-relevante";
    applyFactorFilters();
    return;
  }

  const suggestedIndex = suggested - 1;
  const decisionIndex = decision - 1;
  const relative = Math.floor((suggestedIndex + decisionIndex) / 2) + 1;

  relativeCell.textContent = importanceLabels[relative];
  stateCell.innerHTML = renderStateBadge(relative > 1);
  row.dataset.state = relative > 1 ? "relevante" : "no-relevante";
  applyFactorFilters();
}

document.querySelectorAll("[data-decision-select]").forEach((select) => {
  select.addEventListener("change", () => updateRelativeImportance(select));
});

document.getElementById("factor-search")?.addEventListener("input", applyFactorFilters);
document.getElementById("dimension-filter")?.addEventListener("change", applyFactorFilters);
document.getElementById("state-filter")?.addEventListener("change", applyFactorFilters);
