/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        void: '#050810',
        panel: '#0b1120',
        border: '#1a2744',
        accent: '#00d4ff',
        accentGreen: '#00ff88',
        accentRed: '#ff3366',
        accentYellow: '#ffcc00',
        accentPurple: '#a855f7',
        textPrimary: '#e2e8f0',
        textMuted: '#64748b',
      },
      fontFamily: {
        display: ['"Orbitron"', 'monospace'],
        body: ['"Share Tech Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}