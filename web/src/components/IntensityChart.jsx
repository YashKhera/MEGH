import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceDot, CartesianGrid } from 'recharts'

export default function IntensityChart({ fixes, index, mlWind }) {
  const data = fixes.map((f, i) => ({
    i,
    t: (f.timestamp || '').slice(5, 16).replace('T', ' '),
    wind: parseFloat(f.wind_kts),
  }))
  return (
    <div className="card p-4">
      <h3 className="mb-2 text-sm font-semibold t2">Intensity timeline — wind (kt, 6-hourly)</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid stroke="rgb(var(--c-line))" />
          <XAxis dataKey="i" stroke="rgb(var(--c-muted))" tick={{ fontSize: 11, fill: 'rgb(var(--c-muted))' }} />
          <YAxis stroke="rgb(var(--c-muted))" tick={{ fontSize: 11, fill: 'rgb(var(--c-muted))' }} />
          <Tooltip contentStyle={{ background: 'rgb(var(--c-panel))', border: '1px solid rgb(var(--c-line))' }} />
          <Line type="monotone" dataKey="wind" stroke="#38bdf8" dot={false} strokeWidth={2} name="Best-track wind" />
          {mlWind != null && (
            <ReferenceDot x={index} y={mlWind} r={6} fill="#ef4444" stroke="#fff" label={{ value: `ML ${mlWind.toFixed(0)}`, fill: '#fca5a5', fontSize: 11 }} />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
