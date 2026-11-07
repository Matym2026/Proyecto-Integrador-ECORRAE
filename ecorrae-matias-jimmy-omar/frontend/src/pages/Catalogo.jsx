import { useState } from 'react'
import { api } from '../api'
import { ROLES, TIPOS_CENTRO, TIPOS_DESTINO } from '../constantes'
import Formulario from '../components/Formulario'
import { Badge, Confirmar, Estado, Modal, Si, useCarga, useToast } from '../components/ui'


export const CATALOGOS = {
  centros: {
    titulo: 'Centros de acopio y tratamiento', singular: 'centro',
    columnas: [['nombre', 'Nombre'], ['tipo', 'Tipo', 'badge'], ['ciudad', 'Ciudad'], ['direccion', 'Dirección'], ['responsable', 'Responsable'], ['telefono', 'Teléfono'], ['activo', 'Activo', 'bool']],
    campos: [
      { name: 'nombre', label: 'Nombre', required: true, minLength: 3, maxLength: 120, ancho: 'completo' },
      { name: 'tipo', label: 'Tipo', type: 'select', required: true, options: TIPOS_CENTRO },
      { name: 'ciudad', label: 'Ciudad', required: true, minLength: 2, maxLength: 80 },
      { name: 'direccion', label: 'Dirección', maxLength: 200, ancho: 'completo' },
      { name: 'responsable', label: 'Responsable', maxLength: 120 },
      { name: 'telefono', label: 'Teléfono', pattern: '^\\+?[0-9]{7,15}$', patternMsg: 'Solo dígitos (7 a 15)' },
      { name: 'activo', label: 'Activo', type: 'checkbox', defecto: true },
    ],
  },
  destinos: {
    titulo: 'Destinos finales (gestores autorizados)', singular: 'destino',
    columnas: [['nombre', 'Nombre'], ['tipo', 'Tipo', 'badge'], ['ruc', 'RUC'], ['licencia_ambiental', 'Licencia ambiental'], ['ciudad', 'Ciudad'], ['contacto', 'Contacto'], ['activo', 'Activo', 'bool']],
    campos: [
      { name: 'nombre', label: 'Nombre', required: true, minLength: 3, maxLength: 120, ancho: 'completo' },
      { name: 'tipo', label: 'Tipo de tratamiento', type: 'select', required: true, options: TIPOS_DESTINO },
      { name: 'ciudad', label: 'Ciudad', required: true, minLength: 2, maxLength: 80 },
      { name: 'ruc', label: 'RUC', pattern: '^[0-9]{13}$', patternMsg: 'El RUC tiene 13 dígitos' },
      { name: 'licencia_ambiental', label: 'Licencia ambiental', maxLength: 60 },
      { name: 'contacto', label: 'Contacto', maxLength: 120, ancho: 'completo' },
      { name: 'activo', label: 'Activo', type: 'checkbox', defecto: true },
    ],
  },
  usuarios: {
    titulo: 'Usuarios del sistema', singular: 'usuario',
    columnas: [['nombre', 'Nombre'], ['email', 'Correo'], ['rol', 'Rol', 'badge'], ['activo', 'Activo', 'bool']],
    campos: [
      { name: 'nombre', label: 'Nombre completo', required: true, minLength: 3, maxLength: 120, ancho: 'completo' },
      { name: 'email', label: 'Correo', type: 'email', required: true, maxLength: 150 },
      { name: 'rol', label: 'Rol', type: 'select', required: true, options: ROLES },
      { name: 'activo', label: 'Activo', type: 'checkbox', defecto: true },
    ],
  },
}

export default function Catalogo({ recurso }) {
  const cfg = CATALOGOS[recurso]
  const [q, setQ] = useState('')
  const { datos, error, cargando, recargar } = useCarga(() => api.get(`/${recurso}`, { q }), [recurso, q])
  const [form, setForm] = useState(null)
  const [borrar, setBorrar] = useState(null)
  const toast = useToast()

  return (
    <>
      <div className="cabecera">
        <h1>{cfg.titulo}</h1>
        <button className="btn btn-primario" onClick={() => setForm({})}>+ Nuevo {cfg.singular}</button>
      </div>
      <div className="filtros">
        <input type="search" placeholder="Buscar…" onKeyDown={(e) => e.key === 'Enter' && setQ(e.target.value.trim())} onBlur={(e) => setQ(e.target.value.trim())} />
      </div>
      <Estado cargando={cargando} error={error} vacio={datos && !datos.length}>
        {datos && (
          <div className="tarjeta sin-padding">
            <table className="tabla">
              <thead><tr>{cfg.columnas.map(([k, t]) => <th key={k}>{t}</th>)}<th></th></tr></thead>
              <tbody>
                {datos.map((fila) => (
                  <tr key={fila.id}>
                    {cfg.columnas.map(([k, , tipo]) => (
                      <td key={k}>{tipo === 'badge' ? <Badge v={fila[k]} /> : tipo === 'bool' ? <Si v={fila[k]} /> : fila[k] || '—'}</td>
                    ))}
                    <td className="acciones">
                      <button className="btn-link" onClick={() => setForm(fila)}>Editar</button>
                      <button className="btn-link peligro" onClick={() => setBorrar(fila)}>Eliminar</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Estado>
      {form && (
        <Modal titulo={form.id ? `Editar ${cfg.singular}` : `Nuevo ${cfg.singular}`} onClose={() => setForm(null)}>
          <Formulario campos={cfg.campos} inicial={form} onCancel={() => setForm(null)}
            onSubmit={async (d) => {
              if (form.id) await api.put(`/${recurso}/${form.id}`, d)
              else await api.post(`/${recurso}`, d)
              toast(`${cfg.singular[0].toUpperCase() + cfg.singular.slice(1)} guardado`); setForm(null); recargar()
            }} />
        </Modal>
      )}
      {borrar && (
        <Confirmar texto={`¿Eliminar "${borrar.nombre}"? Si tiene registros relacionados la base de datos lo impedirá; en ese caso puede marcarlo como inactivo.`}
          onNo={() => setBorrar(null)}
          onSi={async () => {
            try { await api.del(`/${recurso}/${borrar.id}`); toast('Registro eliminado'); recargar() }
            catch (e) { toast(e.message, 'error') }
            setBorrar(null)
          }} />
      )}
    </>
  )
}
