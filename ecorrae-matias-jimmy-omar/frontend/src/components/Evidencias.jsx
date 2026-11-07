import { useRef, useState } from 'react'
import { api } from '../api'
import { fecha } from '../constantes'
import { Confirmar, useCarga, useToast } from './ui'

const PERMITIDOS = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf']
const MAX_MB = 10


export default function Evidencias({ dispositivoId, loteId, onCambio }) {
  const filtro = dispositivoId ? { dispositivo_id: dispositivoId } : { lote_id: loteId }
  const { datos, recargar } = useCarga(() => api.get('/evidencias', filtro), [dispositivoId, loteId])
  const [descripcion, setDescripcion] = useState('')
  const [error, setError] = useState(null)
  const [subiendo, setSubiendo] = useState(false)
  const [borrar, setBorrar] = useState(null)
  const archivo = useRef()
  const toast = useToast()

  const subir = async (e) => {
    e.preventDefault()
    const f = archivo.current.files[0]
    if (!f) return setError('Seleccione un archivo')
    if (!PERMITIDOS.includes(f.type)) return setError('Solo se permiten JPG, PNG, WEBP o PDF')
    if (f.size > MAX_MB * 1024 * 1024) return setError(`El archivo supera ${MAX_MB} MB`)
    const fd = new FormData()
    fd.append('archivo', f)
    Object.entries(filtro).forEach(([k, v]) => fd.append(k, v))
    if (descripcion.trim()) fd.append('descripcion', descripcion.trim())
    setSubiendo(true); setError(null)
    try {
      await api.upload('/evidencias', fd)
      toast('Evidencia cargada')
      archivo.current.value = ''; setDescripcion('')
      recargar(); onCambio?.()
    } catch (ex) { setError(ex.message) } finally { setSubiendo(false) }
  }

  return (
    <div>
      <form className="fila-upload" onSubmit={subir}>
        <input type="file" ref={archivo} accept=".jpg,.jpeg,.png,.webp,.pdf" />
        <input type="text" placeholder="Descripción (opcional)" maxLength={255} value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
        <button className="btn btn-primario" disabled={subiendo}>{subiendo ? 'Subiendo…' : 'Subir'}</button>
      </form>
      {error && <div className="alerta alerta-error">{error}</div>}
      {datos?.length ? (
        <ul className="lista-evid">
          {datos.map((e) => (
            <li key={e.id}>
              <a href={api.url(`/evidencias/${e.id}/archivo`)} target="_blank" rel="noreferrer">
                {e.tipo_mime === 'application/pdf' ? '📄' : '🖼️'} {e.nombre_archivo}
              </a>
              <span className="muted"> {e.descripcion ? `· ${e.descripcion} ` : ''}· {(e.tamano_bytes / 1024).toFixed(1)} KB · {fecha(e.fecha)}</span>
              <button className="btn-link peligro" onClick={() => setBorrar(e)}>Eliminar</button>
            </li>
          ))}
        </ul>
      ) : <p className="muted">Sin evidencias adjuntas.</p>}
      {borrar && (
        <Confirmar texto={`¿Eliminar la evidencia "${borrar.nombre_archivo}"?`} onNo={() => setBorrar(null)}
          onSi={async () => {
            try { await api.del(`/evidencias/${borrar.id}`); toast('Evidencia eliminada'); recargar(); onCambio?.() }
            catch (ex) { toast(ex.message, 'error') }
            setBorrar(null)
          }} />
      )}
    </div>
  )
}
