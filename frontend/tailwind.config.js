/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0a0d14",
        surface: "#111726",
        surfaceBorder: "#1f293d",
        brand: "#38bdf8",
        brandDark: "#0284c7",
        accent: "#a855f7",
        success: "#22c55e",
        warning: "#eab308",
        danger: "#ef4444"
      }
    },
  },
  plugins: [],
}
