import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { ClerkProvider } from '@clerk/clerk-react'
import { AuthProvider } from './lib/auth.jsx'
import App from './App.jsx'
import './index.css'

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

if (!PUBLISHABLE_KEY || PUBLISHABLE_KEY.includes('placeholder')) {
  throw new Error('Missing VITE_CLERK_PUBLISHABLE_KEY in environment')
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ClerkProvider publishableKey={PUBLISHABLE_KEY}>
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
