/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        baton: {
          black: '#000000',
          'near-black': '#0a0a0b',
          'layer-1': '#151617',
          'layer-2': '#242628',
          'layer-3': '#303236',
          accent: '#34d59a',
          'accent-dim': '#285d49',
          warning: '#ff3621',
          white: '#ffffff',
          'text-secondary': '#797d86',
          'text-tertiary': '#94979e',
          'text-highlight': '#c9cbcf',
          border: '#303236',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Geist Mono', 'Fira Code', 'Source Code Pro', 'monospace'],
      },
      borderRadius: {
        'baton': '4px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scanline': 'scanline 8s linear infinite',
        'signal-pulse': 'signal-pulse 2s ease-in-out infinite',
        'blink': 'blink 1s step-end infinite',
      },
      keyframes: {
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        'signal-pulse': {
          '0%, 100%': { opacity: '0.3' },
          '50%': { opacity: '1' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
      },
    },
  },
  plugins: [],
};
