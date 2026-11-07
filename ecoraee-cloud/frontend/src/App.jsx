import { useEffect, useState } from 'react'
import { NavLink, Route, Routes } from 'react-router-dom'
import { api } from './api'
import Catalogo from './pages/Catalogo'
import Dashboard from './pages/Dashboard'
import DispositivoDetalle from './pages/DispositivoDetalle'
import Dispositivos from './pages/Dispositivos'
import Evaluaciones from './pages/Evaluaciones'
import LoteDetalle from './pages/LoteDetalle'
import Lotes from './pages/Lotes'
import Movimientos from './pages/Movimientos'

const MENU = [
  ['Trazabilidad', [['/', 'Panel', '📊'], ['/dispositivos', 'Dispositivos', '💻'], ['/evaluaciones', 'Evaluaciones', '🔍'], ['/lotes', 'Lotes', '📦'], ['/movimientos', 'Movimientos', '🚚']]],
  ['Catálogos', [['/centros', 'Centros', '🏭'], ['/destinos', 'Destinos', '♻️'], ['/usuarios', 'Usuarios', '👤']]],
]

function EstadoBackend() {
  const [ok, setOk] = useState(null)
  useEffect(() => {
    const ver = () => api.get('/health').then(() => setOk(true)).catch(() => setOk(false))
    ver()
    const t = setInterval(ver, 15000)
    return () => clearInterval(t)
  }, [])
  return (
    <div className={`backend-estado ${ok ? 'on' : ok === false ? 'off' : ''}`}>
      <span className="punto" /> {ok ? 'API + BD conectadas' : ok === false ? 'Backend sin conexión' : 'Verificando…'}
    </div>
  )
}

export default function App() {
  return (
    <div className="app">
      <aside className="lateral">
        <div className="marca"><span>♻️</span><div><b>EcoRAEE</b> Cloud<small>Trazabilidad de RAEE</small></div></div>
        <nav>
          {MENU.map(([grupo, items]) => (
            <div key={grupo}>
              <div className="nav-grupo">{grupo}</div>
              {items.map(([ruta, texto, icono]) => (
                <NavLink key={ruta} to={ruta} end={ruta === '/'} className={({ isActive }) => (isActive ? 'activo' : '')}>
                  <span>{icono}</span> {texto}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <EstadoBackend />
      </aside>
      <main className="contenido">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dispositivos" element={<Dispositivos />} />
          <Route path="/dispositivos/:id" element={<DispositivoDetalle />} />
          <Route path="/evaluaciones" element={<Evaluaciones />} />
          <Route path="/lotes" element={<Lotes />} />
          <Route path="/lotes/:id" element={<LoteDetalle />} />
          <Route path="/movimientos" element={<Movimientos />} />
          {['centros', 'destinos', 'usuarios'].map((r) => (
            <Route key={r} path={`/${r}`} element={<Catalogo key={r} recurso={r} />} />
          ))}
          <Route path="*" element={<div className="vacio">Página no encontrada</div>} />
        </Routes>
      </main>
    </div>
  )
}
