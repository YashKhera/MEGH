import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import TrackMap from '../components/TrackMap'
import IntensityChart from '../components/IntensityChart'
import EvidencePanel from '../components/EvidencePanel'

const CLASS_COLORS = {
  Depression: 'bg-slate-500', 'Deep Depression': 'bg-sky-600', 'Cyclonic Storm': 'bg-teal-600',
  'Severe Cyclonic Storm': 'bg-yellow-600', 'Very Severe Cyclonic Storm': 'bg-orange-600',
  'Extremely Severe Cyclonic Storm': 'bg-red-600', 'Super Cyclonic Storm': 'bg-purple-600',
}
const badge = (cls) => (
  <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold text-white ${CLASS_COLORS[cls] || 'bg-slate-500'}`}>{cls}</span>
)

function mapStyle() {
  const v = getComputedStyle(document.documentElement).getPropertyValue('--map-style').trim().replace(/^"|"$/g, '')
  return v || 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'
}

export default function CycloneDetail() {
  const { id } = useParams()
  const [detail, setDetail] = useState(null)
  const [index, setIndex] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [prediction, setPrediction] = useState(null)
  const [predLoading, setPredLoading] = useState(false)
  const [error, setError] = useState(null)
  const [style, setStyle] = useState(mapStyle())

  useEffect(() => {
    setDetail(null); setPrediction(null); setError(null)
    api.storm(id).then((d) => { setDetail(d); setIndex(d.fixes.length - 1) })
      .catch((e) => setError(String(e.message || e)))
  }, [id])

  useEffect(() => { setStyle(mapStyle()) }, [detail])

  useEffect(() => {
    if (!playing || !detail) return
    if (index >= detail.fixes.length - 1) { setPlaying(false); return }
    const t = setTimeout(() => setIndex((i) => i + 1), 900)
    return () => clearTimeout(t)
  }, [playing, index, detail])

  useEffect(() => {
    if (!detail) return
    const fix = detail.fixes[index]
    if (!fix) return
    setPredLoading(true)
    api.predict(id, fix.timestamp).then(setPrediction)
      .catch((e) => setError(String(e.message || e)))
      .finally(() => setPredLoading(false))
  }, [detail, index, id])

  if (error) return <div className="mx-auto max-w-7xl px-4 py-8 text-sm text-red-400">{error}</div>
  if (!detail) return <div className="mx-auto max-w-7xl px-4 py-8 text-sm t2">Loading cyclone…</div>

  const fix = detail.fixes[index]
  const next = index + 1 < detail.fixes.length ? detail.fixes[index + 1] : null
  const s = detail.summary

  return (
    <div className="mx-auto max-w-7xl space-y-4 px-4 py-8">
      <Link to="/cyclones" className="t-accent text-sm">← Archive</Link>
      <section className="card p-4">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-3xl font-extrabold t1">{s.name}</h1>
          {badge(s.current_class)}
          <span className="text-sm t2">{s.start.slice(0, 10)} → {s.end.slice(0, 10)} · {s.n_fixes} fixes ·
            peak {s.peak_wind_kts} kt ({s.peak_class})</span>
        </div>
        <div className="mt-3 flex items-center gap-3">
          <button onClick={() => { setIndex(0); setPlaying(true) }} className="btn-primary">▶ Replay</button>
          <button onClick={() => setPlaying((p) => !p)} className="btn-ghost">{playing ? '⏸ Pause' : '▶ Play'}</button>
          <input type="range" min={0} max={detail.fixes.length - 1} value={index}
            onChange={(e) => { setPlaying(false); setIndex(Number(e.target.value)) }} className="flex-1" />
          <span className="text-sm t1">Fix {index + 1}/{detail.fixes.length}</span>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="card p-4">
          <h3 className="mb-2 text-sm font-semibold t2">Satellite observation</h3>
          <img src={api.frameUrl(fix.image_path)} alt="storm frame" className="w-full rounded-lg" style={{ imageRendering: 'pixelated' }} />
          <p className="mt-2 text-xs t2">{fix.timestamp?.replace('T', ' ').slice(0, 16)} UTC ·{' '}
            {parseFloat(fix.latitude).toFixed(2)}°, {parseFloat(fix.longitude).toFixed(2)}° · {fix.satellite_source}</p>
        </div>
        <div className="card p-4">
          <h3 className="mb-2 text-sm font-semibold t2">MEGH analysis</h3>
          {predLoading || !prediction ? <p className="text-sm t2">Analysing…</p> : (
            <div className="space-y-2 text-sm t1">
              <div className="flex items-center justify-between"><span className="t2">Intensity</span>{badge(prediction.class)}</div>
              <div className="flex items-center justify-between"><span className="t2">Confidence</span>
                <span className="font-semibold">{(prediction.confidence * 100).toFixed(0)}%</span></div>
              <div className="h-2 overflow-hidden rounded-full bg-ink" style={{ background: 'rgb(var(--c-ink))' }}>
                <div className="h-full" style={{ width: `${prediction.confidence * 100}%`, background: 'rgb(var(--c-accent))' }} />
              </div>
              <div className="flex items-center justify-between"><span className="t2">Wind</span>
                <span className="font-semibold">{prediction.wind_kts.toFixed(1)} kt <span className="font-normal t2">(track {fix.wind_kts} kt)</span></span></div>
              <div className="flex items-center justify-between"><span className="t2">Next 6h</span>
                <span className="font-semibold text-red-400">{prediction.next_6h.lat}, {prediction.next_6h.lon}</span></div>
              <div className="flex items-center justify-between"><span className="t2">Uncertainty</span><span>±{prediction.uncertainty_km} km</span></div>
              {next && <p className="rounded-lg p-2 text-xs t2" style={{ background: 'rgb(var(--c-ink))' }}>
                Actual next: {parseFloat(next.latitude).toFixed(2)}, {parseFloat(next.longitude).toFixed(2)} — IBTrACS verification.</p>}
            </div>
          )}
        </div>
        <div className="card p-4">
          <h3 className="mb-2 text-sm font-semibold t2">Fix details</h3>
          <dl className="space-y-1.5 text-sm">
            {[['Time', fix.timestamp?.replace('T', ' ').slice(0, 16) + ' UTC'],
              ['Position', `${parseFloat(fix.latitude).toFixed(2)}°, ${parseFloat(fix.longitude).toFixed(2)}°`],
              ['Best-track wind', `${fix.wind_kts} kt`], ['Best-track class', fix.derived_class],
              ['Pressure', fix.pressure_hpa ? `${fix.pressure_hpa} hPa` : '—'], ['Source', fix.satellite_source],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between gap-2"><dt className="t2">{k}</dt><dd className="text-right font-medium t1">{v}</dd></div>
            ))}
          </dl>
        </div>
      </section>

      <TrackMap fixes={detail.fixes} index={index} prediction={prediction} mapStyle={style} />
      <IntensityChart fixes={detail.fixes} index={index} mlWind={prediction?.wind_kts} />
      <EvidencePanel prediction={prediction ? { class: prediction.class, confidence: prediction.confidence,
        wind_kts: prediction.wind_kts, next_6h: prediction.next_6h, uncertainty_km: prediction.uncertainty_km } : null} />
      <p className="pb-6 text-center text-xs t2">Ground truth: NOAA IBTrACS best-track · Not an official warning — follow IMD advisories.</p>
    </div>
  )
}
