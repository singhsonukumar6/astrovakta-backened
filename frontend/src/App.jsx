import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Footer from './components/Footer.jsx'
import Landing from './pages/Landing.jsx'
import Pricing from './pages/Pricing.jsx'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Sandbox from './pages/Sandbox.jsx'
import Admin from './pages/Admin.jsx'
import Docs from './pages/Docs.jsx'
import KundaliReport from './pages/KundaliReport.jsx'
import VerifyEmail from './pages/VerifyEmail.jsx'
import VerifyEmailPrompt from './pages/VerifyEmailPrompt.jsx'
import ForgotPassword from './pages/ForgotPassword.jsx'
import ResetPassword from './pages/ResetPassword.jsx'
import Starfield from './components/Starfield.jsx'

export default function App() {
  return (
    <>
      <Starfield />
      <Navbar />
      <main style={{ flex: 1, position: 'relative', zIndex: 1 }}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/sandbox" element={<Sandbox />} />
          <Route path="/docs" element={<Docs />} />
          <Route path="/kundali-report" element={<KundaliReport />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/verify-email-prompt" element={<VerifyEmailPrompt />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
        </Routes>
      </main>
      <Footer />
    </>
  )
}
