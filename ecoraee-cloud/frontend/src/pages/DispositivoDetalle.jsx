import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { etiqueta, fecha, kg } from '../constantes'
import Evidencias from '../components/Evidencias'
import { FormDispositivo, FormEvaluacion, FormMovimiento } from '../components/formularios'
import { Badge, Confirmar, Estado, Modal, Si, useCarga, useToast } from '../components/ui'

const ICONOS = { REGISTRO: '📝', INGRESO: '📥', EVALUACION: '🔍', TRASLADO: '🚚', ENTREGA_DESTINO: '✅', EVIDENCIA: '📎' }

export default function DispositivoDetalle() {
  const { id } = useParams()
  const { datos, error, cargando, recargar } = useCarga(() => api.get(`/dispositivos/${id}/trazabilidad`), [id])
  const [modal, setModal] = useState(null) // editar | evaluar | TRASLADO | ENTREGA_DESTINO | {evaluacion}
  const [borrarEval, setBorrarEval] = useState(null)
  const toast = useToast()
  const d = datos?.dispositivo

  const hecho = (msg) => { toast(msg); setModal(null); recargar() }
  const evaluable = d && ['REGISTRADO', 'EVALUADO'].includes(d.estado)

  return (
    <Estado cargando={cargando} error={error}>
      {d && (
        <>
          <div className="cabecera">
            <div>
              <Link to="/dispositivos" className="volver">← Dispositivos</Link>
              <h1>{d.codigo_trazabilidad} <Badge v={d.estado} /></h1>
            </div>
            <div className="botones">
              <button className="btn" disabled={d.estado === 'EN_DESTINO'} onClick={() => setModal('editar')}>Editar</button>
              <button className="btn" disabled={!evaluable} onClick={() => setModal('evaluar')}>Evaluar</button>
              <button className="btn" disabled={!!d.lote_id || d.estado === 'EN_DESTINO'} onClick={() => setModal('TRASLADO')}
                title={d.lote_id ? 'Está en un lote: mueva el lote' : ''}>Trasladar</button>
              <button className="btn btn-primario" disabled={d.estado !== 'EVALUADO'} onClick={() => setModal('ENTREGA_DESTINO')}
                title="Entrega individual (sin lote)">Entregar a destino</button>
            </div>
          </div>

          <div className="dos-col">
            <div className="tarjeta">
              <h2>Datos del equipo</h2>
              <dl className="ficha">
                <dt>Tipo</dt><dd>{etiqueta(d.tipo)}</dd>
                <dt>Marca / modelo</dt><dd>{d.marca} {d.modelo}</dd>
                <dt>N.º de serie</dt><dd>{d.numero_serie || '—'}</dd>
                <dt>Peso</dt><dd>{kg(d.peso_kg)}</dd>
                <dt>Centro actual</dt><dd>{d.centro_actual.nombre}</dd>
                <dt>Lote</dt><dd>{d.lote ? <Link to={`/lotes/${d.lote_id}`}>{d.lote.codigo}</Link> : '—'}</dd>
                <dt>Origen</dt><dd>{d.origen || '—'}</dd>
                <dt>Observaciones</dt><dd>{d.observaciones || '—'}</dd>
              </dl>
            </div>
            <div className="tarjeta">
              <h2>Línea de tiempo de trazabilidad</h2>
              <ol className="timeline">
                {datos.linea_tiempo.map((e, i) => (
                  <li key={i}>
                    <span className="tl-icono">{ICONOS[e.tipo]}</span>
                    <div><strong>{e.titulo}</strong><div className="muted">{fecha(e.fecha)}</div>{e.detalle && <div>{e.detalle}</div>}</div>
                  </li>
                ))}
              </ol>
            </div>
          </div>

          <div className="tarjeta">
            <h2>Evaluaciones técnicas</h2>
            {datos.evaluaciones.length ? (
              <table className="tabla">
                <thead><tr><th>Fecha</th><th>Evaluador</th><th>Estado</th><th>Funcional</th><th>Datos borrados</th><th>Peligrosos</th><th>Recomendación</th><th>Observaciones</th><th></th></tr></thead>
                <tbody>
                  {datos.evaluaciones.map((e) => (
                    <tr key={e.id}>
                      <td className="nowrap">{fecha(e.fecha)}</td><td>{e.evaluador.nombre}</td><td><Badge v={e.estado_fisico} /></td>
                      <td><Si v={e.funcional} /></td><td><Si v={e.datos_borrados} /></td><td><Si v={e.contiene_peligrosos} /></td>
                      <td><Badge v={e.recomendacion} /></td><td className="muted">{e.observaciones}</td>
                      <td className="acciones">
                        <button className="btn-link" disabled={!evaluable} onClick={() => setModal({ evaluacion: e })}>Editar</button>
                        <button className="btn-link peligro" disabled={!evaluable} onClick={() => setBorrarEval(e)}>Eliminar</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <p className="muted">Aún no ha sido evaluado.</p>}
          </div>

          <div className="tarjeta">
            <h2>Evidencias del dispositivo</h2>
            <Evidencias dispositivoId={d.id} onCambio={recargar} />
          </div>

          {modal === 'editar' && (
            <Modal titulo={`Editar ${d.codigo_trazabilidad}`} onClose={() => setModal(null)}>
              <FormDispositivo inicial={d} onCancel={() => setModal(null)}
                onSubmit={async (x) => { await api.put(`/dispositivos/${d.id}`, x); hecho('Dispositivo actualizado') }} />
            </Modal>
          )}
          {(modal === 'evaluar' || modal?.evaluacion) && (
            <Modal titulo={modal.evaluacion ? 'Editar evaluación' : `Evaluar ${d.codigo_trazabilidad}`} onClose={() => setModal(null)}>
              <FormEvaluacion dispositivoId={d.id} inicial={modal.evaluacion} onCancel={() => setModal(null)}
                onSubmit={async (x) => {
                  if (modal.evaluacion) await api.put(`/evaluaciones/${modal.evaluacion.id}`, x)
                  else await api.post('/evaluaciones', x)
                  hecho('Evaluación guardada')
                }} />
            </Modal>
          )}
          {(modal === 'TRASLADO' || modal === 'ENTREGA_DESTINO') && (
            <Modal titulo={modal === 'TRASLADO' ? 'Trasladar a otro centro' : 'Entregar a destino final'} onClose={() => setModal(null)}>
              <FormMovimiento tipo={modal} dispositivoId={d.id} centroActualId={d.centro_actual_id} onCancel={() => setModal(null)}
                onSubmit={async (x) => { await api.post('/movimientos', x); hecho('Movimiento registrado') }} />
            </Modal>
          )}
          {borrarEval && (
            <Confirmar texto="¿Eliminar esta evaluación?" onNo={() => setBorrarEval(null)}
              onSi={async () => {
                try { await api.del(`/evaluaciones/${borrarEval.id}`); toast('Evaluación eliminada'); recargar() }
                catch (e) { toast(e.message, 'error') }
                setBorrarEval(null)
              }} />
          )}
        </>
      )}
    </Estado>
  )
}
