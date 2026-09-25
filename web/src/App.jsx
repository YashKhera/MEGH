import { useEffect, useMemo, useState } from 'react'
import { api } from './api'
import TrackMap from './components/TrackMap'
import IntensityChart from './components/IntensityChart'
import EvidencePanel from './components/EvidencePanel'

const CLASS_COLORS = {
  Depression: 'bg-slate-600',
  'Deep Depression': 'bg-sky-700',
  'Cyclonic Storm': 'bg-teal-600',
  'Severe Cyclonic Storm': 'bg-yellow-600',
  'Very Severe Cyclonic Storm': 'bg-orange-600',
  'Extremely Severe Cyclonic Storm': 'bg-red-600',
  'Super Cyclonic Storm': 'bg-purple-700',
}

function badge(cls) {
  return <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold text-white ${CLASS_COLORS[cls] || 'bg-slate-600'}`}>{cls}</span>
}

export default function App() {
  const [storms, setStorms] = useState([])
  const [health, setHealth] = useState(null)
  const [error, setError] = useState(null)
  const [query, setQuery] = useState('')
  const [split, setSplit] = useState('all')
  const [sid, setSid] = useState(null)
  const [detail, setDetail] = useState(null)
  const [index, setIndex] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [prediction, setPrediction] = useState(null)
  const [predLoading, setPredLoading] = useState(false)

  useEffect(() => {
    api.health().then(setHealth).catch((e) => setError(`Backend unreachable — start it with: uvicorn api.main:app --reload (${e.message})`))
    api.storms().then((d) => {
      setStorms(d.storms)
      const biparjoy = d.storms.find((s) => s.name === 'BIPARJOY')
      setSid((biparjoy || d.storms[0]).storm_id)
    }).catch((e) => setError(String(e.message || e)))
  }, [])

  useEffect(() => {
    if (!sid) return
    setDetail(null)
    setPrediction(null)
    api.storm(sid).then((d) => {
      setDetail(d)
      setIndex(d.fixes.length - 1)
    }).catch((e) => setError(String(e.message || e)))
  }, [sid])

  useEffect(() => {
    if (!playing || !detail) return
    if (index >= detail.fixes.length - 1) {
      setPlaying(false)
      return
    }
    const t = setTimeout(() => setIndex((i) => i + 1), 900)
    return () => clearTimeout(t)
  }, [playing, index, detail])

  useEffect(() => {
    if (!detail) return
    const fix = detail.fixes[index]
    if (!fix) return
    setPredLoading(true)
    api.predict(sid, fix.timestamp)
      .then(setPrediction)
      .catch((e) => setError(String(e.message || e)))
      .finally(() => setPredLoading(false))
  }, [detail, index, sid])

  const filtered = useMemo(() => storms.filter((s) => {
    if (split !== 'all' && s.split !== split) return false
    const q = query.trim().toLowerCase()
    if (!q) return true
    return s.name.toLowerCase().includes(q) || s.storm_id.toLowerCase().includes(q) || s.peak_class.toLowerCase().includes(q)
  }), [storms, query, split])

  const fix = detail?.fixes[index]
  const next = detail && index + 1 < detail.fixes.length ? detail.fixes[index + 1] : null

  return (
    <div className="min-h-screen">
      <header className="flex items-center gap-3 border-b border-line bg-panel px-5 py-3">
        <span className="text-2xl">🌀</span>
        <div>
          <h1 className="text-lg font-bold tracking-wide">MEGH <span className="font-normal text-slate-400">· Meteorological &amp; Environmental Geospatial Hub</span></h1>
          <p className="text-xs text-slate-400">North Indian Ocean tropical cyclone analysis · {health ? `models: ${health.ml_backend}` : 'connecting…'}</p>
        </div>
      </header>

      {error && <div className="border-b border-red-900 bg-red-950 px-5 py-2 text-sm text-red-300">{error}</div>}

      <div className="flex">
        <aside className="hidden w-80 shrink-0 flex-col border-r border-line bg-panel md:flex" style={{ height: 'calc(100vh - 65px)' }}>
          <div className="space-y-2 border-b border-line p-3">
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search storms…"
              className="w-full rounded-lg border border-line bg-ink px-3 py-2 text-sm outline-none focus:border-accent" />
            <div className="flex gap-1 text-xs">
              {['all', 'train', 'val', 'test'].map((s) => (
                <button key={s} onClick={() => setSplit(s)}
                  className={`rounded-full px-3 py-1 ${split === s ? 'bg-accent text-ink font-semibold' : 'bg-ink text-slate-300'}`}>{s}</button>
              ))}
            </div>
            <p className="text-xs text-slate-500">{filtered.length} storms · IBTrACS best-track</p>
          </div>
          <div className="flex-1 overflow-y-auto">
            {filtered.map((s) => (
              <button key={s.storm_id} onClick={() => setSid(s.storm_id)}
                className={`block w-full border-b border-line px-4 py-2.5 text-left hover:bg-ink ${s.storm_id === sid ? 'bg-ink border-l-2 border-l-accent' : ''}`}>
                <div className="flex items-center justify-between">
                  <span className="font-semibold">{s.name}</span>
                  <span className="text-xs text-slate-400">{s.peak_wind_kts} kt</span>
                </div>
                <div className="mt-1 flex items-center justify-between text-xs text-slate-400">
                  <span>{s.start.slice(0, 10)} → {s.end.slice(0, 10)} · {s.n_fixes} fixes</span>
                </div>
                <div className="mt-1">{badge(s.peak_class)}</div>
              </button>
            ))}
          </div>
        </aside>

        <main className="flex-1 space-y-4 overflow-y-auto p-5" style={{ height: 'calc(100vh - 65px)' }}>
          {!detail ? (
            <p className="text-slate-400">Loading storm…</p>
          ) : (
            <>
              <section className="rounded-xl border border-line bg-panel p-4">
                <div className="flex flex-wrap items-center gap-3">
                  <h2 className="text-2xl font-bold">{detail.summary.name}</h2>
                  {badge(detail.summary.current_class)}
                  <span className="text-sm text-slate-400">
                    {detail.summary.start.slice(0, 10)} → {detail.summary.end.slice(0, 10)} · {detail.summary.n_fixes} fixes ·
                    peak {detail.summary.peak_wind_kts} kt ({detail.summary.peak_class})
                  </span>
                </div>
                <div className="mt-3 flex items-center gap-3">
                  <button onClick={() => { setIndex(0); setPlaying(true) }}
                    className="rounded-lg bg-accent px-4 py-1.5 text-sm font-semibold text-ink">▶ Replay</button>
                  <button onClick={() => setPlaying((p) => !p)}
                    className="rounded-lg border border-line px-4 py-1.5 text-sm">{playing ? '⏸ Pause' : '▶ Play'}</button>
                  <input type="range" min={0} max={detail.fixes.length - 1} value={index}
                    onChange={(e) => { setPlaying(false); setIndex(Number(e.target.value)) }} className="flex-1" />
                  <span className="text-sm text-slate-300">Fix {index + 1}/{detail.fixes.length}</span>
                </div>
              </section>

              <section className="grid gap-4 lg:grid-cols-3">
                <div className="rounded-xl border border-line bg-panel p-4">
                  <h3 className="mb-2 text-sm font-semibold text-slate-300">Satellite observation</h3>
                  {fix && <img src={api.frameUrl(fix.image_path)} alt="storm frame"
                    className="w-full rounded-lg" style={{ imageRendering: 'pixelated' }} />}
                  {fix && <p className="mt-2 text-xs text-slate-400">{fix.timestamp?.replace('T', ' ').slice(0, 16)} UTC ·
                    {parseFloat(fix.latitude).toFixed(2)}°, {parseFloat(fix.longitude).toFixed(2)}° · {fix.satellite_source}</p>}
                </div>
                <div className="rounded-xl border border-line bg-panel p-4">
                  <h3 className="mb-2 text-sm font-semibold text-slate-300">MEGH analysis</h3>
                  {predLoading || !prediction ? (
                    <p className="text-sm text-slate-400">Analysing…</p>
                  ) : (
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Intensity</span>{badge(prediction.class)}
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Confidence</span>
                        <span className="font-semibold">{(prediction.confidence * 100).toFixed(0)}%</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-ink">
                        <div className="h-full bg-accent" style={{ width: `${prediction.confidence * 100}%` }} />
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Wind</span>
                        <span className="font-semibold">{prediction.wind_kts.toFixed(1)} kt <span className="font-normal text-slate-500">(track {fix.wind_kts} kt)</span></span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Next 6h</span>
                        <span className="font-semibold text-red-300">{prediction.next_6h.lat}, {prediction.next_6h.lon}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Uncertainty</span>
                        <span>±{prediction.uncertainty_km} km</span>
                      </div>
                      {next && (
                        <p className="rounded-lg bg-ink p-2 text-xs text-slate-300">
                          Actual next: {parseFloat(next.latitude).toFixed(2)}, {parseFloat(next.longitude).toFixed(2)} —
                          revealed from IBTrACS for verification.
                        </p>
                      )}
                    </div>
                  )}
                </div>
                <div className="rounded-xl border border-line bg-panel p-4">
                  <h3 className="mb-2 text-sm font-semibold text-slate-300">Fix details</h3>
                  {fix && (
                    <dl className="space-y-1.5 text-sm">
                      {[['Time', fix.timestamp?.replace('T', ' ').slice(0, 16) + ' UTC'],
                        ['Position', `${parseFloat(fix.latitude).toFixed(2)}°, ${parseFloat(fix.longitude).toFixed(2)}°`],
                        ['Best-track wind', `${fix.wind_kts} kt`],
                        ['Best-track class', fix.derived_class],
                        ['Pressure', fix.pressure_hpa ? `${fix.pressure_hpa} hPa` : '—'],
                        ['Source', fix.satellite_source],
                      ].map(([k, v]) => (
                        <div key={k} className="flex justify-between gap-2">
                          <dt className="text-slate-400">{k}</dt><dd className="text-right font-medium">{v}</dd>
                        </div>
                      ))}
                    </dl>
                  )}
                </div>
              </section>

              <TrackMap fixes={detail.fixes} index={index} prediction={prediction} />
              <IntensityChart fixes={detail.fixes} index={index} mlWind={prediction?.wind_kts} />
              <EvidencePanel prediction={prediction ? {
                class: prediction.class, confidence: prediction.confidence,
                wind_kts: prediction.wind_kts, next_6h: prediction.next_6h,
                uncertainty_km: prediction.uncertainty_km } : null} />

              <footer className="pb-4 text-center text-xs text-slate-500">
                MEGH decision-support analysis · ground truth: NOAA IBTrACS best-track · Not an official warning — always follow IMD advisories.
              </footer>
            </>
          )}
        </main>
      </div>
    </div>
  )
}
