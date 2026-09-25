import { createContext, useContext, useEffect, useState } from 'react'
import { api, getToken, setToken } from './api'

// Server-backed sessions: token in localStorage, identity verified by /auth/me.
// Roles: viewer (public user) vs specialist sub-roles (analyst, researcher).
const AuthCtx = createContext({ user: null, login: async () => {}, signup: async () => {}, logout: () => {} })

export const ROLES = {
  viewer: { label: 'Viewer', desc: 'Track storms, view analysis and evidence.' },
  analyst: { label: 'Analyst', desc: 'Verification metrics, baselines, provenance.' },
  researcher: { label: 'Researcher', desc: 'Model internals, evaluation, RAG sources.' },
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    if (!getToken()) { setReady(true); return }
    api.me().then((d) => setUser(d.user)).catch(() => setToken(null)).finally(() => setReady(true))
  }, [])

  async function login(name, password) {
    const d = await api.login(name, password)
    setToken(d.token)
    setUser(d.user)
    return d.user
  }

  async function signup(name, password, role) {
    const d = await api.signup(name, password, role)
    setToken(d.token)
    setUser(d.user)
    return d.user
  }

  function logout() {
    api.logout().catch(() => {})
    setToken(null)
    setUser(null)
  }

  return <AuthCtx.Provider value={{ user, ready, login, signup, logout }}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)
export const isSpecialist = (u) => u && (u.role === 'analyst' || u.role === 'researcher')
