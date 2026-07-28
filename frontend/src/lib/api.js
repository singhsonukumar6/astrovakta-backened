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

// ──── API KEYS ────
export const getKeys = () => api.get('/auth/keys').then((r) => r.data)

export const createKey = (name, tier) =>
  api.post('/auth/keys', { name, tier }).then((r) => r.data)

export const revokeKey = (keyId) =>
  api.delete(`/auth/keys/${keyId}`).then((r) => r.data)

// ──── ADMIN ────
export const adminGetUsers = (page = 1, search = '') =>
  api.get('/admin/users', { params: { page, search } }).then((r) => r.data)

export const adminGetUser = (userId) =>
  api.get(`/admin/users/${userId}`).then((r) => r.data)

export const adminUpdatePlan = (userId, plan) =>
  api.put(`/admin/users/${userId}/plan`, { plan }).then((r) => r.data)

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
  api.get('/ai-providers/providers').then((r) => r.data)

export const createProvider = (data) =>
  api.post('/ai-providers/providers', data).then((r) => r.data)

export const updateProvider = (id, data) =>
  api.put(`/ai-providers/providers/${id}`, data).then((r) => r.data)

export const deleteProvider = (id) =>
  api.delete(`/ai-providers/providers/${id}`).then((r) => r.data)

export const testProvider = (id) =>
  api.post(`/ai-providers/providers/${id}/test`).then((r) => r.data)

export const getSupportedProviders = () =>
  api.get('/ai-providers/supported').then((r) => r.data)

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
