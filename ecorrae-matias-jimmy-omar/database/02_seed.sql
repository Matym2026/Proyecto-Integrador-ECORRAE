-- =====================================================================
-- EcoRAEE Cloud - Datos de prueba
-- =====================================================================

INSERT INTO usuarios (nombre, email, rol) VALUES
 ('Ana Torres',      'ana.torres@ecoraee.ec',     'ADMIN'),
 ('Carlos Mena',     'carlos.mena@ecoraee.ec',    'OPERADOR'),
 ('Lucía Andrade',   'lucia.andrade@ecoraee.ec',  'EVALUADOR'),
 ('Diego Salazar',   'diego.salazar@ecoraee.ec',  'EVALUADOR'),
 ('María Cevallos',  'maria.cevallos@ecoraee.ec', 'AUDITOR');

INSERT INTO centros (nombre, tipo, ciudad, direccion, responsable, telefono) VALUES
 ('Centro de Acopio Quito Norte',    'ACOPIO',      'Quito',     'Av. de la Prensa N58-120',      'Carlos Mena',   '022456789'),
 ('Centro de Acopio Guayaquil Sur',  'ACOPIO',      'Guayaquil', 'Av. 25 de Julio y Pío Jaramillo','Rosa Villacís', '042345678'),
 ('Bodega Central Quito',            'ALMACEN',     'Quito',     'Panamericana Sur km 12',        'Ana Torres',    '022987654'),
 ('Planta de Tratamiento Cuenca',    'TRATAMIENTO', 'Cuenca',    'Parque Industrial, calle C',    'Pablo Ordóñez', '072876543');

INSERT INTO destinos (nombre, tipo, ruc, licencia_ambiental, ciudad, contacto) VALUES
 ('Reciclatech Ecuador',           'RECICLAJE',         '1792345678001', 'MAAE-LA-2024-0112', 'Quito',     'reciclaje@reciclatech.ec'),
 ('Fundación Reconecta',           'DONACION',          '0992345678001', NULL,                'Guayaquil', 'donaciones@reconecta.org'),
 ('Recupera Andes',                'REUTILIZACION',     '0192345678001', 'MAAE-LA-2023-0457', 'Cuenca',    'ventas@recuperaandes.ec'),
 ('Gestora Ambiental Pichincha',   'DISPOSICION_FINAL', '1793456789001', 'MAAE-LA-2022-0890', 'Quito',     'operaciones@gap.ec');

-- Lotes
INSERT INTO lotes (codigo, descripcion, centro_id, destino_id, estado, creado_por, fecha_creacion, fecha_cierre) VALUES
 ('LOTE-2026-001', 'Equipos de cómputo dados de baja - oficina matriz', 3, 1, 'ENTREGADO', 1, '2026-10-05 09:00', '2026-10-12 15:30'),
 ('LOTE-2026-002', 'Impresoras y servidor del data center',             1, NULL, 'ABIERTO', 2, '2026-10-20 10:00', NULL),
 ('LOTE-2026-003', 'Dispositivos móviles recolectados en campaña',     2, NULL, 'ABIERTO', 2, '2026-10-25 11:00', NULL);

-- Dispositivos
INSERT INTO dispositivos (codigo_trazabilidad, tipo, marca, modelo, numero_serie, peso_kg, estado, centro_actual_id, lote_id, registrado_por, origen, observaciones, fecha_registro) VALUES
 ('RAEE-2026-00001','PORTATIL',        'Dell',    'Latitude 5490',        'DL5490-8K2M1',  2.10,'EN_DESTINO', 3, 1,    2,'Oficina matriz - Contabilidad','Pantalla rota',               '2026-10-01 08:30'),
 ('RAEE-2026-00002','COMPUTADOR',      'HP',      'ProDesk 600 G3',       'HP600-MXL7731', 7.50,'EN_DESTINO', 3, 1,    2,'Oficina matriz - Ventas',      'No enciende',                 '2026-10-01 08:45'),
 ('RAEE-2026-00003','MONITOR',         'Samsung', 'S22F350',              'SM22-ZZ0912',   3.20,'EN_DESTINO', 3, 1,    2,'Oficina matriz - Ventas',      NULL,                          '2026-10-01 09:00'),
 ('RAEE-2026-00004','IMPRESORA',       'Epson',   'L3150',                'EP3150-X55A',   4.30,'EN_LOTE',    1, 2,    2,'Empresa cliente Insumos SA',   'Cabezal dañado',              '2026-10-15 10:10'),
 ('RAEE-2026-00005','SERVIDOR',        'HPE',     'ProLiant DL380 Gen9',  'CZ2649ABCD',   18.00,'EN_LOTE',    1, 2,    2,'Data center cliente',          'Discos retirados',            '2026-10-15 10:30'),
 ('RAEE-2026-00006','CELULAR',         'Samsung', 'Galaxy A52',           'R58R12ABC34',   0.19,'EVALUADO',   2, NULL, 2,'Campaña Guayaquil Recicla',    NULL,                          '2026-10-22 14:00'),
 ('RAEE-2026-00007','TABLET',          'Lenovo',  'Tab M10',              'HA1B2C3D',      0.46,'EN_LOTE',    2, 3,    2,'Campaña Guayaquil Recicla',    'Batería hinchada',            '2026-10-22 14:15'),
 ('RAEE-2026-00008','EQUIPO_RED',      'Cisco',   'Catalyst 2960',        'FOC1234X0YZ',   3.60,'REGISTRADO', 1, NULL, 2,'Data center cliente',          NULL,                          '2026-10-28 09:00'),
 ('RAEE-2026-00009','PORTATIL',        'Lenovo',  'ThinkPad T470',        'PF0XYZ12',      1.60,'REGISTRADO', 2, NULL, 2,'Campaña Guayaquil Recicla',    'Teclado incompleto',          '2026-10-29 16:20'),
 ('RAEE-2026-00010','MONITOR',         'LG',      '24MK430H',             'LG24-905RA',    2.90,'EVALUADO',   1, NULL, 2,'Oficina matriz - RRHH',        NULL,                          '2026-10-30 11:00'),
 ('RAEE-2026-00011','ELECTRODOMESTICO','Mabe',    'Microondas HMM70S',    'MB70-2231',    11.50,'REGISTRADO', 2, NULL, 2,'Donación ciudadana',           NULL,                          '2026-11-02 10:00'),
 ('RAEE-2026-00012','COMPUTADOR',      'Lenovo',  'ThinkCentre M720q',    'MJ0ABC12',      1.30,'REGISTRADO', 1, NULL, 2,'Oficina matriz - Sistemas',    'Fuente quemada',              '2026-11-03 08:40');

-- Evaluaciones técnicas
INSERT INTO evaluaciones (dispositivo_id, evaluador_id, fecha, estado_fisico, funcional, contiene_peligrosos, datos_borrados, recomendacion, observaciones) VALUES
 (1, 3, '2026-10-03 10:00', 'REGULAR', FALSE, FALSE, TRUE,  'RECICLAJE',         'Disco borrado con DoD 5220.22-M'),
 (2, 3, '2026-10-03 10:30', 'MALO',    FALSE, FALSE, TRUE,  'RECICLAJE',         'Placa madre con capacitores dañados'),
 (3, 4, '2026-10-03 11:00', 'MALO',    FALSE, FALSE, FALSE, 'RECICLAJE',         'Panel quebrado'),
 (4, 4, '2026-10-17 09:00', 'MALO',    FALSE, TRUE,  FALSE, 'RECICLAJE',         'Restos de tinta, manejo especial'),
 (5, 3, '2026-10-17 09:40', 'BUENO',   TRUE,  FALSE, TRUE,  'REUTILIZACION',     'Apto para reacondicionamiento'),
 (6, 4, '2026-10-23 15:00', 'REGULAR', TRUE,  FALSE, TRUE,  'REUTILIZACION',     'Restablecido de fábrica'),
 (7, 4, '2026-10-23 15:20', 'MALO',    FALSE, TRUE,  FALSE, 'DISPOSICION_FINAL', 'Batería de litio hinchada: residuo peligroso'),
 (10,3, '2026-10-31 10:00', 'BUENO',   TRUE,  FALSE, TRUE,  'REUTILIZACION',     NULL);

-- Movimientos: ingreso de cada dispositivo a su centro de acopio
INSERT INTO movimientos (tipo, dispositivo_id, centro_destino_id, responsable_id, fecha, observaciones)
SELECT 'INGRESO', d.id,
       CASE WHEN d.id IN (1,2,3) THEN 1 ELSE d.centro_actual_id END,
       2, d.fecha_registro, 'Ingreso inicial al centro de acopio'
FROM dispositivos d ORDER BY d.id;

-- Ciclo completo del LOTE-2026-001: traslado a bodega y entrega al gestor
INSERT INTO movimientos (tipo, lote_id, centro_origen_id, centro_destino_id, responsable_id, guia_remision, fecha, observaciones) VALUES
 ('TRASLADO', 1, 1, 3, 2, 'GR-001-0001245', '2026-10-08 08:00', 'Traslado a bodega central para consolidación');
INSERT INTO movimientos (tipo, lote_id, centro_origen_id, destino_id, responsable_id, guia_remision, fecha, observaciones) VALUES
 ('ENTREGA_DESTINO', 1, 3, 1, 1, 'GR-001-0001302', '2026-10-12 15:30', 'Entregado con acta de recepción firmada');
