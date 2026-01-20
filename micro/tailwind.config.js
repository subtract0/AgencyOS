/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Calm, warm palette - not clinical
        warm: {
          50: '#fdf8f6',
          100: '#f9ece6',
          200: '#f3d5c8',
          300: '#e9b8a3',
          400: '#db9275',
          500: '#c97552',
          600: '#b25d3d',
          700: '#944a32',
          800: '#7a3f2d',
          900: '#663828',
        },
        night: {
          50: '#f5f7fa',
          100: '#ebeef3',
          200: '#d3dae5',
          300: '#adbcce',
          400: '#8198b3',
          500: '#617a99',
          600: '#4d6280',
          700: '#3f5068',
          800: '#374457',
          900: '#313b4a',
          950: '#1e242f',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
