/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        aether: {
          bg: "#0c1117",
          panel: "#141b24",
          ink: "#e8eef6",
          mute: "#8b9bb0",
          accent: "#3d9cf0",
          heat: "#f0a03d",
        },
      },
      fontFamily: {
        display: ["\"IBM Plex Sans\"", "ui-sans-serif", "system-ui"],
        mono: ["\"IBM Plex Mono\"", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
