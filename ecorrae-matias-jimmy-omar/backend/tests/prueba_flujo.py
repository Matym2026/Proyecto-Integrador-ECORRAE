"""Prueba de integración del flujo completo de trazabilidad contra la API local.
Uso (con el backend corriendo):  python tests/prueba_flujo.py
"""
import sys

import httpx

API = "http://localhost:8000/api"
c = httpx.Client(base_url=API, timeout=10)
ok = 0


def check(cond, msg):
    global ok
    if not cond:
        print(f"  FALLA: {msg}")
        sys.exit(1)
    ok += 1
    print(f"  ok  {msg}")


print("1. Registro de dispositivo")
r = c.post("/dispositivos", json={"tipo": "PORTATIL", "marca": "Acer", "modelo": "Aspire 5",
                                  "numero_serie": "PRUEBA-001", "peso_kg": 1.9, "centro_actual_id": 1,
                                  "registrado_por": 2, "origen": "Prueba automática"})
check(r.status_code == 201, f"crear dispositivo -> {r.status_code}")
d = r.json()
check(d["codigo_trazabilidad"].startswith("RAEE-"), f"código generado {d['codigo_trazabilidad']}")
check(d["estado"] == "REGISTRADO", "estado REGISTRADO")
movs = c.get("/movimientos", params={"dispositivo_id": d["id"]}).json()
check(len(movs) == 1 and movs[0]["tipo"] == "INGRESO", "movimiento INGRESO automático")

print("2. Validaciones de entrada")
r = c.post("/dispositivos", json={"tipo": "XYZ", "marca": "", "peso_kg": -1, "centro_actual_id": 1})
check(r.status_code == 422, f"datos inválidos -> 422 ({r.json()['detail'][:70]}...)")
r = c.post("/dispositivos", json={"tipo": "MONITOR", "marca": "LG", "numero_serie": "PRUEBA-001",
                                  "peso_kg": 2, "centro_actual_id": 1})
check(r.status_code == 409, f"serie duplicada -> 409 ({r.json()['detail']})")
r = c.get("/dispositivos/99999")
check(r.status_code == 404, "dispositivo inexistente -> 404")
r = c.post("/evaluaciones", json={"dispositivo_id": d["id"], "evaluador_id": 3, "estado_fisico": "BUENO",
                                  "funcional": False, "recomendacion": "REUTILIZACION"})
check(r.status_code == 422, "regla: REUTILIZACION exige funcional y datos borrados")
r = c.post("/evaluaciones", json={"dispositivo_id": d["id"], "evaluador_id": 2, "estado_fisico": "BUENO",
                                  "funcional": True, "recomendacion": "RECICLAJE"})
check(r.status_code == 400, f"regla: evaluador sin rol ({r.json()['detail']})")

print("3. Evaluación técnica")
r = c.post("/evaluaciones", json={"dispositivo_id": d["id"], "evaluador_id": 3, "estado_fisico": "MALO",
                                  "funcional": False, "contiene_peligrosos": True, "datos_borrados": True,
                                  "recomendacion": "RECICLAJE", "observaciones": "Batería dañada"})
check(r.status_code == 201, "crear evaluación")
check(c.get(f"/dispositivos/{d['id']}").json()["estado"] == "EVALUADO", "dispositivo pasa a EVALUADO")

print("4. Lote")
r = c.post("/lotes", json={"descripcion": "Lote de prueba", "centro_id": 1, "creado_por": 2})
check(r.status_code == 201, f"crear lote {r.json().get('codigo')}")
lote = r.json()
r = c.post(f"/lotes/{lote['id']}/dispositivos", json={"dispositivo_ids": [d["id"], 10]})
check(r.status_code == 200 and r.json()["total_dispositivos"] == 2, "asignar 2 dispositivos")
r = c.post(f"/lotes/{lote['id']}/dispositivos", json={"dispositivo_ids": [8]})
check(r.status_code == 400, f"rechaza dispositivo no evaluado ({r.json()['detail']})")
r = c.post("/movimientos", json={"tipo": "TRASLADO", "lote_id": lote["id"], "centro_destino_id": 3})
check(r.status_code == 400, "no se mueve un lote ABIERTO")
r = c.post(f"/lotes/{lote['id']}/cerrar")
check(r.json()["estado"] == "CERRADO", "cerrar lote")

print("5. Traslado y entrega")
r = c.post("/movimientos", json={"tipo": "TRASLADO", "lote_id": lote["id"], "centro_destino_id": 3,
                                 "responsable_id": 2, "guia_remision": "GR-PRUEBA-1"})
check(r.status_code == 201, "traslado del lote a Bodega Central")
check(c.get(f"/dispositivos/{d['id']}").json()["centro_actual_id"] == 3, "dispositivos cambian de centro")
r = c.post("/movimientos", json={"tipo": "ENTREGA_DESTINO", "lote_id": lote["id"], "destino_id": 2})
check(r.status_code == 400, f"regla ambiental: peligrosos no van a DONACION")
r = c.post("/movimientos", json={"tipo": "ENTREGA_DESTINO", "lote_id": lote["id"], "destino_id": 1,
                                 "responsable_id": 1, "guia_remision": "GR-PRUEBA-2"})
check(r.status_code == 201, "entrega a Reciclatech")
check(c.get(f"/lotes/{lote['id']}").json()["estado"] == "ENTREGADO", "lote ENTREGADO")
check(c.get(f"/dispositivos/{d['id']}").json()["estado"] == "EN_DESTINO", "dispositivo EN_DESTINO")

print("6. Evidencia (almacenamiento local que simula S3)")
png = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                    "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082")
r = c.post("/evidencias", data={"dispositivo_id": d["id"], "descripcion": "Foto de prueba"},
           files={"archivo": ("foto.png", png, "image/png")})
check(r.status_code == 201, f"subir evidencia -> clave {r.json().get('clave_objeto')}")
ev = r.json()
r = c.get(f"/evidencias/{ev['id']}/archivo")
check(r.status_code == 200 and r.content == png, "descargar evidencia íntegra")
r = c.post("/evidencias", data={"dispositivo_id": d["id"]}, files={"archivo": ("x.exe", b"MZ", "application/x-msdownload")})
check(r.status_code == 415, "rechaza tipo de archivo no permitido")

print("7. Trazabilidad completa")
t = c.get(f"/dispositivos/{d['id']}/trazabilidad").json()
tipos = [e["tipo"] for e in t["linea_tiempo"]]
print("     " + " -> ".join(tipos))
for esperado in ("REGISTRO", "INGRESO", "EVALUACION", "TRASLADO", "ENTREGA_DESTINO", "EVIDENCIA"):
    check(esperado in tipos, f"línea de tiempo incluye {esperado}")

print("8. Integridad referencial y CRUD de catálogos")
r = c.delete("/centros/1")
check(r.status_code == 409, f"no elimina centro con dispositivos ({r.json()['detail']})")
r = c.delete(f"/dispositivos/{d['id']}")
check(r.status_code == 409, "no elimina dispositivo ya entregado")
r = c.post("/centros", json={"nombre": "Centro Prueba", "tipo": "ACOPIO", "ciudad": "Ambato", "telefono": "032123456"})
check(r.status_code == 201, "crear centro")
cid = r.json()["id"]
r = c.put(f"/centros/{cid}", json={"nombre": "Centro Prueba Ambato", "tipo": "ACOPIO", "ciudad": "Ambato"})
check(r.json()["nombre"] == "Centro Prueba Ambato", "actualizar centro")
check(c.delete(f"/centros/{cid}").status_code == 204, "eliminar centro sin relaciones")
r = c.post("/centros", json={"nombre": "X", "tipo": "ACOPIO", "ciudad": "Q", "telefono": "abc"})
check(r.status_code == 422, "valida longitud y teléfono")

print("9. Dashboard")
dash = c.get("/dashboard").json()
check(dash["total_dispositivos"] >= 13, f"total dispositivos {dash['total_dispositivos']}, entregado {dash['peso_entregado_kg']} kg")

print(f"\nTODAS LAS PRUEBAS PASARON ({ok} verificaciones)")
