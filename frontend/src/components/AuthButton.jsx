import { useNavigate } from 'react-router-dom'

let _hasClerk = null
export function hasClerk() {
  if (_hasClerk !== null) return _hasClerk
  const k = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
  _hasClerk = !!(k && !k.includes('placeholder') && k.length > 10)
  return _hasClerk
}

export function SignUpOrRegister({ children, mode = 'modal', className, style }) {
  const navigate = useNavigate()
  if (hasClerk()) {
    try {
      const { SignUpButton } = require('@clerk/clerk-react')
      return <SignUpButton mode={mode}>{children}</SignUpButton>
    } catch {}
  }
  return (
    <div onClick={() => navigate('/register')} className={className} style={{ cursor: 'pointer', ...style }}>
      {children}
    </div>
  )
}

export function SignInOrLogin({ children, mode = 'modal', className, style }) {
  const navigate = useNavigate()
  if (hasClerk()) {
    try {
      const { SignInButton } = require('@clerk/clerk-react')
      return <SignInButton mode={mode}>{children}</SignInButton>
    } catch {}
  }
  return (
    <div onClick={() => navigate('/login')} className={className} style={{ cursor: 'pointer', ...style }}>
      {children}
    </div>
  )
}

export function ClerkSignedIn({ children }) {
  if (!hasClerk()) return null
  try {
    const { SignedIn } = require('@clerk/clerk-react')
    return <SignedIn>{children}</SignedIn>
  } catch { return null }
}

export function ClerkSignedOut({ children }) {
  if (!hasClerk()) return <>{children}</>
  try {
    const { SignedOut } = require('@clerk/clerk-react')
    return <SignedOut>{children}</SignedOut>
  } catch { return <>{children}</> }
}

export function ClerkUserButton(props) {
  if (!hasClerk()) return null
  try {
    const { UserButton } = require('@clerk/clerk-react')
    return <UserButton {...props} />
  } catch { return null }
}
