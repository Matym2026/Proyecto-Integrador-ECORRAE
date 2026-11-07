import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import { ESTADOS_DISPOSITIVO, TIPOS_DISPOSITIVO, etiqueta, fecha, kg } from '../constantes'
import { FormDispositivo, useCatalogos } from '../components/formularios'
import { Badge, Confirmar, Estado, Modal, useCarga, useToast } from '../components/ui'

export default function Dispositivos() {
  const [params, setParams] = useSearchParams()
  const filtros = { q: params.get('q') || '', estado: params.get('estado') || '', tipo: params.get('tipo') || '', centro_id: params.get('centro_id') || '' }
  const { datos, error, cargando, recargar } = useCarga(() => api.get('/dispositivos', filtros), [params.toString()])
  const cat = useCatalogos()
  const [form, setForm] = useState(null) 
  const [borrar, setBorrar] = useState(null)
  const toast = useToast()
  const navigate = useNavigate()

  const filtrar = (k, v) => { const p = new URLSearchParams(params); v ? p.set(k, v) : p.delete(k); setParams(p) }

  const guardar = async (d) => {
    if (form.id) {
      await api.put(`/dispositivos/${form.id}`, d)
      toast('Dispositivo actualizado')
    } else {
      const nuevo = await api.post('/dispositivos', d)
      toast(`Dispositivo ${nuevo.codigo_trazabilidad} registrado`)
    }
    setForm(null); recargar()
  }

  return (
    <>
      <div className="cabecera">
        <h1>Dispositivos RAEE</h1>
        <button className="btn btn-primario" onClick={() => setForm({})}>+ Registrar dispositivo</button>
      </div>

      <div className="filtros">
        <input type="search" placeholder="Buscar código, marca, modelo o serie…" defaultValue={filtros.q}
          onKeyDown={(e) => e.key === 'Enter' && filtrar('q', e.target.value.trim())} onBlur={(e) => filtrar('q', e.target.value.trim())} />
        <select value={filtros.estado} onChange={(e) => filtrar('estado', e.target.value)}>
          <option value="">Todos los estados</option>
          {ESTADOS_DISPOSITIVO.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <select value={filtros.tipo} onChange={(e) => filtrar('tipo', e.target.value)}>
          <option value="">Todos los tipos</option>
          {TIPOS_DISPOSITIVO.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <select value={filtros.centro_id} onChange={(e) => filtrar('centro_id', e.target.value)}>
          <option value="">Todos los centros</option>
          {cat.centros.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>

      <Estado cargando={cargando} error={error} vacio={datos && !datos.length}>
        {datos && (
          <div className="tarjeta sin-padding">
            <table className="tabla">
              <thead><tr><th>Código</th><th>Equipo</th><th>Serie</th><th>Peso</th><th>Estado</th><th>Centro actual</th><th>Lote</th><th>Registro</th><th></th></tr></thead>
              <tbody>
                {datos.map((d) => (
                  <tr key={d.id} className="clic" onClick={() => navigate(`/dispositivos/${d.id}`)}>
                    <td className="nowrap"><b>{d.codigo_trazabilidad}</b></td>
                    <td>{etiqueta(d.tipo)}<div className="muted">{d.marca} {d.modelo}</div></td>
                    <td className="muted">{d.numero_serie || '—'}</td>
                    <td className="nowrap">{kg(d.peso_kg)}</td>
                    <td><Badge v={d.estado} /></td>
                    <td>{d.centro_actual.nombre}</td>
                    <td>{d.lote ? <Link to={`/lotes/${d.lote_id}`} onClick={(e) => e.stopPropagation()}>{d.lote.codigo}</Link> : '—'}</td>
                    <td className="muted nowrap">{fecha(d.fecha_registro)}</td>
                    <td className="acciones" onClick={(e) => e.stopPropagation()}>
                      <button className="btn-link" disabled={d.estado === 'EN_DESTINO'} onClick={() => setForm(d)}>Editar</button>
                      <button className="btn-link peligro" disabled={['EN_LOTE', 'EN_DESTINO'].includes(d.estado)} onClick={() => setBorrar(d)}>Eliminar</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="pie-tabla">{datos.length} dispositivo(s)</div>
          </div>
        )}
      </Estado>

      {form && (
        <Modal titulo={form.id ? `Editar ${form.codigo_trazabilidad}` : 'Registrar dispositivo RAEE'} onClose={() => setForm(null)}>
          {!form.id && <p className="muted">Al registrarlo se genera su código de trazabilidad y el movimiento de ingreso al centro.</p>}
          <FormDispositivo inicial={form} onSubmit={guardar} onCancel={() => setForm(null)} />
        </Modal>
      )}
      {borrar && (
        <Confirmar texto={`¿Eliminar ${borrar.codigo_trazabilidad}? Se borrarán también sus evaluaciones, movimientos y evidencias.`}
          onNo={() => setBorrar(null)}
          onSi={async () => {
            try { await api.del(`/dispositivos/${borrar.id}`); toast('Dispositivo eliminado'); recargar() }
            catch (e) { toast(e.message, 'error') }
            setBorrar(null)
          }} />
      )}
    </>
  )
}
