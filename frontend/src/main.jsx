import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './lib/auth.jsx'
import App from './App.jsx'
import './index.css'

const CLERK_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
const hasClerk = CLERK_KEY && !CLERK_KEY.includes('placeholder') && CLERK_KEY.length > 10

async function render() {
  if (hasClerk) {
    const { ClerkProvider } = await import('@clerk/clerk-react')
    createRoot(document.getElementById('root')).render(
      <StrictMode>
        <ClerkProvider publishableKey={CLERK_KEY}>
          <BrowserRouter>
            <AuthProvider>
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
            </AuthProvider>
          </BrowserRouter>
        </ClerkProvider>
      </StrictMode>,
    )
  } else {
    createRoot(document.getElementById('root')).render(
      <StrictMode>
        <BrowserRouter>
          <AuthProvider>
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
          </AuthProvider>
        </BrowserRouter>
      </StrictMode>,
    )
  }
}

render()
