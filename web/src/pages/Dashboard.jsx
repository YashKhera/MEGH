import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { useAuth, isSpecialist } from '../auth'
import { api } from '../api'

export default function Dashboard() {
  const { user } = useAuth()
  const nav = useNavigate()
  const [storms, setStorms] = useState([])
  const [metrics, setMetrics] = useState(null)
  useEffect(() => {
    api.storms().then((d) => setStorms(d.storms)).catch(() => {})
    api.metrics().then(setMetrics).catch(() => {})
  }, [])

  const role = user?.role || 'viewer'
  const top = [...storms].sort((a, b) => b.peak_wind_kts - a.peak_wind_kts).slice(0, 8)
  const evalTrack = metrics?.eval?.track_test
  const evalCls = metrics?.eval?.classification

  return (
    <div className="mx-auto max-w-7xl space-y-4 px-4 py-8">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-3xl font-extrabold t1">
          {role === 'viewer' ? 'Mission control' : role === 'analyst' ? 'Verification console' : 'Research cockpit'}
        </h1>
        <span className="rounded-full border border-line bg-panel px-3 py-1 text-xs t2">
          {user ? `${user.name} · ${role}` : 'Guest viewer'}
        </span>
        {!user && <button onClick={() => nav('/signup')} className="btn-primary ml-auto">Personalise →</button>}
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { l: 'Storms in archive', v: storms.length },
          { l: 'Fixes analysed', v: storms.reduce((a, s) => a + s.n_fixes, 0) },
          { l: 'Peak wind on record', v: `${Math.max(0, ...storms.map((s) => s.peak_wind_kts))} kt` },
          { l: 'ML backend', v: metrics?.ml_backend || '…' },
        ].map((c) => (
          <div key={c.l} className="card p-4">
            <div className="text-2xl font-extrabold t-accent">{c.v}</div>
            <div className="text-xs t2">{c.l}</div>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card p-4">
          <h3 className="mb-2 font-semibold t1">Most intense storms</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={top} layout="vertical">
              <XAxis type="number" hide />
              <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 11, fill: 'currentColor' }} />
              <Tooltip contentStyle={{ background: 'rgb(var(--c-panel))', border: '1px solid rgb(var(--c-line))' }} />
              <Bar dataKey="peak_wind_kts" radius={[0, 6, 6, 0]} fill="#38bdf8" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card space-y-2 p-4">
          <h3 className="font-semibold t1">Strongest systems — open for replay</h3>
          {top.slice(0, 5).map((s) => (
            <Link key={s.storm_id} to={`/cyclone/${s.storm_id}`}
              className="flex items-center justify-between rounded-lg border border-line p-2.5 hover:border-accent">
              <span className="font-semibold t1">{s.name}</span>
              <span className="text-xs t2">{s.peak_wind_kts} kt · {s.peak_class}</span>
            </Link>
          ))}
          <Link to="/cyclones" className="t-accent text-sm">Full archive →</Link>
        </div>
      </div>

      {isSpecialist(user) && (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="card p-4">
            <h3 className="mb-1 font-semibold t1">Analyst — held-out verification</h3>
            {evalTrack ? (
              <dl className="space-y-1.5 text-sm">
                {[['Test pairs', evalTrack.n_pairs], ['MEGH mean error', `${evalTrack.model_mean_km.toFixed(1)} km`],
                  ['Persistence baseline', `${evalTrack.persist_mean_km.toFixed(1)} km`],
                  ['Skill', `${(evalTrack.persist_mean_km - evalTrack.model_mean_km).toFixed(1)} km`],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between"><dt className="t2">{k}</dt><dd className="font-semibold t1">{v}</dd></div>
                ))}
              </dl>
            ) : <p className="text-sm t2">Loading…</p>}
            <p className="mt-2 text-xs t2">Storm-level split — test storms never seen in training.</p>
          </div>
          <div className="card p-4">
            <h3 className="mb-1 font-semibold t1">{user.role === 'researcher' ? 'Researcher — model card' : 'Classification quality'}</h3>
            {evalCls ? (
              <dl className="space-y-1.5 text-sm">
                {[['Test macro-F1', evalCls.macro_f1.toFixed(2)],
                  ['Vision-only macro-F1', evalCls.vision_only_macro_f1.toFixed(2)],
                  ['Wind MAE', `${metrics.eval.wind.mae.toFixed(2)} kt`],
                  ['Classes', evalCls.labels.length],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between"><dt className="t2">{k}</dt><dd className="font-semibold t1">{v}</dd></div>
                ))}
              </dl>
            ) : <p className="text-sm t2">Loading…</p>}
            {user.role === 'researcher' && (
              <Link to="/methodology" className="t-accent text-sm">Architecture, RAG pipeline &amp; limitations →</Link>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
