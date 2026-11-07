-- =====================================================================
-- EcoRAEE Cloud - Esquema de base de datos (PostgreSQL 14+)
-- Parte II: implementación local. En la Parte I este esquema corre en
-- Amazon RDS PostgreSQL dentro de la subred privada de BD (sg-rds).
-- =====================================================================

DROP TABLE IF EXISTS evidencias   CASCADE;
DROP TABLE IF EXISTS movimientos  CASCADE;
DROP TABLE IF EXISTS evaluaciones CASCADE;
DROP TABLE IF EXISTS dispositivos CASCADE;
DROP TABLE IF EXISTS lotes        CASCADE;
DROP TABLE IF EXISTS destinos     CASCADE;
DROP TABLE IF EXISTS centros      CASCADE;
DROP TABLE IF EXISTS usuarios     CASCADE;

-- ---------------------------------------------------------------------
-- USUARIOS: personas que operan el sistema
-- ---------------------------------------------------------------------
CREATE TABLE usuarios (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(120) NOT NULL,
    email       VARCHAR(150) NOT NULL UNIQUE,
    rol         VARCHAR(20)  NOT NULL
                CHECK (rol IN ('ADMIN','OPERADOR','EVALUADOR','AUDITOR')),
    activo      BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en   TIMESTAMP    NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_usuarios_email CHECK (email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$')
);

-- ---------------------------------------------------------------------
-- CENTROS: puntos de acopio, almacenamiento o tratamiento
-- ---------------------------------------------------------------------
CREATE TABLE centros (
    id           SERIAL PRIMARY KEY,
    nombre       VARCHAR(120) NOT NULL UNIQUE,
    tipo         VARCHAR(20)  NOT NULL
                 CHECK (tipo IN ('ACOPIO','ALMACEN','TRATAMIENTO')),
    ciudad       VARCHAR(80)  NOT NULL,
    direccion    VARCHAR(200),
    responsable  VARCHAR(120),
    telefono     VARCHAR(20),
    activo       BOOLEAN      NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- DESTINOS: gestores autorizados donde termina el RAEE
-- ---------------------------------------------------------------------
CREATE TABLE destinos (
    id                  SERIAL PRIMARY KEY,
    nombre              VARCHAR(120) NOT NULL UNIQUE,
    tipo                VARCHAR(20)  NOT NULL
                        CHECK (tipo IN ('REUTILIZACION','RECICLAJE','DISPOSICION_FINAL','DONACION')),
    ruc                 VARCHAR(13)  CHECK (ruc IS NULL OR ruc ~ '^[0-9]{13}$'),
    licencia_ambiental  VARCHAR(60),
    ciudad              VARCHAR(80)  NOT NULL,
    contacto            VARCHAR(120),
    activo              BOOLEAN      NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- LOTES: agrupación de dispositivos para traslado o entrega
-- ---------------------------------------------------------------------
CREATE TABLE lotes (
    id              SERIAL PRIMARY KEY,
    codigo          VARCHAR(30)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255),
    centro_id       INTEGER      NOT NULL REFERENCES centros(id)  ON DELETE RESTRICT,
    destino_id      INTEGER               REFERENCES destinos(id) ON DELETE RESTRICT,
    estado          VARCHAR(20)  NOT NULL DEFAULT 'ABIERTO'
                    CHECK (estado IN ('ABIERTO','CERRADO','ENTREGADO')),
    creado_por      INTEGER               REFERENCES usuarios(id) ON DELETE SET NULL,
    fecha_creacion  TIMESTAMP    NOT NULL DEFAULT NOW(),
    fecha_cierre    TIMESTAMP,
    CONSTRAINT chk_lote_entregado_destino
        CHECK (estado <> 'ENTREGADO' OR destino_id IS NOT NULL),
    CONSTRAINT chk_lote_fechas
        CHECK (fecha_cierre IS NULL OR fecha_cierre >= fecha_creacion)
);

-- ---------------------------------------------------------------------
-- DISPOSITIVOS: cada aparato RAEE registrado
-- ---------------------------------------------------------------------
CREATE TABLE dispositivos (
    id                   SERIAL PRIMARY KEY,
    codigo_trazabilidad  VARCHAR(30)   NOT NULL UNIQUE,
    tipo                 VARCHAR(30)   NOT NULL
                         CHECK (tipo IN ('COMPUTADOR','PORTATIL','MONITOR','IMPRESORA',
                                         'CELULAR','TABLET','SERVIDOR','EQUIPO_RED',
                                         'ELECTRODOMESTICO','OTRO')),
    marca                VARCHAR(60)   NOT NULL,
    modelo               VARCHAR(80),
    numero_serie         VARCHAR(80)   UNIQUE,
    peso_kg              NUMERIC(8,2)  NOT NULL CHECK (peso_kg > 0 AND peso_kg <= 2000),
    estado               VARCHAR(20)   NOT NULL DEFAULT 'REGISTRADO'
                         CHECK (estado IN ('REGISTRADO','EVALUADO','EN_LOTE','EN_DESTINO')),
    centro_actual_id     INTEGER       NOT NULL REFERENCES centros(id)  ON DELETE RESTRICT,
    lote_id              INTEGER                REFERENCES lotes(id)    ON DELETE SET NULL,
    registrado_por       INTEGER                REFERENCES usuarios(id) ON DELETE SET NULL,
    origen               VARCHAR(150),
    observaciones        TEXT,
    fecha_registro       TIMESTAMP     NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------
-- EVALUACIONES: diagnóstico técnico de cada dispositivo
-- ---------------------------------------------------------------------
CREATE TABLE evaluaciones (
    id                   SERIAL PRIMARY KEY,
    dispositivo_id       INTEGER      NOT NULL REFERENCES dispositivos(id) ON DELETE CASCADE,
    evaluador_id         INTEGER      NOT NULL REFERENCES usuarios(id)     ON DELETE RESTRICT,
    fecha                TIMESTAMP    NOT NULL DEFAULT NOW(),
    estado_fisico        VARCHAR(10)  NOT NULL CHECK (estado_fisico IN ('BUENO','REGULAR','MALO')),
    funcional            BOOLEAN      NOT NULL,
    contiene_peligrosos  BOOLEAN      NOT NULL DEFAULT FALSE,
    datos_borrados       BOOLEAN      NOT NULL DEFAULT FALSE,
    recomendacion        VARCHAR(20)  NOT NULL
                         CHECK (recomendacion IN ('REUTILIZACION','RECICLAJE','DISPOSICION_FINAL')),
    observaciones        TEXT,
    -- Un equipo que se reutiliza debe salir funcional y con datos borrados
    CONSTRAINT chk_eval_reutilizacion
        CHECK (recomendacion <> 'REUTILIZACION' OR (funcional AND datos_borrados))
);

-- ---------------------------------------------------------------------
-- MOVIMIENTOS: historial de trazabilidad (ingreso, traslados, entrega)
-- Aplica a un dispositivo individual o a un lote completo.
-- ---------------------------------------------------------------------
CREATE TABLE movimientos (
    id                 SERIAL PRIMARY KEY,
    tipo               VARCHAR(20)  NOT NULL
                       CHECK (tipo IN ('INGRESO','TRASLADO','ENTREGA_DESTINO')),
    dispositivo_id     INTEGER      REFERENCES dispositivos(id) ON DELETE CASCADE,
    lote_id            INTEGER      REFERENCES lotes(id)        ON DELETE CASCADE,
    centro_origen_id   INTEGER      REFERENCES centros(id)      ON DELETE RESTRICT,
    centro_destino_id  INTEGER      REFERENCES centros(id)      ON DELETE RESTRICT,
    destino_id         INTEGER      REFERENCES destinos(id)     ON DELETE RESTRICT,
    responsable_id     INTEGER      REFERENCES usuarios(id)     ON DELETE SET NULL,
    guia_remision      VARCHAR(40),
    fecha              TIMESTAMP    NOT NULL DEFAULT NOW(),
    observaciones      TEXT,
    CONSTRAINT chk_mov_sujeto CHECK (dispositivo_id IS NOT NULL OR lote_id IS NOT NULL),
    CONSTRAINT chk_mov_ingreso  CHECK (tipo <> 'INGRESO'  OR centro_destino_id IS NOT NULL),
    CONSTRAINT chk_mov_traslado CHECK (tipo <> 'TRASLADO' OR
               (centro_origen_id IS NOT NULL AND centro_destino_id IS NOT NULL
                AND centro_origen_id <> centro_destino_id)),
    CONSTRAINT chk_mov_entrega  CHECK (tipo <> 'ENTREGA_DESTINO' OR destino_id IS NOT NULL)
);

-- ---------------------------------------------------------------------
-- EVIDENCIAS: metadatos de archivos (fotos, actas, certificados).
-- El archivo vive en el almacenamiento de objetos (local hoy, S3 mañana);
-- aquí solo se guarda la clave del objeto.
-- ---------------------------------------------------------------------
CREATE TABLE evidencias (
    id              SERIAL PRIMARY KEY,
    dispositivo_id  INTEGER       REFERENCES dispositivos(id) ON DELETE CASCADE,
    lote_id         INTEGER       REFERENCES lotes(id)        ON DELETE CASCADE,
    nombre_archivo  VARCHAR(255)  NOT NULL,
    clave_objeto    VARCHAR(400)  NOT NULL UNIQUE,
    tipo_mime       VARCHAR(100)  NOT NULL,
    tamano_bytes    INTEGER       NOT NULL CHECK (tamano_bytes > 0),
    descripcion     VARCHAR(255),
    subido_por      INTEGER       REFERENCES usuarios(id) ON DELETE SET NULL,
    fecha           TIMESTAMP     NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_evid_sujeto CHECK (dispositivo_id IS NOT NULL OR lote_id IS NOT NULL)
);

-- Índices para las consultas de trazabilidad
CREATE INDEX idx_dispositivos_estado ON dispositivos(estado);
CREATE INDEX idx_dispositivos_lote   ON dispositivos(lote_id);
CREATE INDEX idx_dispositivos_centro ON dispositivos(centro_actual_id);
CREATE INDEX idx_evaluaciones_disp   ON evaluaciones(dispositivo_id);
CREATE INDEX idx_movimientos_disp    ON movimientos(dispositivo_id);
CREATE INDEX idx_movimientos_lote    ON movimientos(lote_id);
CREATE INDEX idx_evidencias_disp     ON evidencias(dispositivo_id);
CREATE INDEX idx_evidencias_lote     ON evidencias(lote_id);
