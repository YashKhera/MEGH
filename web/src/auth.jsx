import { createContext, useContext, useEffect, useState } from 'react'

// Roles: viewer (public user) vs specialist sub-roles (analyst, researcher).
// Stored locally; the backend stays open for the demo deployment.
const AuthCtx = createContext({ user: null, login: () => {}, signup: () => {}, logout: () => {} })

export const ROLES = {
  viewer: { label: 'Viewer', desc: 'Track storms, view analysis and evidence.' },
  analyst: { label: 'Analyst', desc: 'Verification metrics, baselines, provenance.' },
  researcher: { label: 'Researcher', desc: 'Model internals, evaluation, RAG sources.' },
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('megh-user')) } catch { return null }
  })
  useEffect(() => {
    if (user) localStorage.setItem('megh-user', JSON.stringify(user))
    else localStorage.removeItem('megh-user')
  }, [user])
  return (
    <AuthCtx.Provider value={{
      user,
      login: (name, role) => setUser({ name, role }),
      signup: (name, role) => setUser({ name, role }),
      logout: () => setUser(null),
    }}>{children}</AuthCtx.Provider>
  )
}

export const useAuth = () => useContext(AuthCtx)
export const isSpecialist = (u) => u && (u.role === 'analyst' || u.role === 'researcher')
