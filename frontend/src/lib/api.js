import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ──── AUTH ────
export const login = (email, password) =>
  api.post('/auth/login', { email, password }).then((r) => r.data)

export const register = (email, name, password) =>
  api.post('/auth/register', { email, name, password }).then((r) => r.data)

export const getMe = () => api.get('/auth/me').then((r) => r.data)

export const updateProfile = (data) =>
  api.put('/auth/profile', data).then((r) => r.data)

export const changePassword = (current_password, new_password) =>
  api.post('/auth/change-password', { current_password, new_password }).then((r) => r.data)

export const verifyEmail = (token) =>
  api.get(`/auth/verify-email?token=${token}`).then((r) => r.data)

export const resendVerification = (email) =>
  api.post('/auth/resend-verification', { email }).then((r) => r.data)

export const forgotPassword = (email) =>
  api.post('/auth/forgot-password', { email }).then((r) => r.data)

export const resetPassword = (token, new_password) =>
  api.post('/auth/reset-password', { token, new_password }).then((r) => r.data)

// ──── API KEYS ────
export const getKeys = () => api.get('/auth/keys').then((r) => r.data)

export const createKey = (name, tier) =>
  api.post('/auth/keys', { name, tier }).then((r) => r.data)

export const revokeKey = (keyId) =>
  api.delete(`/auth/keys/${keyId}`).then((r) => r.data)

export const getUsageStats = (keyId) =>
  api.get(`/auth/usage/${keyId}`).then((r) => r.data)

export const getCreditCosts = () =>
  api.get('/auth/credits/costs').then((r) => r.data)

// ──── CONTENT (public) ────
export const getPageConfig = () =>
  api.get('/api/page-config').then((r) => r.data?.data ?? r.data)

export const getBlogs = (params = {}) =>
  api.get('/api/blogs', { params }).then((r) => r.data?.data ?? r.data)

export const getBlog = (slug) =>
  api.get(`/api/blogs/${slug}`).then((r) => r.data?.data ?? r.data)

// ──── PAYMENTS ────
export const createCheckout = (plan, currency) =>
  api.post('/payments/checkout', { plan, currency }).then((r) => r.data)

export const getMyPayments = (page = 1) =>
  api.get('/payments/my-payments', { params: { page } }).then((r) => r.data)

// ──── ADMIN: PAGE CONFIG ────
export const adminGetConfig = () =>
  api.get('/admin/config').then((r) => r.data)

export const adminUpdateConfig = (data) =>
  api.put('/admin/config', data).then((r) => r.data)

export const adminSetConfig = (key, value) =>
  api.post('/admin/config', { key, value }).then((r) => r.data)

export const adminResetConfig = () =>
  api.post('/admin/config/reset').then((r) => r.data)

// ──── ADMIN: BLOGS ────
export const adminGetBlogs = (params = {}) =>
  api.get('/admin/blogs', { params }).then((r) => r.data)

export const adminCreateBlog = (data) =>
  api.post('/admin/blogs', data).then((r) => r.data)

export const adminUpdateBlog = (id, data) =>
  api.put(`/admin/blogs/${id}`, data).then((r) => r.data)

export const adminDeleteBlog = (id) =>
  api.delete(`/admin/blogs/${id}`).then((r) => r.data)

export const adminPublishBlog = (id) =>
  api.post(`/admin/blogs/${id}/publish`).then((r) => r.data)

export const adminUnpublishBlog = (id) =>
  api.post(`/admin/blogs/${id}/unpublish`).then((r) => r.data)

// ──── ADMIN: EARNINGS / PAYMENTS ────
export const adminGetPayments = (params = {}) =>
  api.get('/payments/admin/payments', { params }).then((r) => r.data)

export const adminGetPaymentsTotals = () =>
  api.get('/payments/admin/payments/totals').then((r) => r.data)

// ──── ADMIN ────
export const adminGetUsers = (page = 1, search = '') =>
  api.get('/admin/users', { params: { page, search } }).then((r) => r.data)

export const adminGetUser = (userId) =>
  api.get(`/admin/users/${userId}`).then((r) => r.data)

export const adminUpdatePlan = (userId, plan) =>
  api.put(`/admin/users/${userId}/plan`, { plan }).then((r) => r.data)

export const adminSetMonthlyLimit = (userId, monthlyLimit) =>
  api.put(`/admin/users/${userId}/monthly-limit`, { monthly_limit: monthlyLimit }).then((r) => r.data)

export const adminToggleAdmin = (userId) =>
  api.put(`/admin/users/${userId}/admin`).then((r) => r.data)

export const adminDeleteUser = (userId) =>
  api.delete(`/admin/users/${userId}`).then((r) => r.data)

export const adminGetKeys = (page = 1) =>
  api.get('/admin/keys', { params: { page } }).then((r) => r.data)

export const adminRevokeKey = (keyId) =>
  api.delete(`/admin/keys/${keyId}`).then((r) => r.data)

export const adminUpdateKeyTier = (keyId, tier) =>
  api.put(`/admin/keys/${keyId}/tier`, { tier }).then((r) => r.data)

export const adminGetStats = () =>
  api.get('/admin/stats').then((r) => r.data)

export const adminGetUsageDaily = (days = 30) =>
  api.get('/admin/usage/daily', { params: { days } }).then((r) => r.data)

export const adminGetUsageEndpoints = (limit = 20) =>
  api.get('/admin/usage/endpoints', { params: { limit } }).then((r) => r.data)

export const adminGetJobs = (page = 1, status = '') =>
  api.get('/admin/jobs', { params: { page, status } }).then((r) => r.data)

export const adminResetPassword = (userId, newPassword) =>
  api.put(`/admin/users/${userId}/reset-password`, { new_password: newPassword }).then((r) => r.data)

export const adminCreateKeyForUser = (userId, name, tier) =>
  api.post(`/admin/users/${userId}/keys`, { name, tier }).then((r) => r.data)

export const adminGetUserKeys = (userId) =>
  api.get(`/admin/users/${userId}`).then((r) => r.data)

export const adminGetUserUsage = (userId) =>
  api.get(`/admin/users/${userId}/usage`).then((r) => r.data)

export const adminGetUsageByUser = (limit = 50) =>
  api.get('/admin/usage/by-user', { params: { limit } }).then((r) => r.data)

// ──── AI PROVIDERS ────
export const listProviders = () =>
  api.get('/ai-providers').then((r) => r.data)

export const createProvider = (data) =>
  api.post('/ai-providers', data).then((r) => r.data)

export const updateProvider = (id, data) =>
  api.put(`/ai-providers/${id}`, data).then((r) => r.data)

export const deleteProvider = (id) =>
  api.delete(`/ai-providers/${id}`).then((r) => r.data)

export const testProvider = (id) =>
  api.post(`/ai-providers/${id}/test`).then((r) => r.data)

export const getSupportedProviders = () =>
  api.get('/ai-providers/supported').then((r) => r.data)

// ──── SITE BUILDER (tenant websites) ────
// Availability checks (public — used pre-signup in the wizard)
export const checkSlugAvailability = (slug) =>
  api.get('/sites/check-slug', { params: { slug } }).then((r) => r.data)

export const checkDomainAvailability = (domain) =>
  api.get('/sites/check-domain', { params: { domain } }).then((r) => r.data)

// Owner endpoints (JWT-authenticated)
export const getMySites = () =>
  api.get('/sites/my').then((r) => r.data?.sites ?? r.data?.data?.sites ?? [])

export const createMySite = (data) =>
  api.post('/sites/my', data).then((r) => r.data?.data ?? r.data)

export const getMySite = (siteId) =>
  api.get(`/sites/my/${siteId}`).then((r) => r.data?.data ?? r.data)

export const updateMySite = (siteId, data) =>
  api.put(`/sites/my/${siteId}`, data).then((r) => r.data?.data ?? r.data)

export const publishMySite = (siteId) =>
  api.post(`/sites/my/${siteId}/publish`).then((r) => r.data?.data ?? r.data)

export const unpublishMySite = (siteId) =>
  api.post(`/sites/my/${siteId}/unpublish`).then((r) => r.data?.data ?? r.data)

export const deleteMySite = (siteId) =>
  api.delete(`/sites/my/${siteId}`).then((r) => r.data)

export const saveMySitePage = (siteId, pageKey, data) =>
  api.put(`/sites/my/${siteId}/pages/${pageKey}`, data).then((r) => r.data?.data ?? r.data)

export const setMySiteDomain = (siteId, domain) =>
  api.post(`/sites/my/${siteId}/domain`, { domain }).then((r) => r.data?.data ?? r.data)

export const verifyMySiteDomain = (siteId) =>
  api.post(`/sites/my/${siteId}/domain/verify`).then((r) => r.data?.data ?? r.data)

export const removeMySiteDomain = (siteId) =>
  api.delete(`/sites/my/${siteId}/domain`).then((r) => r.data?.data ?? r.data)

export const createMyService = (siteId, data) =>
  api.post(`/sites/my/${siteId}/services`, data).then((r) => r.data?.data ?? r.data)

export const updateMyService = (siteId, serviceId, data) =>
  api.put(`/sites/my/${siteId}/services/${serviceId}`, data).then((r) => r.data?.data ?? r.data)

export const deleteMyService = (siteId, serviceId) =>
  api.delete(`/sites/my/${siteId}/services/${serviceId}`).then((r) => r.data)

export const getMyAvailability = (siteId) =>
  api.get(`/sites/my/${siteId}/availability`).then((r) => r.data?.data ?? r.data)

export const setMyAvailability = (siteId, rules) =>
  api.put(`/sites/my/${siteId}/availability`, { rules }).then((r) => r.data?.data ?? r.data)

export const getMyBookings = (siteId, params = {}) =>
  api.get(`/sites/my/${siteId}/bookings`, { params }).then((r) => r.data?.bookings ?? r.data?.data?.bookings ?? [])

export const updateMyBooking = (siteId, bookingId, data) =>
  api.put(`/sites/my/${siteId}/bookings/${bookingId}`, data).then((r) => r.data?.data ?? r.data)

export const setMySiteMedia = (siteId, data) =>
  api.put(`/sites/my/${siteId}/media`, data).then((r) => r.data?.data ?? r.data)

export const setMySiteSettings = (siteId, data) =>
  api.put(`/sites/my/${siteId}/settings`, data).then((r) => r.data?.data ?? r.data)

export const getMyLeads = (siteId) =>
  api.get(`/sites/my/${siteId}/leads`).then((r) => r.data?.leads ?? r.data?.data?.leads ?? [])

export const getMySiteStats = (siteId) =>
  api.get(`/sites/my/${siteId}/stats`).then((r) => r.data?.stats ?? r.data?.data?.stats ?? r.data?.data ?? r.data ?? {})

// ──── SITE BUILDER: STORE ────
export const getMyProducts = (siteId) =>
  api.get(`/sites/my/${siteId}/products`).then((r) => r.data?.products ?? r.data?.data?.products ?? [])

export const createMyProduct = (siteId, data) =>
  api.post(`/sites/my/${siteId}/products`, data).then((r) => r.data?.data ?? r.data)

export const updateMyProduct = (siteId, productId, data) =>
  api.put(`/sites/my/${siteId}/products/${productId}`, data).then((r) => r.data?.data ?? r.data)

export const deleteMyProduct = (siteId, productId) =>
  api.delete(`/sites/my/${siteId}/products/${productId}`).then((r) => r.data)

export const getMyOrders = (siteId, params = {}) =>
  api.get(`/sites/my/${siteId}/orders`, { params }).then((r) => r.data?.orders ?? r.data?.data?.orders ?? [])

export const updateMyOrder = (siteId, orderId, data) =>
  api.put(`/sites/my/${siteId}/orders/${orderId}`, data).then((r) => r.data?.data ?? r.data)

// Public tenant-site endpoints (visitor-facing, no auth).
// `resolve` is a slug string or { slug } / { domain } — every endpoint on the
// backend accepts either (?slug= or ?domain=), so subdomain AND custom-domain
// hosting hit the same calls.
const resolveParams = (resolve) =>
  typeof resolve === 'string' ? { slug: resolve } : resolve

export const getPublicSite = (resolve) =>
  api.get('/sites/site', { params: resolveParams(resolve) }).then((r) => r.data?.data ?? r.data)

export const getPublicAvailability = (resolve, weeks = 2) =>
  api.get('/sites/site/availability', { params: { ...resolveParams(resolve), weeks } }).then((r) => r.data?.data ?? r.data)

export const publicBook = (resolve, data) => {
  const qs = new URLSearchParams(resolveParams(resolve)).toString()
  return api.post(`/sites/site/book?${qs}`, data).then((r) => r.data?.data ?? r.data)
}

export const publicKundliTool = (resolve, data) => {
  const qs = new URLSearchParams(resolveParams(resolve)).toString()
  return api.post(`/sites/site/tools/kundli?${qs}`, data).then((r) => r.data)
}

export const publicPanchangTool = (resolve) =>
  api.get('/sites/site/tools/panchang', { params: resolveParams(resolve) }).then((r) => r.data?.data ?? r.data)

export const publicHoroscopeTool = (resolve, sign) =>
  api.get('/sites/site/tools/horoscope', { params: { ...resolveParams(resolve), sign } }).then((r) => r.data)

export const publicPlaceOrder = (resolve, data) => {
  const qs = new URLSearchParams(resolveParams(resolve)).toString()
  return api.post(`/sites/site/order?${qs}`, data).then((r) => r.data)
}

// ──── JOBS ────
export const submitPdfJob = (data) =>
  api.post('/jobs/submit-pdf', data).then((r) => r.data)

export const submitAiJob = (data) =>
  api.post('/jobs/submit-ai', data).then((r) => r.data)

export const getJobStatus = (jobId) =>
  api.get(`/jobs/${jobId}`).then((r) => r.data)

export const downloadJobResult = (jobId) =>
  api.get(`/jobs/${jobId}/download`, { responseType: 'blob' }).then((r) => r)

export const getMyJobs = (status = '') =>
  api.get('/jobs/my-jobs', { params: { status } }).then((r) => r.data)

export default api
