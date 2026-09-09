import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const BACKEND = `http://127.0.0.1:${process.env.BACKEND_PORT || 8901}`

export default defineConfig({
  plugins: [react()],
  server: {
    // Bind IPv4 loopback explicitly: *.localhost names resolve to 127.0.0.1
    // (Node's default 'localhost' binding can end up IPv6-only on macOS).
    host: '127.0.0.1',
    // Tenant subdomain hosting in local dev: browsers resolve *.localhost to
    // 127.0.0.1 automatically (RFC 6761), so pandit-rajesh.localhost:5173
    // reaches this server. allowedHosts permits those Host headers (vite's
    // DNS-rebinding protection).
    allowedHosts: ['.localhost', '.astrovakta.com'],
    proxy: {
      // Local e2e backend lives on 8901 by default (uvicorn --port 8901).
      // Set BACKEND_PORT in the environment to override.
      '/api': BACKEND,
      '/auth': BACKEND,
      '/horoscope': BACKEND,
      '/chart': BACKEND,
      '/ai-providers': BACKEND,
      '/pooja': BACKEND,
      '/reports': BACKEND,
      '/dasha': BACKEND,
      '/calendar-api': BACKEND,
      '/sites': BACKEND,
      '/jobs': BACKEND,
      '/lucky': BACKEND,
      '/name': BACKEND,
      '/calculator': BACKEND,
      '/gemstone': BACKEND,
      '/festival': BACKEND,
      '/prashna': BACKEND,
      '/yogini': BACKEND,
      '/lal-kitab': BACKEND,
      '/kp': BACKEND,
      '^/ai/': BACKEND,
      '^/admin/': BACKEND,
    },
  },
})
