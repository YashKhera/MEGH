// API base: same-origin in dev (Vite proxies to FastAPI), env override for prod.
const BASE = import.meta.env.VITE_API_URL || ''

const TOKEN_KEY = 'megh-token'
export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (t) => (t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY))

function hint(path, status) {
  if (status === 500 && !BASE) {
    return `${path}: backend unreachable (proxy 500). Start it with: uvicorn api.main:app --reload — the web app cannot run without it.`
  }
  if (status === 401) return 'Session expired — please log in again.'
  return `${path}: ${status}`
}

async function req(path, opts = {}) {
  const headers = { ...(opts.headers || {}) }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let r
  try {
    r = await fetch(`${BASE}${path}`, { ...opts, headers })
  } catch {
    throw new Error(`${path}: network error. Is the backend running? (uvicorn api.main:app --reload)`)
  }
  if (!r.ok) {
    if (r.status === 401) setToken(null)
    let detail = ''
    try { detail = (await r.json()).detail || '' } catch { /* non-json */ }
    throw new Error(detail ? `${path}: ${detail}` : hint(path, r.status))
  }
  return r.json()
}

export const api = {
  health: () => req('/health'),
  storms: () => req('/storms'),
  storm: (id) => req(`/storm/${encodeURIComponent(id)}`),
  predict: (storm_id, timestamp) => req('/predict', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ storm_id, timestamp }) }),
  explain: (question, prediction) => req('/explain', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question, prediction }) }),
  metrics: () => req('/metrics'),
  signup: (name, password, role) => req('/auth/signup', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, password, role }) }),
  login: (name, password) => req('/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, password }) }),
  me: () => req('/auth/me'),
  logout: () => req('/auth/logout', { method: 'POST' }),
  frameUrl: (image_path) => {
    const f = image_path.split('/').pop()
    return `${BASE}/frames/${f}`
  },
}
