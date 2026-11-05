import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Servido siempre bajo /gold/ en producción y preview
export default defineConfig({
  base: '/gold/',
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/gold/api': {
        target: 'http://127.0.0.1:8010',
        changeOrigin: true,
      },
    },
  },
})
