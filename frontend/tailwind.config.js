/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      colors: {
        rose:     { DEFAULT: "#e11d48", 950: "#1a0011" },
        emerald:  { DEFAULT: "#10b981" },
        amber:    { DEFAULT: "#f59e0b" },
      },
    },
  },
  plugins: [],
};
