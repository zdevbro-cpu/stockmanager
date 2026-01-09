/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "primary": "#1241a1",
        "background-light": "#f6f6f8",
        "background-dark": "#111621",
        "card-dark": "#1a2232",
        "border-dark": "#243047",
        "text-subtle": "#93a5c8"
      },
      fontFamily: {
        "display": ["Manrope", "sans-serif"],
        "body": ["Manrope", "sans-serif"]
      },
      borderRadius: {
        "lg": "0.5rem",
        "xl": "0.75rem"
      }
    },
  },
  plugins: [],
}
