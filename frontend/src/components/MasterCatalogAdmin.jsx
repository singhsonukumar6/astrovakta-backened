import { useEffect, useState } from 'react'
import { Plus, Trash2, Loader2, Save, X, ChevronLeft, Package, FolderOpen } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../lib/api.js'

const inputStyle = { width: '100%', padding: '10px 12px', border: '1px solid #cbd5e1', borderRadius: 10, fontSize: 14, outline: 'none', background: '#fff', color: '#0f172a', colorScheme: 'light' }
const labelStyle = { display: 'block', fontSize: 12.5, fontWeight: 700, color: '#475569', marginBottom: 5 }
const btnPrimary = { display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 18px', borderRadius: 10, border: 'none', background: '#4f46e5', color: '#fff', fontWeight: 700, fontSize: 14, cursor: 'pointer' }
const btnGhost = { display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 18px', borderRadius: 10, border: '1px solid #e2e8f0', background: '#fff', color: '#0f172a', fontWeight: 700, fontSize: 14, cursor: 'pointer' }
const card = { background: '#fff', border: '1px solid #e2e8f0', borderRadius: 14, padding: 20 }

const isVideo = (src) => /\.(mp4|webm|mov)(\?|$)/i.test(src) || (src || '').startsWith('data:video')

// ═══════════ CATEGORIES PAGE ═══════════
function CategoriesPage({ onBack }) {
  const [cats, setCats] = useState(null)
  const [name, setName] = useState('')
  const [order, setOrder] = useState(0)
  const [editing, setEditing] = useState(null)
  const [busy, setBusy] = useState(false)

  const load = () => api.get('/sites/admin/master/categories')
    .then((r) => setCats(r.data?.categories ?? r.data?.data?.categories ?? []))
    .catch(() => setCats([]))
  useEffect(() => { load() }, [])

  const save = async () => {
    if (!name.trim()) return toast.error('Category name is required')
    setBusy(true)
    try {
      if (editing) await api.put(`/sites/admin/master/categories/${editing.id}`, { name: name.trim(), sort_order: order })
      else await api.post('/sites/admin/master/categories', { name: name.trim(), sort_order: order })
      toast.success(editing ? 'Category updated' : 'Category added')
      setName(''); setOrder(0); setEditing(null); load()
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
    finally { setBusy(false) }
  }

  return (
    <div style={{ colorScheme: 'light', color: '#0f172a' }}>
      <button onClick={onBack} style={{ ...btnGhost, marginBottom: 16, padding: '8px 14px', fontSize: 13 }}>
        <ChevronLeft size={15} /> Back to products
      </button>
      <div style={{ ...card, marginBottom: 20 }}>
        <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
          <FolderOpen size={17} color="#4f46e5" /> {editing ? 'Edit category' : 'Add category'}
        </h3>
        <p style={{ fontSize: 13, color: '#64748b', marginBottom: 14, lineHeight: 1.6 }}>
          Categories organise the master catalog — gemstones, rudraksha, bracelets, healing puja and whatever else you add. Tenants see these groupings when importing.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr auto', gap: 10 }}>
          <div>
            <label style={labelStyle}>Category name *</label>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Gemstones, Rudraksha, Healing Puja" style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>Sort order</label>
            <input type="number" value={order} onChange={(e) => setOrder(Number(e.target.value))} style={inputStyle} />
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button onClick={save} disabled={busy} style={btnPrimary}>
              {busy ? <Loader2 size={15} className="spin" /> : <Plus size={15} />} {editing ? 'Update' : 'Add'}
            </button>
          </div>
        </div>
        {editing && (
          <button onClick={() => { setEditing(null); setName(''); setOrder(0) }} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: 12.5, textDecoration: 'underline', marginTop: 8, padding: 0 }}>
            Cancel edit
          </button>
        )}
      </div>
      <div style={{ ...card }}>
        <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 12 }}>All categories ({(cats || []).length})</h3>
        {!cats ? <div style={{ color: '#64748b' }}>Loading…</div> : cats.length === 0 ? (
          <div style={{ color: '#64748b', fontSize: 14, textAlign: 'center', padding: 24 }}>No categories yet — add your first above.</div>
        ) : cats.map((c) => (
          <div key={c.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '11px 0', borderBottom: '1px solid #f1f5f9' }}>
            <span style={{ width: 34, height: 34, borderRadius: 9, background: 'rgba(79,70,229,0.08)', color: '#4f46e5', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 13 }}>#{(c.sort_order ?? 0) + 1}</span>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: 14.5 }}>{c.name}</div>
              <div style={{ fontSize: 12, color: '#94a3b8' }}>/{c.slug}</div>
            </div>
            <button onClick={() => { setEditing(c); setName(c.name); setOrder(c.sort_order ?? 0) }} style={{ background: 'none', border: '1px solid #e2e8f0', borderRadius: 8, padding: '5px 12px', cursor: 'pointer', fontSize: 12.5, fontWeight: 700 }}>Edit</button>
            <button onClick={async () => {
              if (!window.confirm(`Delete "${c.name}"? Products keep existing but lose the grouping.`)) return
              try { await api.delete(`/sites/admin/master/categories/${c.id}`); load() } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
            }} style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer' }}><Trash2 size={15} /></button>
          </div>
        ))}
      </div>
    </div>
  )
}

// ═══════════ PRODUCTS PAGE ═══════════
function ProductsPage({ categories, onManageCategories }) {
  const [products, setProducts] = useState(null)
  const [editing, setEditing] = useState(null)
  const [busy, setBusy] = useState(false)

  const load = () => api.get('/sites/admin/master/products')
    .then((r) => setProducts(r.data?.products ?? r.data?.data?.products ?? []))
    .catch(() => setProducts([]))
  useEffect(() => { load() }, [])

  const blank = () => ({ id: null, name: '', category_id: categories[0]?.id ?? null, description: '',
    images: [], attributes: [{ name: 'Weight', value: '' }, { name: 'Origin', value: '' }], mrp: 0, margin: 0 })

  const save = async () => {
    if (!editing.name.trim()) return toast.error('Product name is required')
    if (!editing.images.length) return toast.error('Add at least one image')
    setBusy(true)
    try {
      const payload = { ...editing, attributes: (editing.attributes || []).filter((a) => a.name && String(a.value).trim()) }
      if (editing.id) await api.put(`/sites/admin/master/products/${editing.id}`, payload)
      else await api.post('/sites/admin/master/products', payload)
      toast.success('Saved'); setEditing(null); load()
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to save') }
    finally { setBusy(false) }
  }

  const addMediaUrl = () => {
    const url = window.prompt('Image or video URL:')
    if (url && url.trim()) setEditing({ ...editing, images: [...editing.images, url.trim()] })
  }
  const addMediaFile = (file) => {
    if (!file) return
    if (file.size > 4_000_000) { toast.error('File too large (max ~4 MB) — use a URL for big videos'); return }
    if (file.type.startsWith('video/') && file.size > 2_000_000) { toast.error('Videos over 2 MB must be added by URL'); return }
    const reader = new FileReader()
    reader.onload = () => setEditing((ed) => ({ ...ed, images: [...ed.images, reader.result] }))
    reader.readAsDataURL(file)
  }

  return (
    <div style={{ colorScheme: 'light', color: '#0f172a' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 8 }}>
        <h3 style={{ fontSize: 17, fontWeight: 800, display: 'flex', alignItems: 'center', gap: 8 }}><Package size={18} color="#4f46e5" /> Master products ({(products || []).length})</h3>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={onManageCategories} style={{ ...btnGhost, padding: '9px 14px', fontSize: 13 }}><FolderOpen size={14} /> Manage categories</button>
          <button onClick={() => setEditing(blank())} style={{ ...btnPrimary, padding: '9px 14px', fontSize: 13 }}><Plus size={15} /> Add product</button>
        </div>
      </div>
      <div style={{ ...card }}>
        {!products ? <div style={{ color: '#64748b' }}>Loading…</div> : products.length === 0 ? (
          <div style={{ color: '#64748b', fontSize: 14, textAlign: 'center', padding: 24 }}>No products yet — add your first.</div>
        ) : products.map((p) => (
          <div key={p.id} style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '10px 0', borderBottom: '1px solid #f1f5f9' }}>
            {p.images?.[0]
              ? (isVideo(p.images[0])
                  ? <video src={p.images[0]} style={{ width: 46, height: 46, borderRadius: 8, objectFit: 'cover' }} muted />
                  : <img src={p.images[0]} alt="" style={{ width: 46, height: 46, borderRadius: 8, objectFit: 'cover' }} />)
              : <div style={{ width: 46, height: 46, borderRadius: 8, background: '#f1f5f9' }} />}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 700, fontSize: 13.5, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {p.name} <span style={{ color: '#94a3b8', fontWeight: 600, fontSize: 11.5 }}>{p.category_name}</span>
              </div>
              <div style={{ fontSize: 12, color: '#64748b' }}>
                MRP ₹{p.mrp} · margin ₹{p.margin} · tenant cost ₹{Math.max(0, p.mrp - p.margin)}
                {!!(p.attributes?.length) && ` · ${p.attributes.length} properties`}
              </div>
            </div>
            <button onClick={() => setEditing({ ...p, images: p.images || [], attributes: p.attributes?.length ? p.attributes : [{ name: 'Weight', value: '' }] })} style={{ background: 'none', border: '1px solid #e2e8f0', borderRadius: 8, padding: '5px 12px', cursor: 'pointer', fontSize: 12.5, fontWeight: 700 }}>Edit</button>
            <button onClick={async () => {
              if (!window.confirm('Delete this product?')) return
              try { await api.delete(`/sites/admin/master/products/${p.id}`); load() } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
            }} style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer' }}><Trash2 size={15} /></button>
          </div>
        ))}
      </div>

      {editing && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.5)', zIndex: 200, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', overflowY: 'auto', padding: '36px 16px' }} onClick={(e) => e.target === e.currentTarget && setEditing(null)}>
          <div style={{ background: '#fff', borderRadius: 18, width: '100%', maxWidth: 680, padding: 26 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ fontSize: 18, fontWeight: 800 }}>{editing.id ? 'Edit product' : 'Add product'}</h3>
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
                  <option value="">— none —</option>
                  {categories.map((c) => <option key={c.id} value={c.id} style={{ color: '#0f172a', background: '#fff' }}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label style={labelStyle}>MRP (₹) — buyer pays *</label>
                <input type="number" value={editing.mrp} onChange={(e) => setEditing({ ...editing, mrp: Number(e.target.value) })} style={inputStyle} />
              </div>
              <div>
                <label style={labelStyle}>Your margin (₹)</label>
                <input type="number" value={editing.margin} onChange={(e) => setEditing({ ...editing, margin: Number(e.target.value) })} style={inputStyle} />
              </div>
            </div>
            <div style={{ marginBottom: 12 }}>
              <label style={labelStyle}>Description</label>
              <textarea value={editing.description || ''} onChange={(e) => setEditing({ ...editing, description: e.target.value })} rows={4}
                placeholder="Certification, benefits, wearing instructions, who should wear it…"
                style={{ ...inputStyle, resize: 'vertical', fontFamily: 'inherit', lineHeight: 1.6 }} />
            </div>

            <div style={{ marginBottom: 14 }}>
              <label style={labelStyle}>Custom properties & dimensions</label>
              {(editing.attributes || []).map((a, i) => (
                <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr auto', gap: 8, marginBottom: 8 }}>
                  <input value={a.name} onChange={(e) => setEditing({ ...editing, attributes: editing.attributes.map((x, j) => j === i ? { ...x, name: e.target.value } : x) })}
                    placeholder="Property (Weight, Size, Metal…)" style={inputStyle} />
                  <input value={a.value} onChange={(e) => setEditing({ ...editing, attributes: editing.attributes.map((x, j) => j === i ? { ...x, value: e.target.value } : x) })}
                    placeholder="Value (5.25 carat, 18 mm…)" style={inputStyle} />
                  <button type="button" onClick={() => setEditing({ ...editing, attributes: editing.attributes.filter((_, j) => j !== i) })}
                    style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer' }}><X size={15} /></button>
                </div>
              ))}
              <button type="button" onClick={() => setEditing({ ...editing, attributes: [...(editing.attributes || []), { name: '', value: '' }] })}
                style={{ background: 'none', border: 'none', color: '#4f46e5', fontWeight: 700, fontSize: 12.5, cursor: 'pointer', padding: 0 }}>
                + Add property
              </button>
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={labelStyle}>Images & videos (first image is the main photo)</label>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 8 }}>
                {(editing.images || []).map((src, i) => (
                  <div key={i} style={{ position: 'relative' }}>
                    {isVideo(src)
                      ? <video src={src} style={{ width: 72, height: 72, borderRadius: 10, objectFit: 'cover', border: '1px solid #e2e8f0', background: '#0f172a' }} muted />
                      : <img src={src} alt="" style={{ width: 72, height: 72, objectFit: 'cover', borderRadius: 10, border: i === 0 ? '2px solid #4f46e5' : '1px solid #e2e8f0' }} />}
                    {i === 0 && !isVideo(src) && <span style={{ position: 'absolute', bottom: 3, left: 3, fontSize: 8.5, fontWeight: 800, background: '#4f46e5', color: '#fff', borderRadius: 4, padding: '1px 4px' }}>MAIN</span>}
                    <button onClick={() => setEditing({ ...editing, images: editing.images.filter((_, j) => j !== i) })}
                      style={{ position: 'absolute', top: -6, right: -6, width: 20, height: 20, borderRadius: '50%', border: 'none', background: '#dc2626', color: '#fff', cursor: 'pointer', fontSize: 11 }}>×</button>
                  </div>
                ))}
                <label style={{ width: 72, height: 72, borderRadius: 10, border: '2px dashed #cbd5e1', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: '#94a3b8', fontSize: 9, fontWeight: 700, gap: 2 }}>
                  <Plus size={18} /> UPLOAD
                  <input type="file" accept="image/*,video/mp4,video/webm" style={{ display: 'none' }} onChange={(e) => addMediaFile(e.target.files?.[0])} />
                </label>
              </div>
              <button type="button" onClick={addMediaUrl} style={{ background: 'none', border: 'none', color: '#4f46e5', fontWeight: 700, fontSize: 12.5, cursor: 'pointer', padding: 0 }}>
                + Add image/video from URL (recommended for videos)
              </button>
            </div>

            <div style={{ display: 'flex', gap: 10 }}>
              <button onClick={save} disabled={busy} style={{ ...btnPrimary, flex: 1, justifyContent: 'center', padding: 13, fontSize: 14.5 }}>
                {busy ? <Loader2 size={15} className="spin" /> : <Save size={15} />} Save product
              </button>
              <button onClick={() => setEditing(null)} style={{ ...btnGhost, padding: 13 }}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ═══════════ ROOT: routes between the pages ═══════════
export default function MasterCatalogAdmin() {
  const [categories, setCategories] = useState([])
  const [page, setPage] = useState('products')
  const [loadError, setLoadError] = useState(null)

  const loadCats = () => api.get('/sites/admin/master/categories')
    .then((r) => setCategories(r.data?.categories ?? r.data?.data?.categories ?? []))
    .catch((e) => setLoadError(e.response?.status === 403
      ? 'Admin access required — your account is not marked as an admin.'
      : e.response?.data?.detail || 'Could not load the catalog'))
  useEffect(() => { loadCats() }, [])

  if (loadError) {
    return (
      <div style={{ background: '#fff', border: '1px solid #fecaca', borderRadius: 14, padding: 28, colorScheme: 'light' }}>
        <h3 style={{ fontSize: 16, fontWeight: 800, color: '#dc2626', marginBottom: 6 }}>Catalog unavailable</h3>
        <div style={{ fontSize: 14, color: '#64748b' }}>{loadError}</div>
      </div>
    )
  }

  return (
    <div style={{ colorScheme: 'light', color: '#0f172a' }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 18 }}>
        {[['products', 'Products', Package], ['categories', 'Categories', FolderOpen]].map(([id, label, Icon]) => (
          <button key={id} onClick={() => setPage(id)} style={{
            display: 'inline-flex', alignItems: 'center', gap: 7, padding: '9px 18px', borderRadius: 10, cursor: 'pointer',
            fontWeight: 700, fontSize: 13.5,
            border: `1.5px solid ${page === id ? '#4f46e5' : '#e2e8f0'}`,
            background: page === id ? '#4f46e5' : '#fff', color: page === id ? '#fff' : '#334155',
          }}><Icon size={15} /> {label}</button>
        ))}
      </div>
      {page === 'products'
        ? <ProductsPage categories={categories} onManageCategories={() => setPage('categories')} />
        : <CategoriesPage onBack={() => setPage('products')} />}
    </div>
  )
}
