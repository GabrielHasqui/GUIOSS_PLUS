(() => {
  const searchInput = document.getElementById("admin-user-search");
  const roleFilter = document.getElementById("admin-user-role-filter");
  const statusFilter = document.getElementById("admin-user-status-filter");
  const rows = Array.from(document.querySelectorAll("[data-admin-user-row]"));
  const emptyState = document.getElementById("admin-users-empty-state");
  const pagination = document.getElementById("admin-users-pagination");
  const pageList = document.getElementById("admin-users-page-list");
  const firstButton = document.getElementById("admin-users-first-page");
  const prevButton = document.getElementById("admin-users-prev-page");
  const nextButton = document.getElementById("admin-users-next-page");
  const lastButton = document.getElementById("admin-users-last-page");
  const pageSize = 6;
  let currentPage = 1;

  const editModal = document.getElementById("edit-user-modal");
  const editSubtitle = document.getElementById("edit-user-modal-subtitle");
  const editUserId = document.getElementById("edit-user-id");
  const editFirstName = document.getElementById("edit-first-name");
  const editLastName = document.getElementById("edit-last-name");
  const editEmail = document.getElementById("edit-email");
  const editRole = document.getElementById("edit-role");
  const editIsActive = document.getElementById("edit-is-active");
  const editIsActiveContainer = document.getElementById("edit-is-active-container");
  const editIsActiveHelp = document.getElementById("edit-is-active-help");
  const editButtons = Array.from(document.querySelectorAll("[data-edit-user-id]"));
  const deleteUserId = document.getElementById("delete-user-id");
  const deleteUserName = document.getElementById("delete-user-name");
  const deleteButtons = Array.from(document.querySelectorAll("[data-delete-user-id]"));

  const normalize = (value) => (value || "")
    .toString()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();

  const setActiveControlLock = (isCurrentUser) => {
    if (!editIsActive) {
      return;
    }

    editIsActive.dataset.locked = isCurrentUser ? "true" : "false";
    editIsActive.setAttribute("aria-disabled", isCurrentUser ? "true" : "false");

    if (isCurrentUser) {
      editIsActive.checked = true;
    }

    editIsActiveContainer?.classList.toggle("bg-gray-50", isCurrentUser);
    editIsActiveContainer?.classList.toggle("cursor-not-allowed", isCurrentUser);

    if (editIsActiveHelp) {
      editIsActiveHelp.textContent = isCurrentUser
        ? "Tu propia cuenta debe permanecer activa."
        : "Desmarca esta opcion para desactivar el acceso al sistema.";
    }
  };

  editIsActive?.addEventListener("click", (event) => {
    if (editIsActive.dataset.locked === "true") {
      event.preventDefault();
    }
  });

  const filteredRows = () => {
    const query = normalize(searchInput?.value);
    const role = roleFilter?.value;
    const status = statusFilter?.value;

    return rows.filter((row) => {
      const matchesSearch = !query || normalize(row.dataset.userSearch).includes(query);
      const matchesRole = !role || row.dataset.userRole === role;
      const matchesStatus = !status || row.dataset.userStatus === status;
      return matchesSearch && matchesRole && matchesStatus;
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
    if (!searchInput || !roleFilter || !statusFilter || !pageList || !firstButton || !prevButton || !nextButton || !lastButton) {
      return;
    }

    const matches = filteredRows();
    const totalPages = Math.max(1, Math.ceil(matches.length / pageSize));
    currentPage = Math.min(currentPage, totalPages);
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    const pageRows = new Set(matches.slice(start, end));

    rows.forEach((row) => {
      row.classList.toggle("hidden", !pageRows.has(row));
    });

    emptyState?.classList.toggle("hidden", matches.length > 0);
    pagination?.classList.toggle("hidden", matches.length === 0 || totalPages <= 1);

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

  searchInput?.addEventListener("input", () => {
    currentPage = 1;
    applyFilters();
  });
  roleFilter?.addEventListener("change", () => {
    currentPage = 1;
    applyFilters();
  });
  statusFilter?.addEventListener("change", () => {
    currentPage = 1;
    applyFilters();
  });
  prevButton?.addEventListener("click", () => {
    currentPage = Math.max(1, currentPage - 1);
    applyFilters();
  });
  nextButton?.addEventListener("click", () => {
    currentPage += 1;
    applyFilters();
  });
  firstButton?.addEventListener("click", () => {
    currentPage = 1;
    applyFilters();
  });
  lastButton?.addEventListener("click", () => {
    currentPage = Math.max(1, Math.ceil(filteredRows().length / pageSize));
    applyFilters();
  });

  editButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (!editModal) {
        return;
      }

      if (editSubtitle) {
        editSubtitle.textContent = button.dataset.editDisplayName || "Actualiza la informacion del usuario seleccionado.";
      }
      if (editUserId) {
        editUserId.value = button.dataset.editUserId || "";
      }
      if (editFirstName) {
        editFirstName.value = button.dataset.editFirstName || "";
      }
      if (editLastName) {
        editLastName.value = button.dataset.editLastName || "";
      }
      if (editEmail) {
        editEmail.value = button.dataset.editEmail || "";
      }
      if (editRole) {
        editRole.value = button.dataset.editRole || "evaluator";
      }
      if (editIsActive) {
        editIsActive.checked = button.dataset.editIsActive === "true";
        setActiveControlLock(button.dataset.editIsCurrentUser === "true");
      }
    });
  });

  deleteButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (deleteUserId) {
        deleteUserId.value = button.dataset.deleteUserId || "";
      }
      if (deleteUserName) {
        deleteUserName.textContent = button.dataset.deleteDisplayName || "seleccionado";
      }
    });
  });

  setActiveControlLock(editIsActive?.dataset.locked === "true");

  applyFilters();
})();
