/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      boxShadow: {
        soft: "0 12px 40px -24px rgba(12, 19, 33, 0.45)",
        card: "0 10px 24px -18px rgba(12, 19, 33, 0.5)",
      },
    },
  },
  plugins: [],
};
