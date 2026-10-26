/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        saffron: {
          50: '#fffaf0',
          100: '#feebc8',
          200: '#fbd38d',
          300: '#f6ad55',
          400: '#ed8936',
          500: '#dd6b20',
          600: '#c05621',
          700: '#9c4221',
          800: '#7b341e',
          900: '#652b19',
        },
        marigold: {
          DEFAULT: '#F59E0B',
          dark: '#D97706',
          light: '#FDE68A',
        },
        peacock: {
          DEFAULT: '#0E7490',
          dark: '#155E75',
          light: '#CFFAFE',
        }
      }
    },
  },
  plugins: [],
}
