// Firebase Auth for client sign-in. Renders/activates only when the
// VITE_FIREBASE_* env vars are set (Vercel env or frontend/.env.local).
import { initializeApp } from 'firebase/app'
import { getAuth, GoogleAuthProvider, EmailAuthProvider, createUserWithEmailAndPassword, sendEmailVerification, signInWithPopup, signOut } from 'firebase/auth'

const cfg = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

export const firebaseEnabled = Boolean(cfg.apiKey && cfg.projectId && cfg.appId)

let auth = null
export function firebaseAuth() {
  if (!firebaseEnabled) return null
  if (!auth) auth = getAuth(initializeApp(cfg))
  return auth
}

export async function signInWithFirebase(provider = 'google') {
  const a = firebaseAuth()
  if (!a) throw new Error('Firebase not configured')
  if (provider === 'google') {
    return (await signInWithPopup(a, new GoogleAuthProvider())).user
  }
  throw new Error(`Provider ${provider} not enabled yet`)
}

export async function signUpWithEmailAndVerify(email, password) {
  const a = firebaseAuth()
  if (!a) throw new Error('Firebase not configured')
  const cred = await createUserWithEmailAndPassword(a, email, password)
  await sendEmailVerification(cred.user)
  return cred.user
}

export function signOutFirebase() {
  if (auth) signOut(auth).catch(() => {})
}
