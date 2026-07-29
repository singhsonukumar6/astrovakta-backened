import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/auth': 'http://127.0.0.1:8000',
      '/horoscope': 'http://127.0.0.1:8000',
      '/chart': 'http://127.0.0.1:8000',
      '/ai-providers': 'http://127.0.0.1:8000',
      '/pooja': 'http://127.0.0.1:8000',
      '/reports': 'http://127.0.0.1:8000',
      '/dasha': 'http://127.0.0.1:8000',
      '/calendar-api': 'http://127.0.0.1:8000',
      '/jobs': 'http://127.0.0.1:8000',
      '/lucky': 'http://127.0.0.1:8000',
      '/name': 'http://127.0.0.1:8000',
      '/calculator': 'http://127.0.0.1:8000',
      '/gemstone': 'http://127.0.0.1:8000',
      '/festival': 'http://127.0.0.1:8000',
      '/prashna': 'http://127.0.0.1:8000',
      '/yogini': 'http://127.0.0.1:8000',
      '/lal-kitab': 'http://127.0.0.1:8000',
      '/kp': 'http://127.0.0.1:8000',
      '^/ai/': 'http://127.0.0.1:8000',
      '^/admin/': 'http://127.0.0.1:8000',
    },
  },
})
