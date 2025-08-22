import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      // New chat and image endpoints (keep /api prefix)
      '/api/chat': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/api/images': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      // Existing endpoints (remove /api prefix)
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})