const newEvaluationForm = document.getElementById("new-evaluation-form");
const newEvaluationModal = document.getElementById("new-evaluation");
const loadingModal = document.getElementById("evaluation-loading");
const createEvaluationButton = document.getElementById("create-evaluation-button");
const contextSelect = document.querySelector("[data-context-select]");
const contextModeInput = document.querySelector("[data-context-mode]");
const otherContextInput = document.querySelector("[data-context-other-input]");
const contextListButton = document.querySelector("[data-context-list-button]");

function activateContextInput() {
  if (!contextSelect || !contextModeInput || !otherContextInput || !contextListButton) {
    return;
  }

  contextSelect.classList.add("hidden");
  contextSelect.required = false;
  contextSelect.removeAttribute("name");

  otherContextInput.classList.remove("hidden");
  otherContextInput.setAttribute("name", "context");
  otherContextInput.required = true;
  otherContextInput.focus();

  contextListButton.classList.remove("hidden");
  contextModeInput.value = "other";
}

function activateContextSelect() {
  if (!contextSelect || !contextModeInput || !otherContextInput || !contextListButton) {
    return;
  }

  otherContextInput.classList.add("hidden");
  otherContextInput.required = false;
  otherContextInput.removeAttribute("name");
  otherContextInput.value = "";

  contextSelect.classList.remove("hidden");
  contextSelect.setAttribute("name", "context");
  contextSelect.required = true;
  contextSelect.value = "";
  contextSelect.focus();

  contextListButton.classList.add("hidden");
  contextModeInput.value = "choice";
}

if (contextListButton) {
  contextListButton.addEventListener("click", activateContextSelect);
}

if (newEvaluationForm) {
  newEvaluationForm.addEventListener("submit", () => {
    newEvaluationModal.classList.add("hidden");
    loadingModal.classList.remove("hidden");
    createEvaluationButton.disabled = true;
    createEvaluationButton.textContent = "Procesando...";
  });
}
