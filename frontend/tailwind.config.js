/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        void: '#0d1117',
        panel: '#141c27',
        border: '#1e2d42',
        accent: '#D5F6FB',
        accentGreen: '#D1FEB8',
        accentRed: '#F6B8D0',
        accentYellow: '#F6F3A9',
        accentPurple: '#EBCCFF',
        textPrimary: '#e8f4f8',
        textMuted: '#7a9bb5',
      },
      fontFamily: {
        display: ['"Rajdhani"', 'sans-serif'],
        body: ['"Inconsolata"', 'monospace'],
      },
    },
  },
  plugins: [],
}