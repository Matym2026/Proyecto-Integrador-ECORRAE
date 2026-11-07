import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import { etiqueta, fecha, kg } from '../constantes'
import Evidencias from '../components/Evidencias'
import Formulario from '../components/Formulario'
import { FormMovimiento } from '../components/formularios'
import { Badge, Confirmar, Estado, Modal, useCarga, useToast } from '../components/ui'

export default function LoteDetalle() {
  const { id } = useParams()
  const carga = useCarga(() => Promise.all([
    api.get(`/lotes/${id}`),
    api.get('/dispositivos', { lote_id: id }),
    api.get('/movimientos', { lote_id: id }),
  ]), [id])
  const [lote, disps, movs] = carga.datos || []
  const [modal, setModal] = useState(null) 
  const toast = useToast()
  const navigate = useNavigate()
  const hecho = (msg) => { toast(msg); setModal(null); carga.recargar() }
  const accion = async (fn, msg) => { try { await fn(); hecho(msg) } catch (e) { toast(e.message, 'error'); setModal(null) } }

  return (
    <Estado cargando={carga.cargando} error={carga.error}>
      {lote && (
        <>
          <div className="cabecera">
            <div>
              <Link to="/lotes" className="volver">← Lotes</Link>
              <h1>{lote.codigo} <Badge v={lote.estado} /></h1>
            </div>
            <div className="botones">
              {lote.estado === 'ABIERTO' && <>
                <button className="btn" onClick={() => setModal('editar')}>Editar</button>
                <button className="btn" onClick={() => setModal('agregar')}>+ Agregar dispositivos</button>
                <button className="btn btn-primario" disabled={!disps.length} onClick={() => setModal('cerrar')}>Cerrar lote</button>
                <button className="btn btn-peligro" onClick={() => setModal('eliminar')}>Eliminar</button>
              </>}
              {lote.estado === 'CERRADO' && <>
                <button className="btn" onClick={() => setModal('TRASLADO')}>Trasladar lote</button>
                <button className="btn btn-primario" onClick={() => setModal('ENTREGA_DESTINO')}>Entregar a destino final</button>
              </>}
            </div>
          </div>

          <div className="kpis">
            <div className="kpi"><span>{lote.estado === 'ENTREGADO' ? 'Último centro' : 'Centro actual'}</span><strong className="kpi-txt">{lote.centro.nombre}</strong></div>
            <div className="kpi"><span>Dispositivos</span><strong>{lote.total_dispositivos}</strong></div>
            <div className="kpi"><span>Peso total</span><strong>{kg(lote.peso_total_kg)}</strong></div>
            <div className="kpi"><span>Destino final</span><strong className="kpi-txt">{lote.destino?.nombre || 'Pendiente'}</strong></div>
          </div>
          {lote.descripcion && <p className="muted">{lote.descripcion}</p>}

          <div className="tarjeta">
            <h2>Dispositivos del lote</h2>
            {disps.length ? (
              <table className="tabla">
                <thead><tr><th>Código</th><th>Equipo</th><th>Peso</th><th>Estado</th><th></th></tr></thead>
                <tbody>
                  {disps.map((d) => (
                    <tr key={d.id}>
                      <td><Link to={`/dispositivos/${d.id}`}>{d.codigo_trazabilidad}</Link></td>
                      <td>{etiqueta(d.tipo)} · {d.marca} {d.modelo}</td><td>{kg(d.peso_kg)}</td><td><Badge v={d.estado} /></td>
                      <td className="acciones">{lote.estado === 'ABIERTO' &&
                        <button className="btn-link peligro" onClick={() => accion(() => api.del(`/lotes/${id}/dispositivos/${d.id}`), 'Dispositivo retirado del lote')}>Quitar</button>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <p className="muted">El lote está vacío. Agregue dispositivos evaluados del mismo centro.</p>}
          </div>

          <div className="dos-col">
            <div className="tarjeta">
              <h2>Movimientos del lote</h2>
              {movs.length ? (
                <ul className="lista-mov">
                  {movs.map((m) => (
                    <li key={m.id}><Badge v={m.tipo} /> {m.centro_origen?.nombre} → {m.destino?.nombre || m.centro_destino?.nombre}
                      <div className="muted">{fecha(m.fecha)} {m.guia_remision && `· guía ${m.guia_remision}`} {m.responsable && `· ${m.responsable.nombre}`}</div></li>
                  ))}
                </ul>
              ) : <p className="muted">Sin movimientos todavía.</p>}
            </div>
            <div className="tarjeta">
              <h2>Evidencias del lote</h2>
              <p className="muted">Actas de entrega, guías de remisión, certificados del gestor.</p>
              <Evidencias loteId={lote.id} />
            </div>
          </div>

          {modal === 'agregar' && <AgregarDispositivos lote={lote} onClose={() => setModal(null)} onListo={hecho} />}
          {modal === 'editar' && (
            <Modal titulo={`Editar ${lote.codigo}`} onClose={() => setModal(null)}>
              <Formulario campos={[{ name: 'descripcion', label: 'Descripción', type: 'textarea', maxLength: 255 }]} inicial={lote}
                onCancel={() => setModal(null)} onSubmit={async (d) => { await api.put(`/lotes/${id}`, d); hecho('Lote actualizado') }} />
            </Modal>
          )}
          {modal === 'cerrar' && <Confirmar peligro={false} texto="Al cerrar el lote ya no podrá agregar ni quitar dispositivos. ¿Continuar?"
            onNo={() => setModal(null)} onSi={() => accion(() => api.post(`/lotes/${id}/cerrar`), 'Lote cerrado')} />}
          {modal === 'eliminar' && <Confirmar texto="¿Eliminar el lote? Sus dispositivos volverán a estado EVALUADO."
            onNo={() => setModal(null)}
            onSi={async () => { try { await api.del(`/lotes/${id}`); toast('Lote eliminado'); navigate('/lotes') } catch (e) { toast(e.message, 'error'); setModal(null) } }} />}
          {(modal === 'TRASLADO' || modal === 'ENTREGA_DESTINO') && (
            <Modal titulo={modal === 'TRASLADO' ? `Trasladar ${lote.codigo}` : `Entregar ${lote.codigo} a destino final`} onClose={() => setModal(null)}>
              <FormMovimiento tipo={modal} loteId={lote.id} centroActualId={lote.centro_id} onCancel={() => setModal(null)}
                onSubmit={async (x) => { await api.post('/movimientos', x); hecho(modal === 'TRASLADO' ? 'Lote trasladado' : 'Lote entregado a destino final') }} />
            </Modal>
          )}
        </>
      )}
    </Estado>
  )
}

function AgregarDispositivos({ lote, onClose, onListo }) {
  const { datos, cargando } = useCarga(() => api.get('/dispositivos', { estado: 'EVALUADO', centro_id: lote.centro_id, sin_lote: true }))
  const [sel, setSel] = useState([])
  const [error, setError] = useState(null)
  const toggle = (id) => setSel((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]))
  return (
    <Modal titulo={`Agregar dispositivos a ${lote.codigo}`} onClose={onClose}>
      <p className="muted">Dispositivos EVALUADOS, sin lote, ubicados en {lote.centro.nombre}.</p>
      {error && <div className="alerta alerta-error">{error}</div>}
      {cargando ? <div className="cargando">Cargando…</div> : datos.length ? (
        <ul className="lista-check">
          {datos.map((d) => (
            <li key={d.id}><label className="check">
              <input type="checkbox" checked={sel.includes(d.id)} onChange={() => toggle(d.id)} />
              <b>{d.codigo_trazabilidad}</b> {etiqueta(d.tipo)} · {d.marca} {d.modelo} · {kg(d.peso_kg)}
            </label></li>
          ))}
        </ul>
      ) : <p className="vacio">No hay dispositivos disponibles. Evalúe primero los equipos de este centro.</p>}
      <div className="acciones-form">
        <button className="btn" onClick={onClose}>Cancelar</button>
        <button className="btn btn-primario" disabled={!sel.length} onClick={async () => {
          try { await api.post(`/lotes/${lote.id}/dispositivos`, { dispositivo_ids: sel }); onListo(`${sel.length} dispositivo(s) agregados`) }
          catch (e) { setError(e.message) }
        }}>Agregar {sel.length || ''}</button>
      </div>
    </Modal>
  )
}
