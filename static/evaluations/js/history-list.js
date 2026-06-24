(() => {
  const searchInput = document.getElementById("history-search");
  const contextFilter = document.getElementById("history-context-filter");
  const rows = Array.from(document.querySelectorAll("[data-history-row]"));
  const visibleCount = document.getElementById("visible-history-count");
  const emptyState = document.getElementById("history-empty-state");
  const pagination = document.getElementById("history-pagination");
  const pageList = document.getElementById("history-page-list");
  const firstButton = document.getElementById("history-first-page");
  const prevButton = document.getElementById("history-prev-page");
  const nextButton = document.getElementById("history-next-page");
  const lastButton = document.getElementById("history-last-page");
  const pageSize = 6;
  let currentPage = 1;

  if (!searchInput || !contextFilter || !firstButton || !prevButton || !nextButton || !lastButton || !pageList) {
    return;
  }

  const normalize = (value) => (value || "")
    .toString()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();

  const filteredRows = () => {
    const query = normalize(searchInput.value);
    const context = contextFilter.value;

    return rows.filter((row) => {
      const textMatch = !query
        || normalize(row.dataset.software).includes(query)
        || normalize(row.dataset.context).includes(query);
      const contextMatch = !context || row.dataset.context === context.toLowerCase();
      return textMatch && contextMatch;
    });
  };

  const pageNumbers = (totalPages) => {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, index) => index + 1);
    }

    const pages = new Set([1, totalPages, currentPage, currentPage - 1, currentPage + 1]);
    if (currentPage <= 4) {
      pages.add(2);
      pages.add(3);
      pages.add(4);
      pages.add(5);
    }
    if (currentPage >= totalPages - 3) {
      pages.add(totalPages - 1);
      pages.add(totalPages - 2);
      pages.add(totalPages - 3);
      pages.add(totalPages - 4);
    }

    const sortedPages = Array.from(pages)
      .filter((page) => page >= 1 && page <= totalPages)
      .sort((a, b) => a - b);
    const result = [];

    sortedPages.forEach((page, index) => {
      if (index > 0 && page - sortedPages[index - 1] > 1) {
        result.push("...");
      }
      result.push(page);
    });

    return result;
  };

  const applyFilters = () => {
    const matches = filteredRows();
    const totalPages = Math.max(1, Math.ceil(matches.length / pageSize));
    currentPage = Math.min(currentPage, totalPages);
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    const pageRows = new Set(matches.slice(start, end));

    rows.forEach((row) => {
      row.classList.toggle("hidden", !pageRows.has(row));
    });

    if (visibleCount) {
      visibleCount.textContent = matches.length;
    }
    if (emptyState) {
      emptyState.classList.toggle("hidden", matches.length > 0);
    }
    if (pagination) {
      pagination.classList.toggle("hidden", matches.length === 0 || totalPages <= 1);
    }

    pageList.innerHTML = "";
    pageNumbers(totalPages).forEach((page) => {
      if (page === "...") {
        const ellipsis = document.createElement("span");
        ellipsis.className = "flex h-8 min-w-8 items-center justify-center px-1 text-guios-orange";
        ellipsis.textContent = "...";
        pageList.appendChild(ellipsis);
        return;
      }

      const button = document.createElement("button");
      button.className = page === currentPage
        ? "flex h-8 min-w-8 items-center justify-center rounded-md bg-guios-orange px-2 font-semibold text-white"
        : "flex h-8 min-w-8 items-center justify-center rounded-md px-2 text-guios-navy hover:bg-guios-orange hover:text-white";
      button.type = "button";
      button.textContent = page;
      button.setAttribute("aria-label", `Ir a pagina ${page}`);
      button.addEventListener("click", () => {
        currentPage = page;
        applyFilters();
      });
      pageList.appendChild(button);
    });

    firstButton.disabled = currentPage <= 1;
    prevButton.disabled = currentPage <= 1;
    nextButton.disabled = currentPage >= totalPages;
    lastButton.disabled = currentPage >= totalPages;
  };

  searchInput.addEventListener("input", () => {
    currentPage = 1;
    applyFilters();
  });
  contextFilter.addEventListener("change", () => {
    currentPage = 1;
    applyFilters();
  });
  prevButton.addEventListener("click", () => {
    currentPage = Math.max(1, currentPage - 1);
    applyFilters();
  });
  nextButton.addEventListener("click", () => {
    currentPage += 1;
    applyFilters();
  });
  firstButton.addEventListener("click", () => {
    currentPage = 1;
    applyFilters();
  });
  lastButton.addEventListener("click", () => {
    currentPage = Math.max(1, Math.ceil(filteredRows().length / pageSize));
    applyFilters();
  });
  applyFilters();
})();
