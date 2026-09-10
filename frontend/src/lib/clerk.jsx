/**
 * Clerk is RETIRED from this app. AstroVakta uses email + password (JWT)
 * auth exclusively — the Clerk instance previously used was decommissioned
 * (its frontend API domain no longer serves Clerk), which broke every
 * auth button wrapped in <SignedOut> and hid /login behind redirects.
 *
 * Every export below is a harmless stub so old imports keep working.
 * To revive Clerk someday: restore the real re-exports and the provider
 * in main.jsx, and remove the /login /register routes' unconditional pages.
 */

export const CLERK_ENABLED = false

export function ClerkProvider({ children }) {
  return children
}

export function SignedIn() {
  return null
}

export function SignedOut() {
  // Renders nothing for the old auth-button pattern: callers must show their
  // own email/password login UI (Link to /login) instead.
  return null
}

export const SignInButton = () => null
export const SignUpButton = () => null
export const UserButton = () => null

export const useUser = () => ({ isLoaded: true, isSignedIn: false, user: null })
export const useAuth = () => ({ isLoaded: true, isSignedIn: false, userId: null })
export const useClerk = () => ({ openSignIn: () => {}, openSignUp: () => {} })
