module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/evaluations/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        guios: {
          navy: "#12216a",
          text: "#002B3A",
          muted: "#334155",
          orange: "#F28C00",
          border: "#D9DEE5",
          surface: "#F4F4F4",
          good: "#A7DCA0",
          bad: "#E99ABB",
          warn: "#FFF2B8",
        },
      },
    },
  },
  plugins: [],
};
