/**
 * Minimal HTML sanitizer for trusted-ish content that must keep formatting
 * (blog bodies, admin previews). Allowlist-based: unknown tags are unwrapped,
 * unknown attributes dropped, and script/style-class elements removed with
 * their contents. URLs are restricted to safe schemes.
 *
 * For anything user-generated that doesn't need markup, prefer plain text.
 */

const ALLOWED_TAGS = new Set([
  'A', 'ABBR', 'B', 'BLOCKQUOTE', 'BR', 'CODE', 'DIV', 'EM', 'FIGCAPTION',
  'FIGURE', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'HR', 'I', 'IMG', 'LI', 'MARK',
  'OL', 'P', 'PRE', 'S', 'SMALL', 'SPAN', 'STRONG', 'SUB', 'SUP', 'TABLE',
  'TBODY', 'TD', 'TH', 'THEAD', 'TR', 'U', 'UL',
])

// Removed together with their contents
const DROP_TAGS = new Set([
  'SCRIPT', 'STYLE', 'IFRAME', 'OBJECT', 'EMBED', 'LINK', 'META', 'FORM',
  'BASE', 'TEMPLATE', 'NOSCRIPT', 'SVG', 'MATH', 'AUDIO', 'VIDEO',
])

const ALLOWED_ATTRS = {
  A: new Set(['href', 'title', 'target']),
  IMG: new Set(['src', 'alt', 'title', 'width', 'height', 'loading']),
  TH: new Set(['colspan', 'rowspan']),
  TD: new Set(['colspan', 'rowspan']),
}

const URL_ATTRS = new Set(['href', 'src'])

const SAFE_URL = /^(https?:\/\/|mailto:|\/|#)/i
const SAFE_DATA_IMAGE = /^data:image\/(png|jpe?g|gif|webp|svg\+xml);base64,/i

function safeUrlAttr(tag, value) {
  const v = String(value || '').trim()
  if (SAFE_URL.test(v)) return v
  if (tag === 'IMG' && SAFE_DATA_IMAGE.test(v)) return v
  return null
}

function cleanNode(node) {
  let i = 0
  while (i < node.children.length) {
    const child = node.children[i]
    const tag = child.tagName.toUpperCase()

    if (DROP_TAGS.has(tag)) {
      child.remove()
      continue // don't advance: siblings shifted left
    }

    if (!ALLOWED_TAGS.has(tag)) {
      // unwrap: keep the text/children, drop the unknown element
      while (child.firstChild) node.insertBefore(child.firstChild, child)
      child.remove()
      continue
    }

    for (const attr of Array.from(child.attributes)) {
      const name = attr.name.toLowerCase()
      if (name.startsWith('on') || !ALLOWED_ATTRS[tag]?.has(name)) {
        child.removeAttribute(attr.name)
        continue
      }
      if (URL_ATTRS.has(name)) {
        const safe = safeUrlAttr(tag, attr.value)
        if (safe === null) child.removeAttribute(attr.name)
        else child.setAttribute(attr.name, safe)
      }
    }
    // rendered in-app links must never leak the opener
    if (tag === 'A' && child.getAttribute('target') === '_blank') {
      child.setAttribute('rel', 'noopener noreferrer nofollow')
    }

    cleanNode(child)
    i += 1
  }
}

export function sanitizeHtml(dirty) {
  try {
    const doc = new DOMParser().parseFromString(String(dirty || ''), 'text/html')
    cleanNode(doc.body)
    return doc.body.innerHTML
  } catch {
    return ''
  }
}
