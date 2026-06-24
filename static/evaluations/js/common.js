document.querySelectorAll("[data-notification-close]").forEach((button) => {
  button.addEventListener("click", () => {
    button.closest("[data-notification]")?.remove();
  });
});

document.querySelectorAll("[data-modal-open]").forEach((button) => {
  button.addEventListener("click", () => {
    document.getElementById(button.dataset.modalOpen)?.classList.remove("hidden");
  });
});

document.querySelectorAll("[data-modal-close]").forEach((button) => {
  button.addEventListener("click", () => {
    document.getElementById(button.dataset.modalClose)?.classList.add("hidden");
  });
});

document.querySelectorAll("[data-admin-dropdown]").forEach((dropdown) => {
  const toggle = dropdown.querySelector("[data-admin-dropdown-toggle]");
  const menu = dropdown.querySelector("[data-admin-dropdown-menu]");

  if (!toggle || !menu) {
    return;
  }

  const close = () => {
    menu.classList.add("hidden");
    toggle.setAttribute("aria-expanded", "false");
  };

  const open = () => {
    menu.classList.remove("hidden");
    toggle.setAttribute("aria-expanded", "true");
  };

  toggle.addEventListener("click", (event) => {
    event.stopPropagation();
    if (menu.classList.contains("hidden")) {
      open();
    } else {
      close();
    }
  });

  dropdown.addEventListener("click", (event) => {
    event.stopPropagation();
  });

  document.addEventListener("click", close);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      close();
    }
  });
});

setTimeout(() => {
  document.querySelectorAll("[data-notification]").forEach((notification) => {
    notification.remove();
  });
}, 5500);
