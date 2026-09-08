/**
 * Clerk integration with graceful degradation.
 *
 * The site must always render — for users AND for crawlers (Googlebot, GPTBot,
 * ClaudeBot). If the Clerk key is missing/invalid, we render the public site
 * normally with auth controls in their signed-out presentation, instead of
 * blanking the whole app (SEO-fatal: an empty page cannot be indexed or cited).
 *
 * main.jsx previously threw on a missing key, which turned ANY Clerk issue into
 * an empty <div id="root">.
 */
import {
  ClerkProvider as RealClerkProvider,
  SignedIn as RealSignedIn,
  SignedOut as RealSignedOut,
  SignInButton as RealSignInButton,
  SignUpButton as RealSignUpButton,
  UserButton as RealUserButton,
  useUser as realUseUser,
  useAuth as realUseAuth,
  useClerk as realUseClerk,
} from '@clerk/clerk-react'

const rawKey = (import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || '').trim()
// Clerk keys look like pk_test_XXX / pk_live_XXX with no other characters.
export const CLERK_ENABLED = /^pk_(test|live)_[A-Za-z0-9]+$/.test(rawKey)

function FallbackProvider({ children }) {
  return children
}

function SignedOutFallback({ children }) {
  return children
}

function SignedInFallback() {
  return null
}

// Auth buttons degrade to anchors pointing at the hero's free-tier CTA.
function SignInButtonFallback({ children, ...props }) {
  return <a href="/#start-free" {...props}>{children}</a>
}

function SignUpButtonFallback({ children, ...props }) {
  return <a href="/#start-free" {...props}>{children}</a>
}

export const ClerkProvider = CLERK_ENABLED ? RealClerkProvider : FallbackProvider
export const SignedIn = CLERK_ENABLED ? RealSignedIn : SignedInFallback
export const SignedOut = CLERK_ENABLED ? RealSignedOut : SignedOutFallback
export const SignInButton = CLERK_ENABLED ? RealSignInButton : SignInButtonFallback
export const SignUpButton = CLERK_ENABLED ? RealSignUpButton : SignUpButtonFallback
export const UserButton = CLERK_ENABLED ? RealUserButton : () => null
export const useUser = CLERK_ENABLED ? realUseUser : () => ({ isLoaded: true, isSignedIn: false, user: null })
export const useAuth = CLERK_ENABLED ? realUseAuth : () => ({ isLoaded: true, isSignedIn: false, userId: null })
export const useClerk = CLERK_ENABLED ? realUseClerk : () => ({ openSignIn: () => {}, openSignUp: () => {} })
