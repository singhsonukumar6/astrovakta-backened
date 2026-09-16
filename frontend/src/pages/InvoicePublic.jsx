import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Printer, Globe, Check } from 'lucide-react'
import { getPublicInvoice } from '../lib/api.js'
import DashboardLoader from '../components/DashboardLoader.jsx'

// Public, client-facing invoice behind the shareable /invoice/<token> link.
// White-label: the astrologer's brand only, printable on paper (A4).
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const fmtDate = (iso) => {
  if (!iso) return '—'
  const d = new Date(String(iso).slice(0, 10) + 'T00:00:00')
  if (Number.isNaN(d.getTime())) return String(iso)
  return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`
}

export default function InvoicePublic() {
  const { token } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getPublicInvoice(token)
      .then((d) => (d?.invoice ? setData(d) : setError('not_found')))
      .catch(() => setError('not_found'))
  }, [token])

  useEffect(() => { document.title = data ? `Invoice ${data.invoice.number}` : 'Invoice' }, [data])

  if (error) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 14, background: '#f6f6f9', color: '#18181b' }}>
        <Globe size={44} color="#a1a1aa" />
        <h2 style={{ fontSize: 21, fontWeight: 800, margin: 0 }}>Invoice not found</h2>
        <p style={{ color: '#71717a', fontSize: 14, margin: 0 }}>This link is invalid or the invoice was removed.</p>
      </div>
    )
  }
  if (!data) {
    return <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f6f6f9' }}>
      <DashboardLoader label="Loading invoice" size={44} />
    </div>
  }

  const { invoice: inv, site } = data
  const theme = site.theme || {}
  const accent = theme.primaryColor || '#4f46e5'
  const contact = site.contact || {}
  const symbol = inv.currency === 'INR' ? '₹' : `${inv.currency || ''} `

  return (
    <div style={{ minHeight: '100vh', background: '#f6f6f9', padding: '32px 16px', fontFamily: "'Inter', -apple-system, system-ui, sans-serif", color: '#18181b' }}>
      {/* toolbar (hidden when printing) */}
      <div className="no-print" style={{ maxWidth: 800, margin: '0 auto 18px', display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
        <button onClick={() => window.print()} style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 20px', borderRadius: 10, border: 'none', background: accent, color: '#fff', fontWeight: 700, fontSize: 14, cursor: 'pointer' }}>
          <Printer size={15} /> Print / Save PDF
        </button>
      </div>

      {/* the invoice sheet */}
      <div style={{
        maxWidth: 800, margin: '0 auto', background: '#fff', borderRadius: 18,
        boxShadow: '0 12px 44px rgba(24,24,27,0.09)', overflow: 'hidden',
      }}>
        {/* brand band */}
        <div style={{ background: `linear-gradient(135deg, ${accent}, ${theme.accentColor || '#d97706'})`, padding: '34px 40px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            {site.logo_url
              ? <img src={site.logo_url} alt={site.name} style={{ width: 54, height: 54, borderRadius: 14, objectFit: 'cover', border: '2px solid rgba(255,255,255,0.5)' }} />
              : <div style={{ width: 54, height: 54, borderRadius: 14, background: 'rgba(255,255,255,0.2)', color: '#fff', fontSize: 22, fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {(site.name || 'A').trim().charAt(0).toUpperCase()}
                </div>}
            <div>
              <div style={{ color: '#fff', fontSize: 21, fontWeight: 800, letterSpacing: -0.3 }}>{site.name}</div>
              {site.tagline && <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: 12.5, marginTop: 2 }}>{site.tagline}</div>}
            </div>
          </div>
          <div style={{ textAlign: 'right', color: '#fff' }}>
            <div style={{ fontSize: 26, fontWeight: 800, letterSpacing: 2 }}>INVOICE</div>
            <div style={{ fontSize: 13, opacity: 0.85, marginTop: 2 }}>{inv.number}</div>
          </div>
        </div>

        <div style={{ padding: '30px 40px 36px' }}>
          {/* meta + bill-to */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 22, marginBottom: 28 }}>
            <div>
              <div style={labelSm}>Billed to</div>
              <div style={{ fontWeight: 800, fontSize: 15.5, marginTop: 6 }}>{inv.client_name}</div>
              {inv.client_email && <div style={{ fontSize: 13, color: '#71717a', marginTop: 2 }}>{inv.client_email}</div>}
              {inv.client_phone && <div style={{ fontSize: 13, color: '#71717a' }}>{inv.client_phone}</div>}
            </div>
            <div>
              <div style={labelSm}>Issued</div>
              <div style={{ fontSize: 14.5, fontWeight: 600, marginTop: 6 }}>{fmtDate(inv.created_at)}</div>
            </div>
            <div>
              <div style={labelSm}>Due</div>
              <div style={{ fontSize: 14.5, fontWeight: 600, marginTop: 6 }}>{inv.due_date ? fmtDate(inv.due_date) : 'On receipt'}</div>
            </div>
            <div>
              <div style={labelSm}>Status</div>
              <div style={{ marginTop: 8 }}>
                {inv.status === 'paid' ? (
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: 'rgba(34,197,94,0.12)', color: '#16a34a', fontWeight: 800, fontSize: 13, padding: '6px 14px', borderRadius: 999 }}>
                    <Check size={14} /> PAID
                  </span>
                ) : (
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: inv.status === 'sent' ? 'rgba(59,130,246,0.1)' : 'rgba(148,163,184,0.15)', color: inv.status === 'sent' ? '#2563eb' : '#64748b', fontWeight: 800, fontSize: 13, padding: '6px 14px', borderRadius: 999, textTransform: 'uppercase' }}>
                    {inv.status === 'sent' ? 'Awaiting payment' : 'Draft'}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* items */}
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Description', 'Qty', 'Price', 'Amount'].map((h, i) => (
                  <th key={h} style={{ ...th, textAlign: i === 0 ? 'left' : 'right' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(inv.items || []).map((it, i) => (
                <tr key={i}>
                  <td style={{ ...td, fontWeight: 600 }}>{it.name}</td>
                  <td style={{ ...td, textAlign: 'right', color: '#71717a' }}>{it.qty}</td>
                  <td style={{ ...td, textAlign: 'right', color: '#71717a' }}>{symbol}{it.price}</td>
                  <td style={{ ...td, textAlign: 'right', fontWeight: 700 }}>{symbol}{(it.price || 0) * (it.qty || 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* totals */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 18 }}>
            <div style={{ width: 280 }}>
              <div style={totalRow}><span style={{ color: '#71717a' }}>Subtotal</span><b>{symbol}{inv.subtotal}</b></div>
              {inv.tax_rate ? <div style={totalRow}><span style={{ color: '#71717a' }}>Tax ({inv.tax_rate}%)</span><b>{symbol}{inv.tax_amount}</b></div> : null}
              <div style={{ ...totalRow, borderTop: '2px solid #18181b', paddingTop: 12, fontSize: 17 }}>
                <span>Total</span><b>{symbol}{inv.total}</b>
              </div>
            </div>
          </div>

          {/* notes + payment + contact */}
          {(inv.notes || contact.upiNumber || contact.phone || contact.email || contact.city) && (
            <div style={{ marginTop: 30, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 18 }}>
              {inv.notes && (
                <div style={{ background: '#fafafc', border: '1px solid #ececf3', borderRadius: 12, padding: '14px 16px' }}>
                  <div style={labelSm}>Notes</div>
                  <div style={{ fontSize: 13.5, color: '#3f3f46', lineHeight: 1.65, marginTop: 5 }}>{inv.notes}</div>
                </div>
              )}
              <div style={{ background: '#fafafc', border: '1px solid #ececf3', borderRadius: 12, padding: '14px 16px' }}>
                <div style={labelSm}>Contact</div>
                <div style={{ fontSize: 13.5, color: '#3f3f46', lineHeight: 1.8, marginTop: 5 }}>
                  {contact.phone && <div>{contact.phone}</div>}
                  {contact.email && <div>{contact.email}</div>}
                  {contact.city && <div>{contact.city}</div>}
                </div>
              </div>
            </div>
          )}

          <div style={{ marginTop: 30, paddingTop: 18, borderTop: '1px solid #ececf3', fontSize: 12, color: '#a1a1aa', textAlign: 'center', lineHeight: 1.7 }}>
            Thank you for your business — {site.name}
          </div>
        </div>
      </div>

      {/* print styling: only the sheet, on white */}
      <style>{`
        @media print {
          body { background: #fff !important; }
          .no-print { display: none !important; }
          @page { size: A4; margin: 12mm; }
        }
      `}</style>
    </div>
  )
}

const labelSm = { fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.8, color: '#a1a1aa' }
const th = { fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.6, color: '#71717a', padding: '10px 8px', borderBottom: '2px solid #e4e4e7' }
const td = { padding: '13px 8px', fontSize: 14, borderBottom: '1px solid #f1f1f4' }
const totalRow = { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '7px 0', fontSize: 14.5 }
