import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth, isSpecialist } from '../auth'
import { useTheme } from '../theme'

export default function Navbar() {
  const { user, logout } = useAuth()
  const { theme, toggle } = useTheme()
  const nav = useNavigate()
  const link = ({ isActive }) => `px-3 py-1.5 rounded-lg text-sm ${isActive ? 'bg-accent text-ink font-semibold' : 't2 hover:t1'}`

  return (
    <header className="sticky top-0 z-50 border-b border-line bg-panel/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center gap-2 px-4 py-3">
        <Link to="/dashboard" className="mr-2 flex items-center gap-2">
          <span className="text-2xl">🌀</span>
          <span className="text-lg font-bold tracking-wide t1">MEGH</span>
        </Link>
        <nav className="flex items-center gap-1">
          <NavLink to="/dashboard" className={link}>Dashboard</NavLink>
          <NavLink to="/cyclones" className={link}>Cyclones</NavLink>
          <NavLink to="/methodology" className={link}>How it works</NavLink>
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <button onClick={toggle} title="Toggle light / dark" className="btn-ghost !px-3">
            {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
          </button>
          {!user ? (
            <>
              <button onClick={() => nav('/login')} className="btn-ghost">Login</button>
              <button onClick={() => nav('/signup')} className="btn-primary">Sign up</button>
            </>
          ) : (
            <>
              <span className="hidden text-xs t2 sm:inline">
                {user.name} · {isSpecialist(user) ? 'Specialist' : 'Viewer'}
              </span>
              <button onClick={() => { logout(); nav('/dashboard') }} className="btn-ghost">Logout</button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
