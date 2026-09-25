import { Suspense, lazy, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
const Globe3D = lazy(() => import('../components/Globe3D'))
import { api } from '../api'

const CLASS_ORDER = ['Depression', 'Deep Depression', 'Cyclonic Storm', 'Severe Cyclonic Storm',
  'Very Severe Cyclonic Storm', 'Extremely Severe Cyclonic Storm', 'Super Cyclonic Storm']
const CLASS_HEX = ['#64748b', '#0284c7', '#0d9488', '#ca8a04', '#ea580c', '#dc2626', '#9333ea']

const STEPS = [
  { t: 'Observe', d: 'Multi-source satellite frames aligned to IBTrACS best-track fixes.', icon: '🛰️' },
  { t: 'Perceive', d: 'Vision models identify the cyclone pattern and estimate structure.', icon: '👁️' },
  { t: 'Classify', d: 'Intensity class on the IMD scale with calibrated confidence.', icon: '📊' },
  { t: 'Estimate', d: 'Sustained wind regression in knots, verified against best-track.', icon: '💨' },
  { t: 'Predict', d: '6-hour movement forecast, scored against a persistence baseline.', icon: '🧭' },
  { t: 'Explain', d: 'Retrieved IMD / WMO / IBTrACS evidence with citations — never invented numbers.', icon: '📚' },
]

function Counter({ to, suffix }) {
  const [v, setV] = useState(0)
  useEffect(() => {
    let raf
    const t0 = performance.now()
    const tick = (t) => {
      const p = Math.min(1, (t - t0) / 1400)
      setV(to * (1 - Math.pow(1 - p, 3)))
      if (p < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [to])
  return <span>{Number.isInteger(to) ? Math.round(v) : v.toFixed(1)}{suffix}</span>
}

export default function Landing() {
  const [storms, setStorms] = useState([])
  const [metrics, setMetrics] = useState(null)
  useEffect(() => {
    api.storms().then((d) => setStorms(d.storms)).catch(() => {})
    api.metrics().then(setMetrics).catch(() => {})
  }, [])

  const classDist = CLASS_ORDER.map((c, i) => ({
    name: c.split(' ')[0], full: c, n: storms.filter((s) => s.peak_class === c).length, fill: CLASS_HEX[i],
  }))
  const fixes = storms.reduce((a, s) => a + s.n_fixes, 0)
  const evalTrack = metrics?.eval?.track_test
  const errData = evalTrack ? [
    { name: 'MEGH', km: +evalTrack.model_mean_km.toFixed(1) },
    { name: 'Persistence', km: +evalTrack.persist_mean_km.toFixed(1) },
  ] : []

  return (
    <div>
      {/* HERO */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute -left-32 top-10 h-96 w-96 rounded-full bg-accent opacity-20 blur-3xl" />
        <div className="pointer-events-none absolute -right-32 bottom-0 h-96 w-96 rounded-full bg-accent2 opacity-20 blur-3xl" />
        <div className="mx-auto grid max-w-7xl gap-6 px-4 py-12 lg:grid-cols-2">
          <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}>
            <p className="mb-3 inline-block rounded-full border border-line bg-panel px-3 py-1 text-xs t2">
              North Indian Ocean · Satellite intelligence · IBTrACS-verified
            </p>
            <h1 className="text-4xl font-extrabold leading-tight t1 md:text-6xl">
              See every cyclone <span className="t-accent">before</span> it turns.
            </h1>
            <p className="mt-4 max-w-xl text-base t2 md:text-lg">
              MEGH — the Meteorological &amp; Environmental Geospatial Hub — fuses satellite
              vision with decades of best-track history to identify cyclones, classify IMD
              intensity, estimate winds and forecast 6-hour movement, with evidence you can inspect.
            </p>
            <div className="mt-6 flex gap-3">
              <Link to="/cyclones" className="btn-primary !px-6 !py-3 !text-base">Explore cyclones →</Link>
              <Link to="/methodology" className="btn-ghost !px-6 !py-3 !text-base">How it works</Link>
            </div>
            <div className="mt-8 grid max-w-lg grid-cols-3 gap-3">
              {[
                { v: storms.length, suf: '', l: 'Storms tracked' },
                { v: fixes, suf: '', l: '6-hourly fixes' },
                { v: evalTrack ? evalTrack.persist_mean_km - evalTrack.model_mean_km : 0, suf: ' km', l: 'Track skill vs baseline' },
              ].map((s) => (
                <div key={s.l} className="card p-3 text-center">
                  <div className="text-2xl font-extrabold t-accent"><Counter to={s.v} suffix={s.suf} /></div>
                  <div className="text-xs t2">{s.l}</div>
                </div>
              ))}
            </div>
          </motion.div>
          <motion.div initial={{ opacity: 0, scale: 0.94 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.9 }}
            className="h-[380px] md:h-[480px]">
            <Suspense fallback={<div className="flex h-full items-center justify-center text-sm t2">Loading 3D globe…</div>}>
              <Globe3D storms={storms} />
            </Suspense>
            <p className="text-center text-xs t2">Live storm genesis points · drag to rotate</p>
          </motion.div>
        </div>
      </section>

      {/* PIPELINE */}
      <section className="mx-auto max-w-7xl px-4 py-10">
        <h2 className="mb-1 text-2xl font-bold t1">From pixels to forecast in six steps</h2>
        <p className="mb-6 text-sm t2">One observable, verifiable path — models predict, evidence explains.</p>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
          {STEPS.map((s, i) => (
            <motion.div key={s.t} initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }} transition={{ delay: i * 0.08 }}
              className="card animate-floaty p-4" style={{ animationDelay: `${i * 0.7}s` }}>
              <div className="text-3xl">{s.icon}</div>
              <div className="mt-2 text-xs font-bold uppercase tracking-wider t-accent">0{i + 1}</div>
              <div className="font-semibold t1">{s.t}</div>
              <div className="mt-1 text-xs t2">{s.d}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* LIVE CHARTS */}
      <section className="mx-auto grid max-w-7xl gap-4 px-4 py-6 lg:grid-cols-2">
        <div className="card p-4">
          <h3 className="mb-1 font-semibold t1">Storms by peak intensity (live)</h3>
          <p className="mb-2 text-xs t2">Peak IMD class across the archive</p>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={classDist} layout="vertical">
              <XAxis type="number" hide />
              <YAxis dataKey="name" type="category" width={90} tick={{ fontSize: 11, fill: 'currentColor' }} />
              <Tooltip contentStyle={{ background: 'rgb(var(--c-panel))', border: '1px solid rgb(var(--c-line))' }} />
              <Bar dataKey="n" radius={[0, 6, 6, 0]}>
                {classDist.map((c) => <Cell key={c.full} fill={c.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card p-4">
          <h3 className="mb-1 font-semibold t1">Track error: MEGH vs baseline (held-out storms)</h3>
          <p className="mb-2 text-xs t2">Mean 6h great-circle error, kilometres — lower is better</p>
          {errData.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={errData}>
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: 'currentColor' }} />
                <YAxis tick={{ fontSize: 11, fill: 'currentColor' }} />
                <Tooltip contentStyle={{ background: 'rgb(var(--c-panel))', border: '1px solid rgb(var(--c-line))' }} />
                <Bar dataKey="km" radius={[8, 8, 0, 0]}>
                  <Cell fill="#38bdf8" /><Cell fill="#f59e0b" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : <p className="text-sm t2">Loading evaluation…</p>}
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-7xl px-4 pb-14">
        <div className="card flex flex-col items-center gap-4 p-8 text-center">
          <div className="text-4xl">🌀</div>
          <h2 className="text-2xl font-bold t1">Replay Tauktae, Biparjoy, Mocha — fix by fix.</h2>
          <p className="max-w-2xl text-sm t2">Scrub the timeline, compare MEGH's 6-hour forecast against the actual
            IBTrACS track, and ask the evidence layer why each classification was made.</p>
          <Link to="/cyclones" className="btn-primary !px-8 !py-3 !text-base">Open the archive →</Link>
        </div>
      </section>
    </div>
  )
}
