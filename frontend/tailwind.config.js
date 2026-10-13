/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'soc-bg': '#0a0c0f',
        'soc-surface': '#111318',
        'soc-elevated': '#1a1d24',
        'soc-hover': '#232730',
        'soc-border': '#1e2330',
        'soc-border-active': '#39ff14',
        'accent-green': '#39ff14',
        'accent-cyan': '#00d4ff',
        'accent-amber': '#ffb347',
        'error-red': '#ff4444',
        'text-primary': '#e2e8f0',
        'text-secondary': '#7a8599',
        'text-muted': '#4a5568',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'blink': 'blink 1s step-end infinite',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'slide-in': 'slideIn 200ms ease-out',
      },
      keyframes: {
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        slideIn: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
