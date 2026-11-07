// Cliente HTTP del backend. Todas las rutas van a /api (proxy de Vite -> FastAPI).
const BASE = import.meta.env.VITE_API_URL || '/api'

export class ApiError extends Error {
  constructor(mensaje, status, errores = []) {
    super(mensaje)
    this.status = status
    this.errores = errores // [{campo, mensaje}] cuando el backend rechaza la validación
  }
}

async function request(metodo, ruta, cuerpo, esFormData = false) {
  let resp
  try {
    resp = await fetch(BASE + ruta, {
      method: metodo,
      headers: cuerpo && !esFormData ? { 'Content-Type': 'application/json' } : undefined,
      body: cuerpo ? (esFormData ? cuerpo : JSON.stringify(cuerpo)) : undefined,
    })
  } catch {
    throw new ApiError('No se pudo conectar con el backend. ¿Está corriendo en el puerto 8000?', 0)
  }
  if (resp.status === 204) return null
  const datos = await resp.json().catch(() => ({}))
  if (!resp.ok) throw new ApiError(datos.detail || `Error ${resp.status}`, resp.status, datos.errores || [])
  return datos
}

const qs = (p) => {
  const limpio = Object.fromEntries(Object.entries(p || {}).filter(([, v]) => v !== '' && v != null && v !== false))
  const s = new URLSearchParams(limpio).toString()
  return s ? `?${s}` : ''
}

export const api = {
  get: (ruta, params) => request('GET', ruta + qs(params)),
  post: (ruta, cuerpo) => request('POST', ruta, cuerpo),
  put: (ruta, cuerpo) => request('PUT', ruta, cuerpo),
  patch: (ruta, cuerpo) => request('PATCH', ruta, cuerpo),
  del: (ruta) => request('DELETE', ruta),
  upload: (ruta, formData) => request('POST', ruta, formData, true),
  url: (ruta) => BASE + ruta,
}
