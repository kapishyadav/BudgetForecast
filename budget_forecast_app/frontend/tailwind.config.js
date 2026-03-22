/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: 'var(--primary)',
        accent: 'var(--accent)',
        'light-accent': 'var(--light-accent)',
      },
      borderRadius: {
        'theme': 'var(--radius)',
      }
    },
  },
  plugins: [],
}
