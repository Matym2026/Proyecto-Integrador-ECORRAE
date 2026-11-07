import { useEffect, useState } from 'react'
import { api } from '../api'
import { ESTADOS_FISICOS, RECOMENDACIONES, TIPOS_DISPOSITIVO, etiqueta } from '../constantes'
import Formulario from './Formulario'


export function useCatalogos() {
  const [cat, setCat] = useState({ centros: [], destinos: [], usuarios: [], evaluadores: [] })
  useEffect(() => {
    Promise.all([
      api.get('/centros', { solo_activos: true }),
      api.get('/destinos', { solo_activos: true }),
      api.get('/usuarios', { solo_activos: true }),
    ]).then(([c, d, u]) => setCat({
      centros: c.map((x) => ({ value: x.id, label: `${x.nombre} (${x.ciudad})` })),
      destinos: d.map((x) => ({ value: x.id, label: `${x.nombre} · ${etiqueta(x.tipo)}`, tipo: x.tipo })),
      usuarios: u.map((x) => ({ value: x.id, label: `${x.nombre} · ${etiqueta(x.rol)}` })),
      evaluadores: u.filter((x) => ['EVALUADOR', 'ADMIN'].includes(x.rol)).map((x) => ({ value: x.id, label: x.nombre })),
    })).catch(() => {})
  }, [])
  return cat
}

export function FormDispositivo({ inicial, onSubmit, onCancel }) {
  const cat = useCatalogos()
  const edicion = !!inicial?.id
  const campos = [
    { name: 'tipo', label: 'Tipo de equipo', type: 'select', required: true, options: TIPOS_DISPOSITIVO },
    { name: 'marca', label: 'Marca', required: true, minLength: 2, maxLength: 60 },
    { name: 'modelo', label: 'Modelo', maxLength: 80 },
    { name: 'numero_serie', label: 'Número de serie', maxLength: 80, ayuda: 'Único por equipo' },
    { name: 'peso_kg', label: 'Peso (kg)', type: 'number', step: '0.01', required: true, minExclusive: 0, max: 2000 },
    ...(edicion ? [] : [
      { name: 'centro_actual_id', label: 'Centro de acopio', type: 'select', required: true, options: cat.centros, numerico: true },
      { name: 'registrado_por', label: 'Registrado por', type: 'select', options: cat.usuarios, numerico: true },
    ]),
    { name: 'origen', label: 'Origen / generador', maxLength: 150, ancho: 'completo', placeholder: 'Empresa, área o campaña de donde proviene' },
    { name: 'observaciones', label: 'Observaciones', type: 'textarea' },
  ]
  if (!edicion && !cat.centros.length) return <div className="cargando">Cargando catálogos…</div>
  return <Formulario campos={campos} inicial={inicial} onSubmit={onSubmit} onCancel={onCancel}
    textoBoton={edicion ? 'Guardar cambios' : 'Registrar dispositivo'} />
}

export function FormEvaluacion({ dispositivoId, dispositivos, inicial, onSubmit, onCancel }) {
  const cat = useCatalogos()
  const campos = [
    ...(dispositivoId ? [] : [{ name: 'dispositivo_id', label: 'Dispositivo', type: 'select', required: true, numerico: true, options: dispositivos || [] }]),
    { name: 'evaluador_id', label: 'Evaluador', type: 'select', required: true, numerico: true, options: cat.evaluadores },
    { name: 'estado_fisico', label: 'Estado físico', type: 'select', required: true, options: ESTADOS_FISICOS },
    { name: 'funcional', label: 'El equipo es funcional', type: 'checkbox' },
    { name: 'datos_borrados', label: 'Datos borrados de forma segura', type: 'checkbox' },
    { name: 'contiene_peligrosos', label: 'Contiene componentes peligrosos (baterías, mercurio, tóner…)', type: 'checkbox', ancho: 'completo' },
    { name: 'recomendacion', label: 'Tratamiento recomendado', type: 'select', required: true, options: RECOMENDACIONES, ancho: 'completo' },
    { name: 'observaciones', label: 'Observaciones', type: 'textarea' },
  ]
  const validar = (v) => ({
    recomendacion: v.recomendacion === 'REUTILIZACION' && (!v.funcional || !v.datos_borrados)
      ? 'Para reutilizar, el equipo debe ser funcional y con datos borrados'
      : v.recomendacion === 'REUTILIZACION' && v.contiene_peligrosos
        ? 'Un equipo con componentes peligrosos no puede reutilizarse' : undefined,
  })
  return (
    <Formulario campos={campos} inicial={inicial} validar={validar} onCancel={onCancel}
      onSubmit={(d) => onSubmit({ ...d, dispositivo_id: dispositivoId || d.dispositivo_id })}
      textoBoton={inicial?.id ? 'Guardar cambios' : 'Registrar evaluación'} />
  )
}

/** Traslado entre centros o entrega a destino final, de un dispositivo o de un lote. */
export function FormMovimiento({ tipo, dispositivoId, loteId, centroActualId, onSubmit, onCancel }) {
  const cat = useCatalogos()
  const campos = [
    tipo === 'TRASLADO'
      ? { name: 'centro_destino_id', label: 'Centro de destino', type: 'select', required: true, numerico: true,
          options: cat.centros.filter((c) => c.value !== centroActualId) }
      : { name: 'destino_id', label: 'Destino final (gestor autorizado)', type: 'select', required: true, numerico: true, options: cat.destinos },
    { name: 'responsable_id', label: 'Responsable', type: 'select', numerico: true, options: cat.usuarios },
    { name: 'guia_remision', label: 'Guía de remisión', maxLength: 40, placeholder: 'GR-001-0000000' },
    { name: 'observaciones', label: 'Observaciones', type: 'textarea' },
  ]
  return (
    <Formulario campos={campos} onCancel={onCancel}
      textoBoton={tipo === 'TRASLADO' ? 'Registrar traslado' : 'Registrar entrega'}
      onSubmit={(d) => onSubmit({ ...d, tipo, dispositivo_id: dispositivoId || null, lote_id: loteId || null })} />
  )
}
