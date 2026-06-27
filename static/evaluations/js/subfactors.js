const complianceLabels = {
  1: "No cumple el requisito",
  2: "Desconozco si cumple requisito",
  3: "Cumple parcialmente el requisito",
  4: "Cumple el requisito",
};

function labelClass(value) {
  if (value === 1) return "inline-block rounded-full px-4 py-1.5 text-xs font-medium text-guios-text bg-guios-bad";
  if (value === 4) return "inline-block rounded-full px-4 py-1.5 text-xs font-medium text-guios-text bg-guios-good";
  return "inline-block rounded-full px-4 py-1.5 text-xs font-medium text-guios-text bg-guios-warn";
}

const saveUrl = document.querySelector("[data-subfactor-save-url]")?.value;
const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
const saveStatus = document.querySelector("[data-save-status]");
const continueButton = document.querySelector("[data-continue-button]");
const meanWeight = document.querySelector("[data-mean-weight]");
const fodaValue = document.querySelector("[data-foda-value]");
const fodaBadge = document.querySelector("[data-foda-badge]");
const pendingTimers = new Map();
const dirtySliders = new Set();

function setStatus(text, isError = false) {
  if (!saveStatus) return;
  saveStatus.textContent = text;
  saveStatus.className = `min-w-36 text-sm ${isError ? "text-red-600" : "text-guios-muted"}`;
}

function setContinueEnabled(enabled) {
  if (!continueButton) return;
  continueButton.disabled = !enabled;
  continueButton.classList.toggle("opacity-60", !enabled);
  continueButton.classList.toggle("hover:opacity-90", enabled);
}

function updateFodaBadge(foda) {
  if (!fodaBadge) return;
  fodaBadge.className = "rounded-full px-3 py-1 text-guios-text";
  if (foda === "Fortaleza" || foda === "Oportunidad") {
    fodaBadge.classList.add("bg-guios-good");
  } else if (foda) {
    fodaBadge.classList.add("bg-guios-bad");
  } else {
    fodaBadge.classList.add("bg-guios-surface");
  }
}

async function saveSlider(slider) {
  if (!saveUrl || !csrfToken || !slider.dataset.subfactorId) return false;

  dirtySliders.delete(slider);
  pendingTimers.delete(slider);
  setStatus("Guardando...");
  setContinueEnabled(false);

  const formData = new FormData();
  formData.append("subfactor_id", slider.dataset.subfactorId);
  formData.append("compliance", slider.value);

  try {
    const response = await fetch(saveUrl, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
        "X-Requested-With": "XMLHttpRequest",
      },
      body: formData,
    });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.error || "No se pudo guardar.");
    }

    if (meanWeight) meanWeight.textContent = data.mean_weight ?? "-";
    if (fodaValue) fodaValue.textContent = data.foda || "-";
    updateFodaBadge(data.foda);
    setContinueEnabled(Boolean(data.all_subfactors_complete));
    setStatus("Guardado");
    return true;
  } catch (error) {
    dirtySliders.add(slider);
    setStatus(error.message, true);
    return false;
  }
}

function scheduleSave(slider) {
  dirtySliders.add(slider);
  setStatus("Cambios pendientes");
  setContinueEnabled(false);

  const currentTimer = pendingTimers.get(slider);
  if (currentTimer) window.clearTimeout(currentTimer);

  pendingTimers.set(
    slider,
    window.setTimeout(() => {
      saveSlider(slider);
    }, 500)
  );
}

async function savePendingChanges() {
  const sliders = Array.from(dirtySliders);
  pendingTimers.forEach((timer) => window.clearTimeout(timer));
  pendingTimers.clear();

  if (!sliders.length) return true;
  const results = await Promise.all(sliders.map((slider) => saveSlider(slider)));
  return results.every(Boolean);
}

document.querySelectorAll("[data-compliance-slider]").forEach((slider) => {
  const row = slider.closest("tr");
  const value = row.querySelector("[data-compliance-value]");
  const label = row.querySelector("[data-compliance-label]");

  slider.addEventListener("input", () => {
    const current = Number(slider.value);
    value.textContent = current;
    label.textContent = complianceLabels[current];
    label.className = labelClass(current);
    scheduleSave(slider);
  });
});

document.querySelector("[data-factor-selector]")?.addEventListener("change", async (event) => {
  event.target.disabled = true;
  const saved = await savePendingChanges();
  if (saved) {
    window.location.href = `?factor=${event.target.value}`;
  } else {
    event.target.disabled = false;
  }
});

document.querySelector("form")?.addEventListener("submit", async (event) => {
  if (!dirtySliders.size) return;

  event.preventDefault();
  const submitter = event.submitter;
  const saved = await savePendingChanges();
  if (saved) event.target.requestSubmit(submitter);
});
