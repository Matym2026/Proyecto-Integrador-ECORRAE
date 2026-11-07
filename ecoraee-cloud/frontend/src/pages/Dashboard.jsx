import { Link } from 'react-router-dom'
import { api } from '../api'
import { etiqueta, fecha, kg } from '../constantes'
import { Badge, Estado, useCarga } from '../components/ui'

const FLUJO = [
  ['REGISTRADO', 'Registro e ingreso', 'Se recibe el equipo en un centro de acopio'],
  ['EVALUADO', 'Evaluación técnica', 'Diagnóstico y tratamiento recomendado'],
  ['EN_LOTE', 'Consolidación en lote', 'Agrupación, traslado entre centros'],
  ['EN_DESTINO', 'Destino final', 'Entrega a gestor autorizado'],
]

export default function Dashboard() {
  const { datos: d, error, cargando } = useCarga(() => api.get('/dashboard'))
  return (
    <>
      <div className="cabecera"><h1>Panel de trazabilidad</h1></div>
      <Estado cargando={cargando} error={error}>
        {d && (
          <>
            <div className="kpis">
              <div className="kpi"><span>Dispositivos registrados</span><strong>{d.total_dispositivos}</strong></div>
              <div className="kpi"><span>Peso total gestionado</span><strong>{kg(d.peso_total_kg)}</strong></div>
              <div className="kpi"><span>Peso entregado a destino</span><strong>{kg(d.peso_entregado_kg)}</strong></div>
              <div className="kpi"><span>Lotes abiertos / cerrados / entregados</span>
                <strong>{d.lotes_por_estado.ABIERTO} / {d.lotes_por_estado.CERRADO} / {d.lotes_por_estado.ENTREGADO}</strong></div>
            </div>

            <div className="tarjeta">
              <h2>Ciclo de trazabilidad</h2>
              <div className="flujo">
                {FLUJO.map(([estado, titulo, desc], i) => (
                  <Link key={estado} to={`/dispositivos?estado=${estado}`} className="flujo-paso">
                    <div className="flujo-num">{i + 1}</div>
                    <div><strong>{titulo}</strong><p>{desc}</p></div>
                    <div className="flujo-cant">{d.por_estado[estado]}</div>
                  </Link>
                ))}
              </div>
            </div>

            <div className="dos-col">
              <div className="tarjeta">
                <h2>Equipos por tipo</h2>
                <div className="barras">
                  {d.por_tipo.map((t) => (
                    <div key={t.tipo} className="barra-fila">
                      <span>{etiqueta(t.tipo)}</span>
                      <div className="barra"><div style={{ width: `${(t.cantidad / d.total_dispositivos) * 100}%` }} /></div>
                      <b>{t.cantidad}</b>
                    </div>
                  ))}
                </div>
              </div>
              <div className="tarjeta">
                <h2>Últimos movimientos</h2>
                <table className="tabla compacta">
                  <tbody>
                    {d.ultimos_movimientos.map((m) => (
                      <tr key={m.id}>
                        <td><Badge v={m.tipo} /></td>
                        <td>{m.lote ? <Link to={`/lotes/${m.lote_id}`}>{m.lote.codigo}</Link>
                          : m.dispositivo && <Link to={`/dispositivos/${m.dispositivo_id}`}>{m.dispositivo.codigo_trazabilidad}</Link>}</td>
                        <td className="muted">{m.destino?.nombre || m.centro_destino?.nombre}</td>
                        <td className="muted nowrap">{fecha(m.fecha)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </Estado>
    </>
  )
}
