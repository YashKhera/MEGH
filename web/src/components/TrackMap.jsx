import { useEffect, useRef } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

// Basemap follows the theme (positron for light, dark-matter for dark); no API key.
const DEFAULT_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'

function line(id, coords, color, width) {
  return {
    id,
    type: 'line',
    source: { type: 'geojson', data: { type: 'Feature', geometry: { type: 'LineString', coordinates: coords } } },
    paint: { 'line-color': color, 'line-width': width },
  }
}

function marker(id, coord, color, label) {
  return {
    id,
    type: 'circle',
    source: { type: 'geojson', data: { type: 'FeatureCollection', features: [
      { type: 'Feature', geometry: { type: 'Point', coordinates: coord }, properties: { label } },
    ] } },
    paint: { 'circle-radius': 8, 'circle-color': color, 'circle-stroke-color': '#fff', 'circle-stroke-width': 1.5 },
  }
}

export default function TrackMap({ fixes, index, prediction, mapStyle }) {
  const ref = useRef(null)
  const mapRef = useRef(null)

  const travelled = fixes.slice(0, index + 1).map((f) => [parseFloat(f.longitude), parseFloat(f.latitude)])
  const full = fixes.map((f) => [parseFloat(f.longitude), parseFloat(f.latitude)])
  const center = travelled[travelled.length - 1]

  useEffect(() => {
    const map = new maplibregl.Map({ container: ref.current, style: mapStyle || DEFAULT_STYLE, center, zoom: 4 })
    mapRef.current = map
    map.on('load', () => {
      map.addLayer(line('full', full, '#64748b', 1.5))
      map.addLayer(line('travelled', travelled, '#38bdf8', 3))
      if (prediction) {
        const { next_6h, persistence_6h } = prediction
        map.addLayer(marker('megh', [next_6h.lon, next_6h.lat], '#ef4444'))
        map.addLayer(marker('persist', [persistence_6h.lon, persistence_6h.lat], '#f59e0b'))
        new maplibregl.Popup({ closeOnClick: false })
          .setLngLat([next_6h.lon, next_6h.lat])
          .setHTML(`<b>MEGH 6h</b><br>${next_6h.lat}, ${next_6h.lon}`)
          .addTo(map)
      }
      if (index + 1 < fixes.length) {
        const n = fixes[index + 1]
        map.addLayer(marker('actual', [parseFloat(n.longitude), parseFloat(n.latitude)], '#22c55e'))
      }
    })
    return () => map.remove()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fixes[0]?.storm_id, index, prediction?.next_6h?.lat, prediction?.next_6h?.lon])

  return <div ref={ref} className="h-[420px] w-full rounded-xl border border-line" />
}
