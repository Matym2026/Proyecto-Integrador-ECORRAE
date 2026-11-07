import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { etiqueta } from '../constantes'

/* ---------- Notificaciones (toasts) ---------- */
const ToastCtx = createContext(() => {})
export const useToast = () => useContext(ToastCtx)

export function ToastProvider({ children }) {
  const [items, setItems] = useState([])
  const notificar = useCallback((texto, tipo = 'ok') => {
    const id = Math.random()
    setItems((x) => [...x, { id, texto, tipo }])
    setTimeout(() => setItems((x) => x.filter((i) => i.id !== id)), tipo === 'error' ? 6000 : 3500)
  }, [])
  return (
    <ToastCtx.Provider value={notificar}>
      {children}
      <div className="toasts">
        {items.map((t) => <div key={t.id} className={`toast toast-${t.tipo}`}>{t.texto}</div>)}
      </div>
    </ToastCtx.Provider>
  )
}

/* ---------- Carga de datos ---------- */
export function useCarga(fn, deps = []) {
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState(null)
  const [cargando, setCargando] = useState(true)
  const recargar = useCallback(() => {
    setCargando(true)
    return fn().then((d) => { setDatos(d); setError(null) })
      .catch((e) => setError(e.message)).finally(() => setCargando(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  useEffect(() => { recargar() }, [recargar])
  return { datos, error, cargando, recargar }
}

export function Estado({ cargando, error, vacio, children }) {
  if (error) return <div className="alerta alerta-error">{error}</div>
  if (cargando && !children) return <div className="cargando">Cargando…</div>
  if (vacio) return <div className="vacio">No hay registros para mostrar.</div>
  return children
}

/* ---------- Modal y confirmación ---------- */
export function Modal({ titulo, onClose, children, ancho }) {
  useEffect(() => {
    const esc = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', esc)
    return () => window.removeEventListener('keydown', esc)
  }, [onClose])
  return (
    <div className="modal-fondo" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" style={ancho ? { maxWidth: ancho } : undefined}>
        <div className="modal-cab">
          <h3>{titulo}</h3>
          <button className="btn-icono" onClick={onClose} aria-label="Cerrar">✕</button>
        </div>
        <div className="modal-cuerpo">{children}</div>
      </div>
    </div>
  )
}

export function Confirmar({ texto, onSi, onNo, peligro = true }) {
  const [ocupado, setOcupado] = useState(false)
  return (
    <Modal titulo="Confirmar" onClose={onNo} ancho={420}>
      <p>{texto}</p>
      <div className="acciones-form">
        <button className="btn" onClick={onNo}>Cancelar</button>
        <button className={`btn ${peligro ? 'btn-peligro' : 'btn-primario'}`} disabled={ocupado}
          onClick={async () => { setOcupado(true); await onSi(); setOcupado(false) }}>
          {ocupado ? 'Procesando…' : 'Confirmar'}
        </button>
      </div>
    </Modal>
  )
}

/* ---------- Insignias de estado ---------- */
const COLORES = {
  REGISTRADO: 'gris', EVALUADO: 'azul', EN_LOTE: 'ambar', EN_DESTINO: 'verde',
  ABIERTO: 'azul', CERRADO: 'ambar', ENTREGADO: 'verde',
  INGRESO: 'gris', TRASLADO: 'ambar', ENTREGA_DESTINO: 'verde',
  REUTILIZACION: 'verde', RECICLAJE: 'azul', DISPOSICION_FINAL: 'rojo', DONACION: 'verde',
  BUENO: 'verde', REGULAR: 'ambar', MALO: 'rojo',
  ADMIN: 'rojo', OPERADOR: 'azul', EVALUADOR: 'verde', AUDITOR: 'gris',
}
export const Badge = ({ v }) => <span className={`badge badge-${COLORES[v] || 'gris'}`}>{etiqueta(v)}</span>

export const Si = ({ v }) => (v ? <span className="si">Sí</span> : <span className="no">No</span>)
