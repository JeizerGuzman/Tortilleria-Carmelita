import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "tortilleria_carmelita.db")


def crear_base_de_datos():
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.executescript("""
        PRAGMA foreign_keys = ON;

        -- ══════════════════════════════════════════════════════════════
        --  TABLAS BASE
        -- ══════════════════════════════════════════════════════════════

        -- Categorías de productos
        CREATE TABLE IF NOT EXISTS Categoria (
            id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre       TEXT NOT NULL
        );

        -- Proveedores de insumos
        CREATE TABLE IF NOT EXISTS Proveedor (
            id_proveedor  INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre        TEXT NOT NULL,
            telefono      TEXT,
            representante TEXT
        );

        -- Usuarios del sistema
        CREATE TABLE IF NOT EXISTS Usuarios (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre     TEXT NOT NULL,
            rol        TEXT NOT NULL CHECK(rol IN ('administrador', 'trabajador')),
            telefono   TEXT,
            contrasena TEXT NOT NULL,
            activo     INTEGER NOT NULL DEFAULT 1   -- 0 = usuario dado de baja
        );

        -- ══════════════════════════════════════════════════════════════
        --  CONFIGURACIÓN DEL SISTEMA (clave-valor)
        -- ══════════════════════════════════════════════════════════════
        -- Ejemplos de claves:
        --   nombre_negocio, direccion, telefono_negocio, rfc
        --   precio_tortilla, unidad_venta, punto_reorden_default
        --   fondo_apertura_default, impresora_ticket, copias_ticket
        CREATE TABLE IF NOT EXISTS Configuracion (
            clave       TEXT PRIMARY KEY,
            valor       TEXT NOT NULL,
            descripcion TEXT             -- para mostrar en pantalla de configuración
        );

        -- ══════════════════════════════════════════════════════════════
        --  CATÁLOGO DE ARTÍCULOS
        -- ══════════════════════════════════════════════════════════════
        -- La tortilla tiene código fijo TORTILLA001.
        -- Los insumos de proveedores también se registran aquí.
        CREATE TABLE IF NOT EXISTS Articulo (
            codigo       TEXT PRIMARY KEY,
            nombre       TEXT NOT NULL,
            precio       REAL NOT NULL,
            costo        REAL NOT NULL DEFAULT 0,
            existencia   REAL NOT NULL DEFAULT 0,
            reorden      REAL NOT NULL DEFAULT 0,
            es_insumo    INTEGER NOT NULL DEFAULT 0,  -- 0=producto venta, 1=insumo interno
            id_categoria INTEGER NOT NULL,
            id_proveedor INTEGER,
            FOREIGN KEY (id_categoria) REFERENCES Categoria(id_categoria),
            FOREIGN KEY (id_proveedor) REFERENCES Proveedor(id_proveedor)
        );

        -- ══════════════════════════════════════════════════════════════
        --  TURNOS / CORTE DE CAJA
        -- ══════════════════════════════════════════════════════════════
        -- Un turno representa una sesión de trabajo (apertura → corte).
        -- Solo puede haber UN turno con estado 'abierto' a la vez.
        CREATE TABLE IF NOT EXISTS Turno (
            id_turno          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_apertura    TEXT NOT NULL,          -- DATETIME: '2025-05-17 08:00:00'
            fecha_cierre      TEXT,                   -- NULL mientras está abierto
            fondo_inicial     REAL NOT NULL DEFAULT 0,-- dinero con que abre la caja
            total_ventas      REAL,                   -- calculado al cerrar
            total_movimientos REAL,                   -- entradas - salidas de caja manual
            efectivo_esperado REAL,                   -- fondo + ventas + entradas - salidas
            efectivo_contado  REAL,                   -- lo que el cajero cuenta físicamente
            diferencia        REAL,                   -- contado - esperado (puede ser negativo)
            estado            TEXT NOT NULL DEFAULT 'abierto'
                                  CHECK(estado IN ('abierto', 'cerrado')),
            id_usuario_apertura INTEGER NOT NULL,
            id_usuario_cierre   INTEGER,
            notas               TEXT,                 -- observaciones del corte
            FOREIGN KEY (id_usuario_apertura) REFERENCES Usuarios(id_usuario),
            FOREIGN KEY (id_usuario_cierre)   REFERENCES Usuarios(id_usuario)
        );

        -- ══════════════════════════════════════════════════════════════
        --  MOVIMIENTOS DE CAJA  (gastos / entradas extra durante el turno)
        -- ══════════════════════════════════════════════════════════════
        -- Ejemplos: compra de bolsas, pago de gas, préstamo a empleado.
        CREATE TABLE IF NOT EXISTS MovimientoCaja (
            id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT,
            id_turno      INTEGER NOT NULL,
            tipo          TEXT NOT NULL CHECK(tipo IN ('entrada', 'salida')),
            concepto      TEXT NOT NULL,
            monto         REAL NOT NULL,
            fecha         TEXT NOT NULL,              -- DATETIME
            id_usuario    INTEGER NOT NULL,
            FOREIGN KEY (id_turno)   REFERENCES Turno(id_turno),
            FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario)
        );

        -- ══════════════════════════════════════════════════════════════
        --  VENTAS
        -- ══════════════════════════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS Venta (
            id_venta      INTEGER PRIMARY KEY AUTOINCREMENT,
            folio         TEXT NOT NULL UNIQUE,       -- 'TRT-00001'
            fecha         TEXT NOT NULL,              -- DATETIME completo
            importe       REAL NOT NULL,
            monto_recibido REAL NOT NULL DEFAULT 0,   -- lo que entregó el cliente
            cambio        REAL NOT NULL DEFAULT 0,    -- importe - monto_recibido
            estado        TEXT NOT NULL DEFAULT 'completada'
                              CHECK(estado IN ('completada', 'cancelada')),
            motivo_cancel TEXT,                       -- razón si fue cancelada
            id_turno      INTEGER NOT NULL,
            id_usuario    INTEGER NOT NULL,
            id_cancela    INTEGER,                    -- usuario que canceló
            FOREIGN KEY (id_turno)   REFERENCES Turno(id_turno),
            FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario),
            FOREIGN KEY (id_cancela) REFERENCES Usuarios(id_usuario)
        );

        -- Detalle de cada venta (cantidad en kg para tortilla)
        CREATE TABLE IF NOT EXISTS DetalleVenta (
            id_venta INTEGER,
            codigo   TEXT NOT NULL,
            cantidad REAL NOT NULL,
            precio   REAL NOT NULL,
            PRIMARY KEY (id_venta, codigo),
            FOREIGN KEY (id_venta) REFERENCES Venta(id_venta),
            FOREIGN KEY (codigo)   REFERENCES Articulo(codigo)
        );

        -- ══════════════════════════════════════════════════════════════
        --  COMPRAS A PROVEEDORES
        -- ══════════════════════════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS Compra (
            id_compra    INTEGER PRIMARY KEY AUTOINCREMENT,
            numdoc       TEXT NOT NULL,
            tipodoc      TEXT NOT NULL,               -- 'factura', 'remision', 'ticket'
            fecha        TEXT NOT NULL,               -- DATETIME completo
            importe      REAL NOT NULL,
            id_proveedor INTEGER NOT NULL,
            id_usuario   INTEGER NOT NULL,
            FOREIGN KEY (id_proveedor) REFERENCES Proveedor(id_proveedor),
            FOREIGN KEY (id_usuario)   REFERENCES Usuarios(id_usuario)
        );

        -- Detalle de cada compra
        CREATE TABLE IF NOT EXISTS DetalleCompra (
            id_compra INTEGER,
            codigo    TEXT NOT NULL,
            cantidad  REAL NOT NULL,
            costo     REAL NOT NULL,
            PRIMARY KEY (id_compra, codigo),
            FOREIGN KEY (id_compra) REFERENCES Compra(id_compra),
            FOREIGN KEY (codigo)    REFERENCES Articulo(codigo)
        );

        -- ══════════════════════════════════════════════════════════════
        --  MOVIMIENTOS DE INVENTARIO  (auditoría de stock)
        -- ══════════════════════════════════════════════════════════════
        -- Cada vez que la existencia de un artículo cambia, se registra aquí.
        -- Tipos:
        --   entrada_compra  → originado por una Compra
        --   salida_venta    → originado por una Venta
        --   ajuste_manual   → el admin corrige el stock manualmente
        --   merma           → desperdicio o pérdida registrada
        CREATE TABLE IF NOT EXISTS MovimientoInventario (
            id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo        TEXT NOT NULL,
            tipo          TEXT NOT NULL CHECK(tipo IN (
                              'entrada_compra',
                              'salida_venta',
                              'entrada_produccion',   -- ← nueva para registrar la tortilla que se produce internamente
                              'ajuste_manual',
                              'merma'
                          )),
            cantidad      REAL NOT NULL,              -- positivo=entrada, negativo=salida
            existencia_anterior REAL NOT NULL,        -- stock antes del movimiento
            existencia_nueva    REAL NOT NULL,        -- stock después del movimiento
            referencia    TEXT,                       -- id_compra, id_venta, o descripción
            fecha         TEXT NOT NULL,              -- DATETIME
            id_usuario    INTEGER NOT NULL,
            FOREIGN KEY (codigo)     REFERENCES Articulo(codigo),
            FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario)
        );
    """)

    # ── Datos iniciales ───────────────────────────────────────────────────────

    # Categorías
    cursor.executemany(
        "INSERT OR IGNORE INTO Categoria (id_categoria, nombre) VALUES (?,?)", [
        (1, 'Tortillas y Derivados'),
        (2, 'Insumos de producción'),
        (3, 'Otros'),
    ])

    # Proveedores
    cursor.executemany(
        "INSERT OR IGNORE INTO Proveedor (id_proveedor, nombre, telefono, representante) VALUES (?,?,?,?)", [
        (1, 'Proveedor General', '9610000000', 'Contacto General'),
    ])

    # Usuarios
    cursor.executemany(
        "INSERT OR IGNORE INTO Usuarios (id_usuario, nombre, rol, telefono, contrasena) VALUES (?,?,?,?,?)", [
        (1, 'Administrador',      'administrador', '9161579322', '07'),
        (2, 'Trabajador General', 'trabajador',    '0000000000', '1234'),
    ])

    # Artículo fijo: Tortilla
    cursor.execute("""
        INSERT OR IGNORE INTO Articulo
            (codigo, nombre, precio, costo, existencia, reorden, es_insumo, id_categoria, id_proveedor)
        VALUES
            ('TORTILLA001', 'Tortilla', 18.0, 0.0, 0.0, 0.0, 0, 1, NULL)
    """)

    # Configuración inicial del sistema
    configuraciones = [
        # Del negocio
        ('nombre_negocio',        'Tortillería Carmelita',  'Nombre del negocio (aparece en tickets)'),
        ('direccion',             '',                        'Dirección del local'),
        ('telefono_negocio',      '',                        'Teléfono del negocio'),
        ('rfc',                   '',                        'RFC (opcional, para facturas)'),
        # De operación
        ('precio_tortilla',       '18.0',                   'Precio por kg de tortilla'),
        ('unidad_venta',          'kg',                      'Unidad de medida para venta de tortilla'),
        ('punto_reorden_default', '10.0',                   'Stock mínimo por defecto antes de alertar'),
        # De caja
        ('fondo_apertura_default','200.0',                  'Fondo con que abre la caja normalmente'),
        # De impresión
        ('impresora_ticket',      '',                        'Nombre o puerto de la impresora de tickets'),
        ('copias_ticket',         '1',                       'Número de copias por ticket de venta'),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO Configuracion (clave, valor, descripcion)
        VALUES (?, ?, ?)
    """, configuraciones)

    conn.commit()
    conn.close()
    print("✅ Base de datos creada correctamente.")
    print(f"   Ubicación: {DB_PATH}")
    print()
    print("Tablas creadas:")
    print("  • Categoria              — categorías de artículos")
    print("  • Proveedor              — proveedores de insumos")
    print("  • Usuarios               — usuarios del sistema (admin / trabajador)")
    print("  • Configuracion          — parámetros del negocio (clave-valor)")
    print("  • Articulo               — catálogo de productos e insumos")
    print("  • Turno                  — sesiones de caja / corte")
    print("  • MovimientoCaja         — gastos y entradas extra por turno")
    print("  • Venta                  — registro de ventas")
    print("  • DetalleVenta           — ítems de cada venta")
    print("  • Compra                 — compras a proveedores")
    print("  • DetalleCompra          — ítems de cada compra")
    print("  • MovimientoInventario   — auditoría de cambios en existencias")


if __name__ == "__main__":
    crear_base_de_datos()