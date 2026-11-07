const op = (lista) => lista.map(([value, label]) => ({ value, label }))

export const TIPOS_DISPOSITIVO = op([
  ['COMPUTADOR', 'Computador de escritorio'], ['PORTATIL', 'Portátil'], ['MONITOR', 'Monitor'],
  ['IMPRESORA', 'Impresora'], ['CELULAR', 'Celular'], ['TABLET', 'Tablet'], ['SERVIDOR', 'Servidor'],
  ['EQUIPO_RED', 'Equipo de red'], ['ELECTRODOMESTICO', 'Electrodoméstico'], ['OTRO', 'Otro'],
])
export const ESTADOS_DISPOSITIVO = op([
  ['REGISTRADO', 'Registrado'], ['EVALUADO', 'Evaluado'], ['EN_LOTE', 'En lote'], ['EN_DESTINO', 'En destino final'],
])
export const ESTADOS_LOTE = op([['ABIERTO', 'Abierto'], ['CERRADO', 'Cerrado'], ['ENTREGADO', 'Entregado']])
export const TIPOS_CENTRO = op([['ACOPIO', 'Acopio'], ['ALMACEN', 'Almacén'], ['TRATAMIENTO', 'Tratamiento']])
export const TIPOS_DESTINO = op([
  ['RECICLAJE', 'Reciclaje'], ['REUTILIZACION', 'Reutilización'], ['DONACION', 'Donación'],
  ['DISPOSICION_FINAL', 'Disposición final'],
])
export const ROLES = op([['ADMIN', 'Administrador'], ['OPERADOR', 'Operador'], ['EVALUADOR', 'Evaluador'], ['AUDITOR', 'Auditor']])
export const ESTADOS_FISICOS = op([['BUENO', 'Bueno'], ['REGULAR', 'Regular'], ['MALO', 'Malo']])
export const RECOMENDACIONES = op([
  ['REUTILIZACION', 'Reutilización'], ['RECICLAJE', 'Reciclaje'], ['DISPOSICION_FINAL', 'Disposición final'],
])
export const TIPOS_MOVIMIENTO = op([['INGRESO', 'Ingreso'], ['TRASLADO', 'Traslado'], ['ENTREGA_DESTINO', 'Entrega a destino']])

const todas = [TIPOS_DISPOSITIVO, ESTADOS_DISPOSITIVO, ESTADOS_LOTE, TIPOS_CENTRO, TIPOS_DESTINO, ROLES,
  ESTADOS_FISICOS, RECOMENDACIONES, TIPOS_MOVIMIENTO].flat()
export const etiqueta = (v) => todas.find((o) => o.value === v)?.label || v

export const fecha = (iso) => (iso ? new Date(iso).toLocaleString('es-EC', { dateStyle: 'medium', timeStyle: 'short' }) : '—')
export const kg = (n) => `${Number(n).toLocaleString('es-EC', { maximumFractionDigits: 2 })} kg`
