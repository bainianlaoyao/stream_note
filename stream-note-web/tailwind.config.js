/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'base': 'var(--bg-base)',
        'surface': 'var(--bg-surface)',
        'elevated': 'var(--bg-elevated)',
        'primary': 'var(--text-primary)',
        'secondary': 'var(--text-secondary)',
        'tertiary': 'var(--text-tertiary)',
        'placeholder': 'var(--text-placeholder)',
        'accent': 'var(--accent-primary)',
        'accent-hover': 'var(--accent-hover)',
        'accent-muted': 'var(--accent-muted)',
      },
      fontFamily: {
        'serif': ['var(--font-serif)'],
        'sans': ['var(--font-sans)'],
        'mono': ['var(--font-mono)'],
      },
      backdropBlur: {
        'glass': '20px',
        'glass-lg': '30px',
      },
    },
  },
  plugins: [],
}
