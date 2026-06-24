(() => {
  const searchInput = document.getElementById("factor-history-search");
  const dimensionFilter = document.getElementById("factor-history-dimension-filter");
  const fodaFilter = document.getElementById("factor-history-foda-filter");
  const rows = Array.from(document.querySelectorAll("[data-factor-history-row]"));
  const visibleCount = document.getElementById("visible-factor-history-count");
  const emptyState = document.getElementById("factor-history-empty-state");

  if (!searchInput || !dimensionFilter || !fodaFilter) {
    return;
  }

  const normalize = (value) => (value || "")
    .toString()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();

  const applyFilters = () => {
    const query = normalize(searchInput.value);
    const dimension = dimensionFilter.value;
    const foda = fodaFilter.value;
    let visible = 0;

    rows.forEach((row) => {
      const textMatch = !query
        || normalize(row.dataset.factorName).includes(query)
        || normalize(row.dataset.dimension).includes(query)
        || normalize(row.dataset.foda).includes(query);
      const dimensionMatch = !dimension || row.dataset.dimension === dimension;
      const fodaMatch = !foda || row.dataset.foda === foda;
      const show = textMatch && dimensionMatch && fodaMatch;

      row.classList.toggle("hidden", !show);
      if (show) {
        visible += 1;
      }
    });

    if (visibleCount) {
      visibleCount.textContent = visible;
    }
    if (emptyState) {
      emptyState.classList.toggle("hidden", visible > 0);
    }
  };

  searchInput.addEventListener("input", applyFilters);
  dimensionFilter.addEventListener("change", applyFilters);
  fodaFilter.addEventListener("change", applyFilters);
})();
