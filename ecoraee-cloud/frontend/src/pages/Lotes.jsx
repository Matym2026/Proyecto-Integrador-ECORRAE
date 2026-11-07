import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { ESTADOS_LOTE, fecha, kg } from '../constantes'
import Formulario from '../components/Formulario'
import { useCatalogos } from '../components/formularios'
import { Badge, Estado, Modal, useCarga, useToast } from '../components/ui'

export default function Lotes() {
  const [estado, setEstado] = useState('')
  const { datos, error, cargando, recargar } = useCarga(() => api.get('/lotes', { estado }), [estado])
  const [nuevo, setNuevo] = useState(false)
  const cat = useCatalogos()
  const toast = useToast()
  const navigate = useNavigate()

  return (
    <>
      <div className="cabecera">
        <h1>Lotes</h1>
        <button className="btn btn-primario" onClick={() => setNuevo(true)}>+ Nuevo lote</button>
      </div>
      <div className="filtros">
        <select value={estado} onChange={(e) => setEstado(e.target.value)}>
          <option value="">Todos los estados</option>
          {ESTADOS_LOTE.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>
      <Estado cargando={cargando} error={error} vacio={datos && !datos.length}>
        {datos && (
          <div className="tarjeta sin-padding">
            <table className="tabla">
              <thead><tr><th>Código</th><th>Descripción</th><th>Estado</th><th>Centro</th><th>Dispositivos</th><th>Peso</th><th>Destino</th><th>Creación</th></tr></thead>
              <tbody>
                {datos.map((l) => (
                  <tr key={l.id} className="clic" onClick={() => navigate(`/lotes/${l.id}`)}>
                    <td><b>{l.codigo}</b></td><td>{l.descripcion}</td><td><Badge v={l.estado} /></td>
                    <td>{l.centro.nombre}</td><td>{l.total_dispositivos}</td><td className="nowrap">{kg(l.peso_total_kg)}</td>
                    <td>{l.destino?.nombre || '—'}</td><td className="muted nowrap">{fecha(l.fecha_creacion)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Estado>
      {nuevo && (
        <Modal titulo="Nuevo lote" onClose={() => setNuevo(false)}>
          <p className="muted">El código se genera automáticamente si lo deja vacío (LOTE-AAAA-NNN).</p>
          <Formulario
            campos={[
              { name: 'codigo', label: 'Código', pattern: '^LOTE-[0-9]{4}-[0-9]{3,}$', patternMsg: 'Formato LOTE-2026-001', placeholder: 'Automático' },
              { name: 'centro_id', label: 'Centro donde se consolida', type: 'select', required: true, numerico: true, options: cat.centros },
              { name: 'creado_por', label: 'Creado por', type: 'select', numerico: true, options: cat.usuarios },
              { name: 'descripcion', label: 'Descripción', type: 'textarea', maxLength: 255 },
            ]}
            onCancel={() => setNuevo(false)}
            onSubmit={async (d) => {
              const l = await api.post('/lotes', d)
              toast(`Lote ${l.codigo} creado`); setNuevo(false); recargar(); navigate(`/lotes/${l.id}`)
            }} />
        </Modal>
      )}
    </>
  )
}
