import { useState } from 'react'
import { api } from '../api'

export default function EvidencePanel({ prediction }) {
  const [q, setQ] = useState('Why was this observation given its intensity class?')
  const [res, setRes] = useState(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState(null)

  async function ask() {
    setLoading(true)
    setErr(null)
    try {
      const data = await api.explain(q, prediction)
      setRes(data)
    } catch (e) {
      setErr(String(e.message || e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-xl border border-line bg-panel p-4">
      <h3 className="mb-2 text-sm font-semibold text-slate-300">Meteorological evidence</h3>
      <div className="flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="flex-1 rounded-lg border border-line bg-ink px-3 py-2 text-sm outline-none focus:border-accent"
        />
        <button onClick={ask} disabled={loading} className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-ink disabled:opacity-50">
          {loading ? '…' : 'Explain'}
        </button>
      </div>
      {err && <p className="mt-2 text-sm text-red-400">{err}</p>}
      {res && (
        <div className="mt-3 text-sm leading-relaxed text-slate-200">
          <p>{res.answer}</p>
          {res.sources?.length > 0 && (
            <ul className="mt-2 space-y-1 text-xs text-slate-400">
              {res.sources.map((s) => (
                <li key={s.id}>📄 {s.citation}{s.url ? ` — ${s.url}` : ''}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
