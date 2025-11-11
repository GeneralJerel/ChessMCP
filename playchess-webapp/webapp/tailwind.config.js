/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Lichess-inspired colors
        'board-light': '#f0d9b5',
        'board-dark': '#b58863',
        'primary': '#3893E8',
        'primary-dark': '#2979C9',
      },
    },
  },
  plugins: [],
}

