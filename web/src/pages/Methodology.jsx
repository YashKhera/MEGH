import { motion } from 'framer-motion'

const ARCH = [
  ['Satellite + best-track ingest', 'IBTrACS fixes aligned to storm-centred frames; full provenance per observation.'],
  ['Vision & intensity models', 'Transfer-learning CNN (ResNet18) with intensity + wind heads; numpy baselines as fallback.'],
  ['Track forecasting', '6-hour displacement model scored against a persistence baseline in great-circle km.'],
  ['Storm-level evaluation', 'Entire storms held out — test cyclones are never seen in training. No frame leakage.'],
  ['Evidence layer', 'FastAPI → TF-IDF retriever → (LLM or template). The language model explains; it never predicts numbers.'],
]

const LIMITS = [
  'Research and decision-support analysis — not an operational warning service.',
  'Frames are currently synthetic proxies (SYN_PROXY) until HURSAT / INSAT-3D ingest lands.',
  'Basin-tuned to the North Indian Ocean; other basins need recalibration.',
  'Labels carry historical reanalysis uncertainty from IBTrACS.',
]

export default function Methodology() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-10">
      <div>
        <h1 className="text-3xl font-extrabold t1">How MEGH works</h1>
        <p className="mt-2 text-sm t2">The full pipeline, honestly stated — what each part does and where it can be wrong.</p>
      </div>
      <div className="space-y-3">
        {ARCH.map(([t, d], i) => (
          <motion.div key={t} initial={{ opacity: 0, x: -16 }} whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }} transition={{ delay: i * 0.05 }} className="card flex gap-4 p-4">
            <span className="text-xl font-extrabold t-accent">0{i + 1}</span>
            <div><div className="font-semibold t1">{t}</div><div className="text-sm t2">{d}</div></div>
          </motion.div>
        ))}
      </div>
      <div className="card border-red-900 p-4">
        <h2 className="font-semibold text-red-400">Limits, stated plainly</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm t2">
          {LIMITS.map((l) => <li key={l}>{l}</li>)}
        </ul>
      </div>
    </div>
  )
}
