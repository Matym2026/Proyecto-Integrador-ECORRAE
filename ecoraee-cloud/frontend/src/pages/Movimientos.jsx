import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { TIPOS_MOVIMIENTO, fecha } from '../constantes'
import Formulario from '../components/Formulario'
import { Badge, Estado, Modal, useCarga, useToast } from '../components/ui'

export default function Movimientos() {
  const [tipo, setTipo] = useState('')
  const { datos, error, cargando, recargar } = useCarga(() => api.get('/movimientos', { tipo }), [tipo])
  const [editar, setEditar] = useState(null)
  const toast = useToast()

  return (
    <>
      <div className="cabecera">
        <h1>Movimientos</h1>
      </div>
      <p className="muted">Registro de auditoría de la trazabilidad. Los traslados y entregas se registran desde el detalle de cada dispositivo o lote; aquí solo se corrigen la guía y las observaciones.</p>
      <div className="filtros">
        <select value={tipo} onChange={(e) => setTipo(e.target.value)}>
          <option value="">Todos los tipos</option>
          {TIPOS_MOVIMIENTO.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>
      <Estado cargando={cargando} error={error} vacio={datos && !datos.length}>
        {datos && (
          <div className="tarjeta sin-padding">
            <table className="tabla">
              <thead><tr><th>Fecha</th><th>Tipo</th><th>Sujeto</th><th>Origen</th><th>Destino</th><th>Responsable</th><th>Guía</th><th></th></tr></thead>
              <tbody>
                {datos.map((m) => (
                  <tr key={m.id}>
                    <td className="nowrap">{fecha(m.fecha)}</td><td><Badge v={m.tipo} /></td>
                    <td>{m.lote ? <Link to={`/lotes/${m.lote_id}`}>Lote {m.lote.codigo}</Link>
                      : <Link to={`/dispositivos/${m.dispositivo_id}`}>{m.dispositivo?.codigo_trazabilidad}</Link>}</td>
                    <td>{m.centro_origen?.nombre || '—'}</td>
                    <td>{m.destino ? <b>{m.destino.nombre}</b> : m.centro_destino?.nombre}</td>
                    <td>{m.responsable?.nombre || '—'}</td><td className="muted">{m.guia_remision || '—'}</td>
                    <td className="acciones"><button className="btn-link" onClick={() => setEditar(m)}>Corregir</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Estado>
      {editar && (
        <Modal titulo="Corregir movimiento" onClose={() => setEditar(null)}>
          <Formulario inicial={editar} onCancel={() => setEditar(null)}
            campos={[
              { name: 'guia_remision', label: 'Guía de remisión', maxLength: 40 },
              { name: 'observaciones', label: 'Observaciones', type: 'textarea' },
            ]}
            onSubmit={async (d) => { await api.patch(`/movimientos/${editar.id}`, d); toast('Movimiento actualizado'); setEditar(null); recargar() }} />
        </Modal>
      )}
    </>
  )
}
