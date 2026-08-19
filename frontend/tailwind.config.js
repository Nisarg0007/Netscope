/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Use CSS variables for theme colors
        background: 'var(--color-bg-main)',
        bgSurface: 'var(--color-bg-surface)',
        bgCard: 'var(--color-bg-card)',
        border: 'var(--color-border)',
        textPrimary: 'var(--color-text-primary)',
        textSecondary: 'var(--color-text-secondary)',
        accentPrimary: 'var(--color-accent-primary)',
        accentSecondary: 'var(--color-accent-secondary)',
        statusSuccess: 'var(--color-status-success)',
        statusWarning: 'var(--color-status-warning)',
        statusError: 'var(--color-status-error)',
      },
    },
  },
  plugins: [],
}