import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceDot, CartesianGrid } from 'recharts'

export default function IntensityChart({ fixes, index, mlWind }) {
  const data = fixes.map((f, i) => ({
    i,
    t: (f.timestamp || '').slice(5, 16).replace('T', ' '),
    wind: parseFloat(f.wind_kts),
  }))
  return (
    <div className="rounded-xl border border-line bg-panel p-4">
      <h3 className="mb-2 text-sm font-semibold text-slate-300">Intensity timeline — wind (kt, 6-hourly)</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid stroke="#1e2a45" />
          <XAxis dataKey="i" stroke="#94a3b8" tick={{ fontSize: 11 }} />
          <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
          <Tooltip contentStyle={{ background: '#111a2e', border: '1px solid #1e2a45' }} />
          <Line type="monotone" dataKey="wind" stroke="#38bdf8" dot={false} strokeWidth={2} name="Best-track wind" />
          {mlWind != null && (
            <ReferenceDot x={index} y={mlWind} r={6} fill="#ef4444" stroke="#fff" label={{ value: `ML ${mlWind.toFixed(0)}`, fill: '#fca5a5', fontSize: 11 }} />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
