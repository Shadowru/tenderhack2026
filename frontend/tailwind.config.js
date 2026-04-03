/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        gov: {
          50: '#e8f0fc',
          100: '#dbeafe',
          200: '#b3cef5',
          300: '#7aabed',
          400: '#3d82e0',
          500: '#0065DC',
          600: '#0055ba',
          700: '#004494',
          800: '#334059',
          900: '#1a2332',
        },
        grayish: {
          50: '#f6f6f6',
          100: '#eaeaef',
          200: '#d4d4dd',
          300: '#b0b5c4',
          400: '#8c96ad',
          500: '#808080',
          600: '#939393',
          700: '#666',
          800: '#334059',
        },
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
