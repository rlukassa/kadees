import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    port: 5173,
    // Proxy API calls ke FastAPI backend
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
