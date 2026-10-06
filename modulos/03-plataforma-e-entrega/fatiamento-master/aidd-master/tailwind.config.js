/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/static/**/*.html',
    './templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0284c7',
          600: '#0369a1',
          700: '#075985',
          900: '#0c4a6e',
        },
        medical: {
          red: '#ef4444',
          orange: '#f97316',
          yellow: '#eab308',
          green: '#22c55e',
          blue: '#3b82f6',
          dark: '#090d16',
          card: '#0f172a',
          border: '#1e293b',
        },
        dark: {
          700: '#1e293b',
          800: '#0f172a',
          900: '#020617',
        },
      },
    },
  },
  plugins: [],
};
