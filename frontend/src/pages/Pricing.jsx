import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Check, Zap, Star, Crown, ArrowRight } from 'lucide-react'

const tiers = [
  {
    name: 'Free',
    price: '$0',
    period: '/month',
    desc: 'Perfect for trying out the API',
    icon: Zap,
    features: ['100 requests/day', 'All 166+ endpoints', 'Community support', 'Standard rate limits'],
    cta: 'Get Started',
    popular: false,
  },
  {
    name: 'Starter',
    price: '$29',
    period: '/month',
    desc: 'For indie developers & small apps',
    icon: Star,
    features: ['1,000 requests/day', 'All 166+ endpoints', 'Email support', '99.5% SLA', 'Usage analytics'],
    cta: 'Start Free Trial',
    popular: false,
  },
  {
    name: 'Pro',
    price: '$99',
    period: '/month',
    desc: 'For growing businesses',
    icon: Crown,
    features: ['10,000 requests/day', 'All 166+ endpoints', 'Priority support', '99.9% SLA', 'Webhooks', 'Custom rate limits'],
    cta: 'Start Free Trial',
    popular: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    desc: 'For large-scale deployments',
    icon: Star,
    features: ['Unlimited requests', 'All 166+ endpoints', 'Dedicated support', '99.99% SLA', 'Custom endpoints', 'On-premise option', 'SLA contract'],
    cta: 'Contact Sales',
    popular: false,
  },
]

const faqs = [
  { q: 'What counts as a request?', a: 'Each API call to any endpoint counts as one request, regardless of the response size.' },
  { q: 'Can I change plans anytime?', a: 'Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately.' },
  { q: 'Is there a free trial for paid plans?', a: 'Yes! Both Starter and Pro plans come with a 14-day free trial.' },
  { q: 'What happens if I exceed my limit?', a: 'You\'ll receive a 429 status code. Upgrade your plan or wait for the daily reset.' },
  { q: 'Do you offer refunds?', a: 'We offer a full refund within 7 days of purchase if you\'re not satisfied.' },
]

export default function Pricing() {
  const [openFaq, setOpenFaq] = useState(null)
  const navigate = useNavigate()

  return (
    <div style={{ paddingTop: 100 }}>
      <section className="section" style={{ paddingBottom: 40 }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="section-title">
            Simple, Transparent <span className="gradient-text">Pricing</span>
          </h1>
          <p className="section-subtitle">
            Start free, scale as you grow. No hidden fees, no surprises.
          </p>
        </motion.div>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: 24,
            maxWidth: 1100,
            margin: '0 auto',
          }}
        >
          {tiers.map((tier, i) => (
            <motion.div
              key={tier.name}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              style={{
                background: 'var(--bg-card)',
                border: tier.popular
                  ? '2px solid rgba(124,58,237,0.5)'
                  : '1px solid var(--border-color)',
                borderRadius: 'var(--radius-lg)',
                padding: 32,
                position: 'relative',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              {tier.popular && (
                <div
                  style={{
                    position: 'absolute',
                    top: -12,
                    left: '50%',
                    transform: 'translateX(-50%)',
                    background: 'var(--gradient-primary)',
                    color: 'white',
                    padding: '4px 16px',
                    borderRadius: 20,
                    fontSize: 12,
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: 1,
                  }}
                >
                  Most Popular
                </div>
              )}

              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 12,
                  background: 'rgba(124,58,237,0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: 16,
                }}
              >
                <tier.icon size={22} color="#a78bfa" />
              </div>

              <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>{tier.name}</h3>
              <p style={{ color: '#64748b', fontSize: 14, marginBottom: 16 }}>{tier.desc}</p>

              <div style={{ display: 'flex', alignItems: 'baseline', marginBottom: 24 }}>
                <span style={{ fontSize: 40, fontWeight: 900 }}>{tier.price}</span>
                {tier.period && (
                  <span style={{ color: '#64748b', fontSize: 15, marginLeft: 4 }}>{tier.period}</span>
                )}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 32, flex: 1 }}>
                {tier.features.map((f) => (
                  <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <Check size={16} color="#22c55e" />
                    <span style={{ color: '#cbd5e1', fontSize: 14 }}>{f}</span>
                  </div>
                ))}
              </div>

              <button
                onClick={() => navigate('/register')}
                className={tier.popular ? 'btn-primary' : 'btn-secondary'}
                style={{ width: '100%', justifyContent: 'center' }}
              >
                {tier.cta}
                <ArrowRight size={16} />
              </button>
            </motion.div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="section">
        <h2 className="section-title">
          Frequently Asked <span className="gradient-text">Questions</span>
        </h2>
        <p className="section-subtitle">Everything you need to know about our pricing.</p>

        <div style={{ maxWidth: 700, margin: '0 auto' }}>
          {faqs.map((faq, i) => (
            <div
              key={i}
              style={{
                borderBottom: '1px solid var(--border-color)',
              }}
            >
              <button
                onClick={() => setOpenFaq(openFaq === i ? null : i)}
                style={{
                  width: '100%',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '20px 0',
                  background: 'none',
                  color: '#e2e8f0',
                  fontSize: 16,
                  fontWeight: 600,
                  textAlign: 'left',
                }}
              >
                {faq.q}
                <span
                  style={{
                    color: '#7c3aed',
                    fontSize: 20,
                    transition: 'transform 0.2s',
                    transform: openFaq === i ? 'rotate(45deg)' : 'none',
                  }}
                >
                  +
                </span>
              </button>
              {openFaq === i && (
                <motion.p
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  style={{ color: '#94a3b8', fontSize: 15, paddingBottom: 20, lineHeight: 1.7 }}
                >
                  {faq.a}
                </motion.p>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
