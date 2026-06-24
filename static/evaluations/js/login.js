const passwordInput = document.querySelector("[data-password-input]");
const togglePasswordButton = document.getElementById("toggle-password");
const eyeOpenIcon = document.getElementById("eye-open-icon");
const eyeClosedIcon = document.getElementById("eye-closed-icon");

if (passwordInput && togglePasswordButton && eyeOpenIcon && eyeClosedIcon) {
  togglePasswordButton.addEventListener("click", () => {
    const isHidden = passwordInput.type === "password";
    passwordInput.type = isHidden ? "text" : "password";
    togglePasswordButton.setAttribute(
      "aria-label",
      isHidden ? "Ocultar contrasena" : "Mostrar contrasena"
    );
    eyeOpenIcon.classList.toggle("hidden", isHidden);
    eyeClosedIcon.classList.toggle("hidden", !isHidden);
  });
}
