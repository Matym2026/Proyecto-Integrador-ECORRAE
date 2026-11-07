import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { RECOMENDACIONES, fecha } from '../constantes'
import { FormEvaluacion } from '../components/formularios'
import { Badge, Confirmar, Estado, Modal, Si, useCarga, useToast } from '../components/ui'

export default function Evaluaciones() {
  const [rec, setRec] = useState('')
  const { datos, error, cargando, recargar } = useCarga(() => api.get('/evaluaciones', { recomendacion: rec }), [rec])
  const [form, setForm] = useState(null)
  const [borrar, setBorrar] = useState(null)
  const [pendientes, setPendientes] = useState([])
  const toast = useToast()

  const abrirNueva = async () => {
    const lista = await api.get('/dispositivos', { estado: 'REGISTRADO' })
    setPendientes(lista.map((d) => ({ value: d.id, label: `${d.codigo_trazabilidad} · ${d.marca} ${d.modelo || ''}` })))
    setForm({})
  }

  return (
    <>
      <div className="cabecera">
        <h1>Evaluaciones técnicas</h1>
        <button className="btn btn-primario" onClick={abrirNueva}>+ Nueva evaluación</button>
      </div>
      <div className="filtros">
        <select value={rec} onChange={(e) => setRec(e.target.value)}>
          <option value="">Todas las recomendaciones</option>
          {RECOMENDACIONES.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>
      <Estado cargando={cargando} error={error} vacio={datos && !datos.length}>
        {datos && (
          <div className="tarjeta sin-padding">
            <table className="tabla">
              <thead><tr><th>Fecha</th><th>Dispositivo</th><th>Evaluador</th><th>Estado</th><th>Funcional</th><th>Datos borrados</th><th>Peligrosos</th><th>Recomendación</th><th></th></tr></thead>
              <tbody>
                {datos.map((e) => (
                  <tr key={e.id}>
                    <td className="nowrap">{fecha(e.fecha)}</td>
                    <td><Link to={`/dispositivos/${e.dispositivo_id}`}>{e.dispositivo.codigo_trazabilidad}</Link><div className="muted">{e.dispositivo.marca}</div></td>
                    <td>{e.evaluador.nombre}</td><td><Badge v={e.estado_fisico} /></td>
                    <td><Si v={e.funcional} /></td><td><Si v={e.datos_borrados} /></td><td><Si v={e.contiene_peligrosos} /></td>
                    <td><Badge v={e.recomendacion} /></td>
                    <td className="acciones">
                      <button className="btn-link" onClick={() => setForm(e)}>Editar</button>
                      <button className="btn-link peligro" onClick={() => setBorrar(e)}>Eliminar</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Estado>
      {form && (
        <Modal titulo={form.id ? `Editar evaluación de ${form.dispositivo.codigo_trazabilidad}` : 'Nueva evaluación'} onClose={() => setForm(null)}>
          {!form.id && !pendientes.length ? <p className="vacio">No hay dispositivos pendientes de evaluación.</p> : (
            <FormEvaluacion dispositivoId={form.dispositivo_id} dispositivos={pendientes} inicial={form} onCancel={() => setForm(null)}
              onSubmit={async (d) => {
                if (form.id) await api.put(`/evaluaciones/${form.id}`, d)
                else await api.post('/evaluaciones', d)
                toast('Evaluación guardada'); setForm(null); recargar()
              }} />
          )}
        </Modal>
      )}
      {borrar && (
        <Confirmar texto={`¿Eliminar la evaluación de ${borrar.dispositivo.codigo_trazabilidad}?`} onNo={() => setBorrar(null)}
          onSi={async () => {
            try { await api.del(`/evaluaciones/${borrar.id}`); toast('Evaluación eliminada'); recargar() }
            catch (e) { toast(e.message, 'error') }
            setBorrar(null)
          }} />
      )}
    </>
  )
}
