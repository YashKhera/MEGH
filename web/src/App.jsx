import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Navbar from './components/Navbar'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import Cyclones from './pages/Cyclones'
import CycloneDetail from './pages/CycloneDetail'
import Methodology from './pages/Methodology'
import { Login, Signup } from './pages/Auth'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen">
        <Navbar />
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Landing />} />
          <Route path="/workspace" element={<Dashboard />} />
          <Route path="/cyclones" element={<Cyclones />} />
          <Route path="/cyclone/:id" element={<CycloneDetail />} />
          <Route path="/methodology" element={<Methodology />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
        <footer className="border-t border-line py-4 text-center text-xs t2">
          MEGH · Meteorological &amp; Environmental Geospatial Hub · IBTrACS-verified analysis ·
          not an official warning — follow IMD advisories.
        </footer>
      </div>
    </BrowserRouter>
  )
}
