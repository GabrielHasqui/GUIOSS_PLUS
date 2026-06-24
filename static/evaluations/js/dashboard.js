const newEvaluationForm = document.getElementById("new-evaluation-form");
const newEvaluationModal = document.getElementById("new-evaluation");
const loadingModal = document.getElementById("evaluation-loading");
const createEvaluationButton = document.getElementById("create-evaluation-button");

if (newEvaluationForm) {
  newEvaluationForm.addEventListener("submit", () => {
    newEvaluationModal.classList.add("hidden");
    loadingModal.classList.remove("hidden");
    createEvaluationButton.disabled = true;
    createEvaluationButton.textContent = "Procesando...";
  });
}
