import { useEffect, useState } from 'react'
import { Plus, Trash2, Loader2, Save, X } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../lib/api.js'

const inputStyle = { width: '100%', padding: '10px 12px', border: '1px solid #e2e8f0', borderRadius: 10, fontSize: 14, outline: 'none', background: '#fff' }
const labelStyle = { display: 'block', fontSize: 12.5, fontWeight: 700, color: '#475569', marginBottom: 5 }

// Master dropshipping catalog: categories + products (MRP, margin, multi-image).
export default function MasterCatalogAdmin() {
  const [categories, setCategories] = useState([])
  const [products, setProducts] = useState([])
  const [newCat, setNewCat] = useState('')
  const [editing, setEditing] = useState(null) // null | product object being created/edited
  const [busy, setBusy] = useState(false)

  const [loadError, setLoadError] = useState(null)
  const load = () => {
    setLoadError(null)
    Promise.all([
      api.get('/sites/admin/master/categories'),
      api.get('/sites/admin/master/products'),
    ]).then(([c, pr]) => {
      setCategories(c.data?.categories ?? c.data?.data?.categories ?? [])
      setProducts(pr.data?.products ?? pr.data?.data?.products ?? [])
    }).catch((e) => {
      setLoadError(e.response?.status === 403
        ? 'Admin access required — your account is not marked as an admin.'
        : e.response?.data?.detail || 'Could not load the catalog')
    })
  }
  useEffect(() => { load() }, [])

  const addCategory = async () => {
    if (!newCat.trim()) return
    setBusy(true)
    try { await api.post('/sites/admin/master/categories', { name: newCat.trim() }); setNewCat(''); load() }
    catch (e) { toast.error(e.response?.data?.detail || 'Failed') } finally { setBusy(false) }
  }

  const delCategory = async (id) => {
    try { await api.delete(`/sites/admin/master/categories/${id}`); load() } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
  }

  const blank = () => ({ id: null, name: '', category_id: categories[0]?.id ?? null, description: '', images: [], mrp: 0, margin: 0 })

  const save = async () => {
    if (!editing.name.trim()) return toast.error('Product name is required')
    if (!editing.images.length) return toast.error('Add at least one product image')
    setBusy(true)
    try {
      if (editing.id) await api.put(`/sites/admin/master/products/${editing.id}`, editing)
      else await api.post('/sites/admin/master/products', editing)
      toast.success('Saved')
      setEditing(null); load()
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to save') }
    finally { setBusy(false) }
  }

  const delProduct = async (id) => {
    try { await api.delete(`/sites/admin/master/products/${id}`); load() } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
  }

  const addImageFromUrl = () => {
    const url = window.prompt('Image URL:')
    if (url && url.trim()) setEditing({ ...editing, images: [...editing.images, url.trim()] })
  }

  const addImageFromFile = (file) => {
    if (!file) return
    if (file.size > 900_000) { toast.error('Image too large — use an image under 900 KB or paste a URL'); return }
    const reader = new FileReader()
    reader.onload = () => setEditing((ed) => ({ ...ed, images: [...ed.images, reader.result] }))
    reader.readAsDataURL(file)
  }

  if (loadError) {
    return (
      <div style={{ background: '#fff', border: '1px solid #fecaca', borderRadius: 14, padding: 28 }}>
        <h3 style={{ fontSize: 16, fontWeight: 800, color: '#dc2626', marginBottom: 6 }}>Catalog unavailable</h3>
        <div style={{ fontSize: 14, color: '#64748b' }}>{loadError}</div>
      </div>
    )
  }

  return (
    <div>
      {/* categories */}
      <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 14, padding: 20, marginBottom: 20 }}>
        <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 10 }}>Categories</h3>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
          {categories.map((c) => (
            <span key={c.id} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#f1f5f9', borderRadius: 999, padding: '6px 12px', fontSize: 13, fontWeight: 600 }}>
              {c.name}
              <button onClick={() => delCategory(c.id)} style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', padding: 0 }}><X size={13} /></button>
            </span>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <input value={newCat} onChange={(e) => setNewCat(e.target.value)} placeholder="New category (Gemstones, Rudraksha, Bracelets…)" style={inputStyle} />
          <button onClick={addCategory} disabled={busy} className="btn-primary" style={{ padding: '10px 16px', borderRadius: 10, border: 'none', background: '#4f46e5', color: '#fff', fontWeight: 700, cursor: 'pointer', whiteSpace: 'nowrap' }}>
            <Plus size={14} style={{ verticalAlign: '-2px' }} /> Add
          </button>
        </div>
      </div>

      {/* products list */}
      <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 14, padding: 20, marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h3 style={{ fontSize: 16, fontWeight: 800 }}>Master products ({products.length})</h3>
          <button onClick={() => setEditing(blank())} className="btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '9px 16px', borderRadius: 10, border: 'none', background: '#4f46e5', color: '#fff', fontWeight: 700, cursor: 'pointer' }}>
            <Plus size={15} /> New product
          </button>
        </div>
        {products.map((p) => (
          <div key={p.id} style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '10px 0', borderBottom: '1px solid #f1f5f9' }}>
            {p.images?.[0] ? <img src={p.images[0]} alt="" style={{ width: 46, height: 46, borderRadius: 8, objectFit: 'cover' }} />
              : <div style={{ width: 46, height: 46, borderRadius: 8, background: '#f1f5f9' }} />}
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: 13.5 }}>{p.name} <span style={{ color: '#94a3b8', fontWeight: 600, fontSize: 11.5 }}>{p.category_name}</span></div>
              <div style={{ fontSize: 12, color: '#64748b' }}>MRP ₹{p.mrp} · margin ₹{p.margin} · tenant cost ₹{Math.max(0, p.mrp - p.margin)}</div>
            </div>
            <button onClick={() => setEditing({ ...p, images: p.images || [] })} style={{ background: 'none', border: '1px solid #e2e8f0', borderRadius: 8, padding: '5px 10px', cursor: 'pointer', fontSize: 12.5, fontWeight: 700 }}>Edit</button>
            <button onClick={() => delProduct(p.id)} style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer' }}><Trash2 size={15} /></button>
          </div>
        ))}
      </div>

      {/* editor */}
      {editing && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.5)', zIndex: 200, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', overflowY: 'auto', padding: '40px 16px' }}>
          <div style={{ background: '#fff', borderRadius: 18, width: '100%', maxWidth: 640, padding: 26 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ fontSize: 18, fontWeight: 800 }}>{editing.id ? 'Edit product' : 'New master product'}</h3>
              <button onClick={() => setEditing(null)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}><X size={20} /></button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
              <div>
                <label style={labelStyle}>Product name *</label>
                <input value={editing.name} onChange={(e) => setEditing({ ...editing, name: e.target.value })} placeholder="Yellow Sapphire 5ct Certified" style={inputStyle} />
              </div>
              <div>
                <label style={labelStyle}>Category</label>
                <select value={editing.category_id ?? ''} onChange={(e) => setEditing({ ...editing, category_id: Number(e.target.value) || null })} style={inputStyle}>
                  <option value="">—</option>
                  {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label style={labelStyle}>MRP (₹) — what the buyer pays *</label>
                <input type="number" value={editing.mrp} onChange={(e) => setEditing({ ...editing, mrp: Number(e.target.value) })} style={inputStyle} />
              </div>
              <div>
                <label style={labelStyle}>Your margin (₹) — tenant pays MRP − margin</label>
                <input type="number" value={editing.margin} onChange={(e) => setEditing({ ...editing, margin: Number(e.target.value) })} style={inputStyle} />
              </div>
            </div>
            <div style={{ marginBottom: 12 }}>
              <label style={labelStyle}>Description</label>
              <textarea value={editing.description || ''} onChange={(e) => setEditing({ ...editing, description: e.target.value })}
                rows={4} placeholder="Certification, weight, benefits, wearing instructions — this sells the product on the astrologer's store."
                style={{ ...inputStyle, resize: 'vertical', fontFamily: 'inherit', lineHeight: 1.6 }} />
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={labelStyle}>Images (first one is the main photo)</label>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 8 }}>
                {(editing.images || []).map((img, i) => (
                  <div key={i} style={{ position: 'relative' }}>
                    <img src={img} alt="" style={{ width: 72, height: 72, objectFit: 'cover', borderRadius: 10, border: i === 0 ? '2px solid #4f46e5' : '1px solid #e2e8f0' }} />
                    <button onClick={() => setEditing({ ...editing, images: editing.images.filter((_, j) => j !== i) })}
                      style={{ position: 'absolute', top: -6, right: -6, width: 20, height: 20, borderRadius: '50%', border: 'none', background: '#dc2626', color: '#fff', cursor: 'pointer', fontSize: 11 }}>×</button>
                    {i === 0 && <span style={{ position: 'absolute', bottom: 3, left: 3, fontSize: 8.5, fontWeight: 800, background: '#4f46e5', color: '#fff', borderRadius: 4, padding: '1px 4px' }}>MAIN</span>}
                  </div>
                ))}
                <label style={{ width: 72, height: 72, borderRadius: 10, border: '2px dashed #cbd5e1', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: '#94a3b8' }}>
                  <Plus size={20} />
                  <input type="file" accept="image/*" style={{ display: 'none' }} onChange={(e) => addImageFromFile(e.target.files?.[0])} />
                </label>
              </div>
              <button type="button" onClick={addImageFromUrl} style={{ background: 'none', border: 'none', color: '#4f46e5', fontWeight: 700, fontSize: 12.5, cursor: 'pointer', padding: 0 }}>
                + Add image from URL
              </button>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button onClick={save} disabled={busy} style={{ flex: 1, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8, padding: 13, borderRadius: 10, border: 'none', background: '#4f46e5', color: '#fff', fontWeight: 800, fontSize: 14.5, cursor: 'pointer' }}>
                {busy ? <Loader2 size={15} className="spin" /> : <Save size={15} />} Save product
              </button>
              <button onClick={() => setEditing(null)} style={{ padding: 13, borderRadius: 10, border: '1px solid #e2e8f0', background: '#fff', fontWeight: 700, cursor: 'pointer' }}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
