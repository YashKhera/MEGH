import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

export function Login() {
  const { login } = useAuth()
  const nav = useNavigate()
  const [name, setName] = useState('')
  const [role, setRole] = useState('viewer')
  return (
    <div className="mx-auto max-w-md px-4 py-14">
      <div className="card p-6">
        <h1 className="text-2xl font-extrabold t1">Welcome back</h1>
        <p className="mt-1 text-sm t2">Log in to your MEGH workspace.</p>
        <label className="mt-4 block text-xs t2">Display name</label>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Ananya" className="input mt-1" />
        <label className="mt-3 block text-xs t2">Workspace</label>
        <select value={role} onChange={(e) => setRole(e.target.value)} className="input mt-1">
          <option value="viewer">Viewer — public storm tracking</option>
          <option value="analyst">Specialist · Analyst — verification & baselines</option>
          <option value="researcher">Specialist · Researcher — models & evidence</option>
        </select>
        <button onClick={() => { login(name.trim() || 'Guest', role); nav('/dashboard') }} className="btn-primary mt-5 w-full !py-2.5">
          Login →
        </button>
        <p className="mt-3 text-center text-xs t2">New here? <Link to="/signup" className="t-accent">Create an account</Link></p>
      </div>
    </div>
  )
}

export function Signup() {
  const { signup } = useAuth()
  const nav = useNavigate()
  const [name, setName] = useState('')
  const [role, setRole] = useState('viewer')
  const roles = [
    ['viewer', 'Viewer', 'Follow cyclones, replay tracks, read evidence.'],
    ['analyst', 'Specialist · Analyst', 'Held-out verification, baseline skill, provenance.'],
    ['researcher', 'Specialist · Researcher', 'Model internals, evaluation tables, RAG sources.'],
  ]
  return (
    <div className="mx-auto max-w-lg px-4 py-14">
      <div className="card p-6">
        <h1 className="text-2xl font-extrabold t1">Join MEGH</h1>
        <p className="mt-1 text-sm t2">One account, workspaces tuned to how you work.</p>
        <label className="mt-4 block text-xs t2">Display name</label>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Arjun" className="input mt-1" />
        <div className="mt-4 space-y-2">
          {roles.map(([v, t, d]) => (
            <button key={v} onClick={() => setRole(v)}
              className={`block w-full rounded-lg border p-3 text-left ${role === v ? 'border-accent' : 'border-line'}`}>
              <div className="text-sm font-semibold t1">{t}</div>
              <div className="text-xs t2">{d}</div>
            </button>
          ))}
        </div>
        <button onClick={() => { signup(name.trim() || 'Guest', role); nav('/dashboard') }} className="btn-primary mt-5 w-full !py-2.5">
          Create account →
        </button>
        <p className="mt-3 text-center text-xs t2">Have an account? <Link to="/login" className="t-accent">Log in</Link></p>
      </div>
    </div>
  )
}
