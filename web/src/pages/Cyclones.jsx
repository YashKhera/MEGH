import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { api } from '../api'

const CLASS_COLORS = {
  Depression: 'bg-slate-500', 'Deep Depression': 'bg-sky-600', 'Cyclonic Storm': 'bg-teal-600',
  'Severe Cyclonic Storm': 'bg-yellow-600', 'Very Severe Cyclonic Storm': 'bg-orange-600',
  'Extremely Severe Cyclonic Storm': 'bg-red-600', 'Super Cyclonic Storm': 'bg-purple-600',
}

export default function Cyclones() {
  const [storms, setStorms] = useState([])
  const [q, setQ] = useState('')
  const [cls, setCls] = useState('all')
  const [err, setErr] = useState(null)
  useEffect(() => { api.storms().then((d) => setStorms(d.storms)).catch((e) => setErr(String(e.message || e))) }, [])

  const classes = useMemo(() => ['all', ...new Set(storms.map((s) => s.peak_class))], [storms])
  const list = storms.filter((s) => {
    if (cls !== 'all' && s.peak_class !== cls) return false
    const t = q.trim().toLowerCase()
    return !t || s.name.toLowerCase().includes(t) || s.storm_id.toLowerCase().includes(t)
  })

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="text-3xl font-extrabold t1">Cyclone archive</h1>
      <p className="mt-1 text-sm t2">{storms.length} North Indian Ocean systems · IBTrACS best-track ground truth</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search name or ID…"
          className="input !w-64" />
        <select value={cls} onChange={(e) => setCls(e.target.value)} className="input !w-64">
          {classes.map((c) => <option key={c}>{c}</option>)}
        </select>
      </div>
      {err && (
        <div className="card mt-4 border-red-900 p-4">
          <p className="text-sm font-semibold text-red-400">Could not load the archive</p>
          <p className="mt-1 font-mono text-xs t2">{err}</p>
          <p className="mt-2 text-xs t2">Backend needed — run <code>uvicorn api.main:app --reload</code> in the repo root, then refresh.</p>
        </div>
      )}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {list.map((s, i) => (
          <motion.div key={s.storm_id} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: Math.min(i * 0.03, 0.5) }}>
            <Link to={`/cyclone/${s.storm_id}`} className="card block p-4 transition hover:border-accent">
              <div className="flex items-center justify-between">
                <span className="text-lg font-bold t1">{s.name}</span>
                <span className="text-sm font-bold t-accent">{s.peak_wind_kts} kt</span>
              </div>
              <div className="mt-1 text-xs t2">{s.start.slice(0, 10)} → {s.end.slice(0, 10)} · {s.n_fixes} fixes · {s.storm_id}</div>
              <div className="mt-2">
                <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold text-white ${CLASS_COLORS[s.peak_class] || 'bg-slate-500'}`}>
                  {s.peak_class}
                </span>
              </div>
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
