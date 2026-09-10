import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './lib/auth.jsx'
import { ConfigProvider } from './lib/ConfigContext.jsx'
import App, { TenantHostApp } from './App.jsx'
import { isTenantHost } from './lib/tenant.js'
import './index.css'

const toastConfig = {
  position: 'top-right',
  toastOptions: {
    style: {
      background: '#ffffff',
      color: '#1e293b',
      border: '1px solid rgba(124,58,237,0.3)',
    },
  },
}

function Root() {
  // Tenant hosts (slug.astrovakta.com / *.localhost / custom domains) render
  // the astrologer's standalone site instead of the platform app — no auth or
  // platform chrome, visitors are the astrologer's clients.
  if (isTenantHost()) {
    return (
      <StrictMode>
        <BrowserRouter>
          <ConfigProvider>
            <TenantHostApp />
            <Toaster {...toastConfig} />
          </ConfigProvider>
        </BrowserRouter>
      </StrictMode>
    )
  }
  return (
    <StrictMode>
      <BrowserRouter>
        <AuthProvider>
          <ConfigProvider>
            <App />
            <Toaster {...toastConfig} />
          </ConfigProvider>
        </AuthProvider>
      </BrowserRouter>
    </StrictMode>
  )
}

createRoot(document.getElementById('root')).render(<Root />)
