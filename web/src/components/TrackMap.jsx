import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

// Basemap follows the theme (positron for light, dark-matter for dark); no API key.
const DEFAULT_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'

const pt = (lon, lat) => ({
  type: 'FeatureCollection',
  features: lon == null || lat == null ? [] : [
    { type: 'Feature', geometry: { type: 'Point', coordinates: [lon, lat] }, properties: {} },
  ],
})
const line = (coords) => ({ type: 'Feature', geometry: { type: 'LineString', coordinates: coords } })

export default function TrackMap({ fixes, index, prediction, mapStyle }) {
  const ref = useRef(null)
  const mapRef = useRef(null)
  const popupRef = useRef(null)
  const [ready, setReady] = useState(false)
  const [failed, setFailed] = useState(null)
  const [retry, setRetry] = useState(0)
  const sid = fixes[0]?.storm_id
  const style = mapStyle || DEFAULT_STYLE

  // Create once per storm / basemap style.
  useEffect(() => {
    setReady(false)
    setFailed(null)
    const map = new maplibregl.Map({ container: ref.current, style, center: [82, 15], zoom: 4 })
    mapRef.current = map
    map.on('error', (e) => setFailed(e?.error?.message || 'map failed to load'))
    map.on('load', () => {
      map.addSource('full', { type: 'geojson', data: line([]) })
      map.addSource('travelled', { type: 'geojson', data: line([]) })
      map.addSource('megh', { type: 'geojson', data: pt(0, 0) })
      map.addSource('persist', { type: 'geojson', data: pt(0, 0) })
      map.addSource('actual', { type: 'geojson', data: pt(0, 0) })
      map.addLayer({ id: 'full', type: 'line', source: 'full', paint: { 'line-color': '#64748b', 'line-width': 1.5 } })
      map.addLayer({ id: 'travelled', type: 'line', source: 'travelled', paint: { 'line-color': '#38bdf8', 'line-width': 3 } })
      for (const [id, color, size] of [['megh', '#ef4444', 8], ['persist', '#f59e0b', 7], ['actual', '#22c55e', 8]]) {
        map.addLayer({ id, type: 'circle', source: id,
          paint: { 'circle-radius': size, 'circle-color': color, 'circle-stroke-color': '#fff', 'circle-stroke-width': 1.5 } })
      }
      setReady(true)
    })
    return () => { popupRef.current?.remove(); map.remove(); mapRef.current = null }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sid, style, retry])

  // Push data into live sources — no rebuild while scrubbing / replaying.
  useEffect(() => {
    const map = mapRef.current
    if (!map || !ready) return
    const full = fixes.map((f) => [parseFloat(f.longitude), parseFloat(f.latitude)])
    const travelled = full.slice(0, index + 1)
    map.getSource('full').setData(line(full))
    map.getSource('travelled').setData(line(travelled))
    const cur = travelled[travelled.length - 1]
    if (cur) map.easeTo({ center: cur, duration: 400 })
    const show = (id, lon, lat) => {
      map.getSource(id).setData(pt(lon, lat))
      map.setLayoutProperty(id, 'visibility', lon == null ? 'none' : 'visible')
    }
    if (prediction) {
      const { next_6h, persistence_6h } = prediction
      show('megh', next_6h.lon, next_6h.lat)
      show('persist', persistence_6h.lon, persistence_6h.lat)
      popupRef.current?.remove()
      popupRef.current = new maplibregl.Popup({ closeOnClick: false })
        .setLngLat([next_6h.lon, next_6h.lat])
        .setHTML(`<b>MEGH 6h</b><br>${next_6h.lat}, ${next_6h.lon}`)
        .addTo(map)
    } else {
      show('megh', null); show('persist', null)
    }
    if (index + 1 < fixes.length) {
      const n = fixes[index + 1]
      show('actual', parseFloat(n.longitude), parseFloat(n.latitude))
    } else {
      show('actual', null)
    }
  }, [fixes, index, prediction, ready])

  if (failed) {
    const lons = fixes.map((f) => parseFloat(f.longitude))
    const lats = fixes.map((f) => parseFloat(f.latitude))
    const x0 = Math.min(...lons) - 2, x1 = Math.max(...lons) + 2
    const y0 = Math.min(...lats) - 2, y1 = Math.max(...lats) + 2
    const X = (v) => ((v - x0) / (x1 - x0)) * 400
    const Y = (v) => 300 - ((v - y0) / (y1 - y0)) * 300
    const coords = fixes.map((f) => `${X(parseFloat(f.longitude))},${Y(parseFloat(f.latitude))}`).join(' ')
    return (
      <div className="card p-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-red-400">Interactive map unavailable ({failed}). Static track:</p>
          <button onClick={() => { setFailed(null); setRetry((r) => r + 1) }} className="btn-ghost !py-1 text-xs">
            Retry map
          </button>
        </div>
        <svg viewBox="0 0 400 300" className="mt-2 w-full rounded-lg" style={{ background: 'rgb(var(--c-ink))' }}>
          <polyline points={coords} fill="none" stroke="#38bdf8" strokeWidth="2" />
          {prediction && <circle cx={X(prediction.next_6h.lon)} cy={Y(prediction.next_6h.lat)} r="6" fill="#ef4444" />}
        </svg>
      </div>
    )
  }
  return <div ref={ref} className="h-[420px] w-full rounded-xl border border-line" />
}
