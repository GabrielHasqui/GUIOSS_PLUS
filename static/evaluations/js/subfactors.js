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

document.querySelectorAll("[data-compliance-slider]").forEach((slider) => {
  const row = slider.closest("tr");
  const value = row.querySelector("[data-compliance-value]");
  const label = row.querySelector("[data-compliance-label]");

  slider.addEventListener("input", () => {
    const current = Number(slider.value);
    value.textContent = current;
    label.textContent = complianceLabels[current];
    label.className = labelClass(current);
  });
});

document.querySelector("[data-factor-selector]")?.addEventListener("change", (event) => {
  window.location.href = `?factor=${event.target.value}`;
});
