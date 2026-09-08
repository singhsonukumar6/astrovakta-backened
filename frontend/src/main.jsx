import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { ClerkProvider, CLERK_ENABLED } from './lib/clerk.jsx'
import { AuthProvider } from './lib/auth.jsx'
import { ConfigProvider } from './lib/ConfigContext.jsx'
import App from './App.jsx'
import './index.css'

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

// Never throw: a bad/missing Clerk key must not blank the whole site (SEO-fatal).
// Auth falls back to its signed-out presentation via src/lib/clerk.jsx.
if (!CLERK_ENABLED) {
  console.warn('Clerk disabled — VITE_CLERK_PUBLISHABLE_KEY is missing or invalid')
}

function Root() {
  return (
    <StrictMode>
      {CLERK_ENABLED ? (
        <ClerkProvider publishableKey={PUBLISHABLE_KEY}>
          <BrowserRouter>
            <AuthProvider>
              <ConfigProvider>
                <App />
                <Toaster
                  position="top-right"
                  toastOptions={{
                    style: {
                      background: '#1a1a3e',
                      color: '#e2e8f0',
                      border: '1px solid rgba(124,58,237,0.3)',
                    },
                  }}
                />
              </ConfigProvider>
            </AuthProvider>
          </BrowserRouter>
        </ClerkProvider>
      ) : (
        <BrowserRouter>
          <AuthProvider>
            <ConfigProvider>
              <App />
              <Toaster
                position="top-right"
                toastOptions={{
                  style: {
                    background: '#1a1a3e',
                    color: '#e2e8f0',
                    border: '1px solid rgba(124,58,237,0.3)',
                  },
                }}
              />
            </ConfigProvider>
          </AuthProvider>
        </BrowserRouter>
      )}
    </StrictMode>
  )
}

createRoot(document.getElementById('root')).render(<Root />)
