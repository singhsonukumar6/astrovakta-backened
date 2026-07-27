import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:5000',
      '/auth': 'http://127.0.0.1:5000',
      '/horoscope': 'http://127.0.0.1:5000',
      '/chart': 'http://127.0.0.1:5000',
      '/ai-providers': 'http://127.0.0.1:5000',
      '/pooja': 'http://127.0.0.1:5000',
      '/reports': 'http://127.0.0.1:5000',
      '/dasha': 'http://127.0.0.1:5000',
      '/calendar-api': 'http://127.0.0.1:5000',
      '/jobs': 'http://127.0.0.1:5000',
      '/lucky': 'http://127.0.0.1:5000',
      '/name': 'http://127.0.0.1:5000',
      '/calculator': 'http://127.0.0.1:5000',
      '/gemstone': 'http://127.0.0.1:5000',
      '/festival': 'http://127.0.0.1:5000',
      '/prashna': 'http://127.0.0.1:5000',
      '^/ai/': 'http://127.0.0.1:5000',
      '^/admin/': 'http://127.0.0.1:5000',
    },
  },
})
