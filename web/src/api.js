// API base: same-origin in dev (Vite proxies to FastAPI), env override for prod.
const BASE = import.meta.env.VITE_API_URL || ''

async function get(path) {
  const r = await fetch(`${BASE}${path}`)
  if (!r.ok) throw new Error(`${path}: ${r.status}`)
  return r.json()
}

async function post(path, body) {
  const r = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(`${path}: ${r.status}`)
  return r.json()
}

export const api = {
  health: () => get('/health'),
  storms: () => get('/storms'),
  storm: (id) => get(`/storm/${encodeURIComponent(id)}`),
  predict: (storm_id, timestamp) => post('/predict', { storm_id, timestamp }),
  explain: (question, prediction) => post('/explain', { question, prediction }),
  frameUrl: (image_path) => {
    const f = image_path.split('/').pop()
    return `${BASE}/frames/${f}`
  },
}
