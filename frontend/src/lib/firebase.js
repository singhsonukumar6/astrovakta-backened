// Firebase Auth for client sign-in. Uses VITE_FIREBASE_* env vars when set
// (Vercel env or frontend/.env.local); otherwise falls back to the project's
// web-app config below so the Google button renders in every deployment.
// Firebase web API keys are public identifiers by design — access is guarded
// by Authorized domains + Auth settings in the Firebase console, not key
// secrecy — so shipping them in the bundle is safe.
import { initializeApp } from 'firebase/app'
import { getAuth, GoogleAuthProvider, EmailAuthProvider, createUserWithEmailAndPassword, sendEmailVerification, signInWithPopup, signOut } from 'firebase/auth'

const FALLBACK_FIREBASE_CONFIG = {
  apiKey: 'AIzaSyBiMflj6OA-1D0okkpgDaqAQjQw7TkJc2Y',
  authDomain: 'astrovaktaapp.firebaseapp.com',
  projectId: 'astrovaktaapp',
  appId: '1:941300385141:web:e89ef7cd359e2d0c5f3f3c',
}

const cfg = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || FALLBACK_FIREBASE_CONFIG.apiKey,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || FALLBACK_FIREBASE_CONFIG.authDomain,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || FALLBACK_FIREBASE_CONFIG.projectId,
  appId: import.meta.env.VITE_FIREBASE_APP_ID || FALLBACK_FIREBASE_CONFIG.appId,
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
