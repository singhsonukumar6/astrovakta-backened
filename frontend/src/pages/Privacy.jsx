import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import { Shield } from 'lucide-react'

function FadeIn({ children, delay = 0 }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: '-60px' })
  return (
    <motion.div ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}>
      {children}
    </motion.div>
  )
}

const sectionStyle = { marginBottom: 24 }
const headingStyle = { fontSize: 20, fontWeight: 700, marginBottom: 10 }
const textStyle = { color: '#94a3b8', fontSize: 15, lineHeight: 1.8, marginBottom: 12 }

export default function Privacy() {
  return (
    <div style={{ paddingTop: 100 }}>
      <section className="section" style={{ maxWidth: 800 }}>
        <FadeIn>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8, justifyContent: 'center' }}>
            <Shield size={24} color="#7c3aed" />
            <p style={{ color: '#64748b', fontSize: 13, textTransform: 'uppercase', letterSpacing: 2.5, fontWeight: 600 }}>Privacy Policy</p>
          </div>
          <h1 style={{ fontSize: 'clamp(28px, 4vw, 44px)', fontWeight: 900, textAlign: 'center', marginBottom: 12, letterSpacing: '-1px' }}>
            Privacy <span className="gradient-text">Policy</span>
          </h1>
          <p style={{ color: '#64748b', fontSize: 14, textAlign: 'center', marginBottom: 48 }}>
            Last updated: July 29, 2026
          </p>
        </FadeIn>

        <FadeIn delay={0.1}>
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)', padding: 40 }}>
            <div style={sectionStyle}>
              <h2 style={headingStyle}>1. Information We Collect</h2>
              <p style={textStyle}>
                When you create an AstroVakta account, we collect your email address and name via Clerk authentication. We do not collect or store birth chart data, planetary positions, or any personal information you submit through our API endpoints. API call data is stored only for usage analytics and rate-limiting purposes.
              </p>
              <p style={textStyle}>
                If you configure AI provider keys (OpenAI, Anthropic, Groq, Together), those keys are encrypted with AES-256 at rest and never logged. We do not have access to your AI provider keys in plaintext.
              </p>
            </div>

            <div style={sectionStyle}>
              <h2 style={headingStyle}>2. How We Use Your Data</h2>
              <p style={textStyle}>
                We use your email to send account-related communications (password resets, API key updates, billing notifications). We use aggregated, anonymized API usage data for platform monitoring and improving our services. We never sell, share, or rent your personal information to third parties.
              </p>
            </div>

            <div style={sectionStyle}>
              <h2 style={headingStyle}>3. Data Storage & Security</h2>
              <p style={textStyle}>
                All data is stored on secure servers with encryption at rest and in transit. API keys are AES-256 encrypted before storage. We use HTTPS for all communications. Database access is restricted to authenticated services only. We regularly audit our security practices.
              </p>
            </div>

            <div style={sectionStyle}>
              <h2 style={headingStyle}>4. API Request Data</h2>
              <p style={textStyle}>
                Your API requests (birth details, chart parameters, etc.) are processed in memory and not persisted. We do not log the content of your API requests or responses. The only data retained is the count and timestamp of API calls for usage tracking and rate limiting.
              </p>
            </div>

            <div style={sectionStyle}>
              <h2 style={headingStyle}>5. Third-Party Services</h2>
              <p style={textStyle}>
                We use Clerk for authentication (their privacy policy applies to your login credentials). If you configure third-party AI providers through our platform, your requests are forwarded to those providers using the keys you supply. We do not share any additional data with those providers beyond what you explicitly send in your API requests.
              </p>
            </div>

            <div style={sectionStyle}>
              <h2 style={headingStyle}>6. Cookies</h2>
              <p style={textStyle}>
                We use essential cookies for authentication (via Clerk) and session management. We do not use tracking cookies, advertising cookies, or third-party analytics cookies on our platform.
              </p>
            </div>

            <div style={sectionStyle}>
              <h2 style={headingStyle}>7. Your Rights</h2>
              <p style={textStyle}>
                You can request deletion of your account and all associated data at any time by contacting us at hello@astrovakta.com. Upon deletion, all your account data, API keys, and usage records will be permanently removed within 30 days.
              </p>
            </div>

            <div style={sectionStyle}>
              <h2 style={headingStyle}>8. Contact</h2>
              <p style={textStyle}>
                For privacy-related inquiries, contact us at hello@astrovakta.com or via WhatsApp at +91 62394 02519.
              </p>
            </div>
          </div>
        </FadeIn>
      </section>
    </div>
  )
}
