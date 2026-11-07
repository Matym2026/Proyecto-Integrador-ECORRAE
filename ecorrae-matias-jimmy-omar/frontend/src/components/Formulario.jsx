import { useState } from 'react'


export function validarCampos(campos, v) {
  const err = {}
  for (const c of campos) {
    const val = v[c.name]
    const vacio = val === '' || val == null
    if (c.type === 'checkbox') continue
    if (c.required && vacio) { err[c.name] = 'Campo obligatorio'; continue }
    if (vacio) continue
    if (c.type === 'number') {
      const n = Number(val)
      if (Number.isNaN(n)) err[c.name] = 'Debe ser un número'
      else if (c.min != null && n < c.min) err[c.name] = `Mínimo ${c.min}`
      else if (c.minExclusive != null && n <= c.minExclusive) err[c.name] = `Debe ser mayor que ${c.minExclusive}`
      else if (c.max != null && n > c.max) err[c.name] = `Máximo ${c.max}`
      continue
    }
    const s = String(val).trim()
    if (c.minLength && s.length < c.minLength) err[c.name] = `Mínimo ${c.minLength} caracteres`
    else if (c.maxLength && s.length > c.maxLength) err[c.name] = `Máximo ${c.maxLength} caracteres`
    else if (c.type === 'email' && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(s)) err[c.name] = 'Correo inválido'
    else if (c.pattern && !new RegExp(c.pattern).test(s)) err[c.name] = c.patternMsg || 'Formato inválido'
  }
  return err
}

export default function Formulario({ campos, inicial = {}, validar, onSubmit, onCancel, textoBoton = 'Guardar' }) {
  const [v, setV] = useState(() => {
    const base = {}
    for (const c of campos) base[c.name] = inicial[c.name] ?? (c.type === 'checkbox' ? (c.defecto ?? false) : '')
    return base
  })
  const [err, setErr] = useState({})
  const [general, setGeneral] = useState(null)
  const [enviando, setEnviando] = useState(false)

  const cambiar = (c, valor) => {
    setV((x) => ({ ...x, [c.name]: valor }))
    if (err[c.name]) setErr((x) => ({ ...x, [c.name]: undefined }))
  }

  const enviar = async (e) => {
    e.preventDefault()
    const errores = { ...validarCampos(campos, v), ...(validar ? validar(v) : {}) }
    Object.keys(errores).forEach((k) => errores[k] === undefined && delete errores[k])
    setErr(errores)
    setGeneral(null)
    if (Object.keys(errores).length) return
   
    const datos = {}
    for (const c of campos) {
      let val = v[c.name]
      if (typeof val === 'string') val = val.trim()
      if (val === '') val = null
      else if (c.type === 'number' || c.numerico) val = val == null ? null : Number(val)
      datos[c.name] = val
    }
    setEnviando(true)
    try {
      await onSubmit(datos)
    } catch (ex) {
      const porCampo = {}
      ;(ex.errores || []).forEach((x) => { if (campos.some((c) => c.name === x.campo)) porCampo[x.campo] = x.mensaje })
      setErr(porCampo)
      setGeneral(ex.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={enviar} noValidate className="form">
      {general && <div className="alerta alerta-error">{general}</div>}
      <div className="form-grid">
        {campos.filter((c) => !c.oculto?.(v)).map((c) => (
          <div key={c.name} className={`campo ${c.ancho === 'completo' || c.type === 'textarea' ? 'campo-completo' : ''} ${c.type === 'checkbox' ? 'campo-check' : ''}`}>
            {c.type === 'checkbox' ? (
              <label className="check">
                <input type="checkbox" checked={!!v[c.name]} onChange={(e) => cambiar(c, e.target.checked)} />
                {c.label}
              </label>
            ) : (
              <>
                <label htmlFor={c.name}>{c.label}{c.required && <span className="req"> *</span>}</label>
                {c.type === 'select' ? (
                  <select id={c.name} value={v[c.name] ?? ''} onChange={(e) => cambiar(c, e.target.value)} className={err[c.name] ? 'invalido' : ''}>
                    <option value="">— Seleccione —</option>
                    {c.options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                ) : c.type === 'textarea' ? (
                  <textarea id={c.name} rows={3} value={v[c.name] ?? ''} onChange={(e) => cambiar(c, e.target.value)} className={err[c.name] ? 'invalido' : ''} />
                ) : (
                  <input id={c.name} type={c.type === 'email' ? 'email' : c.type === 'number' ? 'number' : 'text'} step={c.step}
                    value={v[c.name] ?? ''} placeholder={c.placeholder} onChange={(e) => cambiar(c, e.target.value)} className={err[c.name] ? 'invalido' : ''} />
                )}
              </>
            )}
            {err[c.name] ? <small className="error-campo">{err[c.name]}</small> : c.ayuda && <small className="ayuda">{c.ayuda}</small>}
          </div>
        ))}
      </div>
      <div className="acciones-form">
        {onCancel && <button type="button" className="btn" onClick={onCancel}>Cancelar</button>}
        <button type="submit" className="btn btn-primario" disabled={enviando}>{enviando ? 'Guardando…' : textoBoton}</button>
      </div>
    </form>
  )
}
