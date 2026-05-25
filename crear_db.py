import sqlite3
from conexion import obtener_db_path

DB_PATH = obtener_db_path()


def crear_base_de_datos():
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.executescript("""
        PRAGMA foreign_keys = ON;

        -- ══════════════════════════════════════════════════════════════
        --  TABLAS BASE
        -- ══════════════════════════════════════════════════════════════

        CREATE TABLE IF NOT EXISTS Categoria (
            id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre       TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS Proveedor (
            id_proveedor  INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre        TEXT NOT NULL,
            telefono      TEXT,
            representante TEXT
        );

        CREATE TABLE IF NOT EXISTS Usuarios (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre     TEXT NOT NULL,
            rol        TEXT NOT NULL CHECK(rol IN ('administrador', 'trabajador')),
            telefono   TEXT,
            contrasena TEXT NOT NULL,
            activo     INTEGER NOT NULL DEFAULT 1
        );

        -- ══════════════════════════════════════════════════════════════
        --  CONFIGURACIÓN DEL SISTEMA
        -- ══════════════════════════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS Configuracion (
            clave       TEXT PRIMARY KEY,
            valor       TEXT NOT NULL,
            descripcion TEXT
        );

        -- ══════════════════════════════════════════════════════════════
        --  CATÁLOGO DE ARTÍCULOS
        -- ══════════════════════════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS Articulo (
            codigo       TEXT PRIMARY KEY,
            nombre       TEXT NOT NULL,
            precio       REAL NOT NULL,
            costo        REAL NOT NULL DEFAULT 0,
            existencia   REAL NOT NULL DEFAULT 0,
            reorden      REAL NOT NULL DEFAULT 0,
            es_insumo    INTEGER NOT NULL DEFAULT 0,
            id_categoria INTEGER NOT NULL,
            id_proveedor INTEGER,
            FOREIGN KEY (id_categoria) REFERENCES Categoria(id_categoria),
            FOREIGN KEY (id_proveedor) REFERENCES Proveedor(id_proveedor)
        );

        -- ══════════════════════════════════════════════════════════════
        --  RECETA DE PRODUCCIÓN
        -- ══════════════════════════════════════════════════════════════
        -- Define cuánto insumo se consume para producir cierta cantidad
        -- de producto. La relación es configurable desde Configuracion.
        -- Ejemplo base: 1 bulto harina → 40 kg tortilla
        CREATE TABLE IF NOT EXISTS RecetaProduccion (
            id_receta         INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_producto   TEXT NOT NULL,
            codigo_insumo     TEXT NOT NULL,
            cantidad_insumo   REAL NOT NULL,
            cantidad_producto REAL NOT NULL,
            unidad_insumo     TEXT NOT NULL DEFAULT 'bulto',
            activa            INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (codigo_producto) REFERENCES Articulo(codigo),
            FOREIGN KEY (codigo_insumo)   REFERENCES Articulo(codigo)
        );

        -- ══════════════════════════════════════════════════════════════
        --  TURNOS / CORTE DE CAJA
        -- ══════════════════════════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS Turno (
            id_turno            INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_apertura      TEXT NOT NULL,
            fecha_cierre        TEXT,
            fondo_inicial       REAL NOT NULL DEFAULT 0,
            total_ventas        REAL,
            total_movimientos   REAL,
            efectivo_esperado   REAL,
            efectivo_contado    REAL,
            diferencia          REAL,
            estado              TEXT NOT NULL DEFAULT 'abierto'
                                    CHECK(estado IN ('abierto', 'cerrado')),
            id_usuario_apertura INTEGER NOT NULL,
            id_usuario_cierre   INTEGER,
            notas               TEXT,
            FOREIGN KEY (id_usuario_apertura) REFERENCES Usuarios(id_usuario),
            FOREIGN KEY (id_usuario_cierre)   REFERENCES Usuarios(id_usuario)
        );

        -- ══════════════════════════════════════════════════════════════
        --  MOVIMIENTOS DE CAJA
        -- ══════════════════════════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS MovimientoCaja (
            id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT,
            id_turno      INTEGER NOT NULL,
            tipo          TEXT NOT NULL CHECK(tipo IN ('entrada', 'salida')),
            concepto      TEXT NOT NULL,
            monto         REAL NOT NULL,
            fecha         TEXT NOT NULL,
            id_usuario    INTEGER NOT NULL,
            FOREIGN KEY (id_turno)   REFERENCES Turno(id_turno),
            FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario)
        );

        -- ══════════════════════════════════════════════════════════════
        --  VENTAS
        -- ══════════════════════════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS Venta (
            id_venta       INTEGER PRIMARY KEY AUTOINCREMENT,
            folio          TEXT NOT NULL UNIQUE,
            fecha          TEXT NOT NULL,
            importe        REAL NOT NULL,
            monto_recibido REAL NOT NULL DEFAULT 0,
            cambio         REAL NOT NULL DEFAULT 0,
            estado         TEXT NOT NULL DEFAULT 'completada'
                               CHECK(estado IN ('completada', 'cancelada')),
            motivo_cancel  TEXT,
            id_turno       INTEGER NOT NULL,
            id_usuario     INTEGER NOT NULL,
            id_cancela     INTEGER,
            FOREIGN KEY (id_turno)   REFERENCES Turno(id_turno),
            FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario),
            FOREIGN KEY (id_cancela) REFERENCES Usuarios(id_usuario)
        );

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
        --  COMPRAS
        -- ══════════════════════════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS Compra (
            id_compra    INTEGER PRIMARY KEY AUTOINCREMENT,
            numdoc       TEXT NOT NULL,
            tipodoc      TEXT NOT NULL,
            fecha        TEXT NOT NULL,
            importe      REAL NOT NULL,
            id_proveedor INTEGER NOT NULL,
            id_usuario   INTEGER NOT NULL,
            FOREIGN KEY (id_proveedor) REFERENCES Proveedor(id_proveedor),
            FOREIGN KEY (id_usuario)   REFERENCES Usuarios(id_usuario)
        );

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
        --  MOVIMIENTOS DE INVENTARIO
        -- ══════════════════════════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS MovimientoInventario (
            id_movimiento       INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo              TEXT NOT NULL,
            tipo                TEXT NOT NULL CHECK(tipo IN (
                                    'entrada_compra',
                                    'entrada_produccion',
                                    'salida_produccion',
                                    'salida_venta',
                                    'ajuste_manual',
                                    'merma'
                                )),
            cantidad            REAL NOT NULL,
            existencia_anterior REAL NOT NULL,
            existencia_nueva    REAL NOT NULL,
            referencia          TEXT,
            fecha               TEXT NOT NULL,
            id_usuario          INTEGER NOT NULL,
            FOREIGN KEY (codigo)     REFERENCES Articulo(codigo),
            FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario)
        );
    """)

    # ── Datos iniciales ───────────────────────────────────────────────────────

    cursor.executemany(
        "INSERT OR IGNORE INTO Categoria (id_categoria, nombre) VALUES (?,?)", [
        (1, 'Tortillas y Derivados'),
        (2, 'Insumos de producción'),
        (3, 'Otros'),
    ])

    cursor.executemany(
        "INSERT OR IGNORE INTO Proveedor (id_proveedor, nombre, telefono, representante) VALUES (?,?,?,?)", [
        (1, 'Proveedor Maseca', '9610000000', 'Contacto General'),
    ])

    cursor.executemany(
        "INSERT OR IGNORE INTO Usuarios (id_usuario, nombre, rol, telefono, contrasena) VALUES (?,?,?,?,?)", [
        (1, 'Administrador','administrador', '9614426162', 'kaleb')
    ])

    # Tortilla — producto de venta (kg)
    cursor.execute("""
        INSERT OR IGNORE INTO Articulo
            (codigo, nombre, precio, costo, existencia, reorden,
             es_insumo, id_categoria, id_proveedor)
        VALUES ('TORTILLA001', 'Tortilla', 23.0, 0.0, 0.0, 0.0, 0, 1, NULL)
    """)

    # Harina Maseca — insumo, existencia en bultos
    cursor.execute("""
        INSERT OR IGNORE INTO Articulo
            (codigo, nombre, precio, costo, existencia, reorden,
             es_insumo, id_categoria, id_proveedor)
        VALUES ('HARINA001', 'Harina Maseca (bulto 20 kg)', 0.0, 0.0, 0.0, 2.0, 1, 2, 1)
    """)

    # Receta base: 1 bulto harina → 40 kg tortilla
    cursor.execute("""
        INSERT OR IGNORE INTO RecetaProduccion
            (id_receta, codigo_producto, codigo_insumo,
             cantidad_insumo, cantidad_producto, unidad_insumo, activa)
        VALUES (1, 'TORTILLA001', 'HARINA001', 1.0, 40.0, 'bulto', 1)
    """)

    # Configuración inicial
    configuraciones = [
        ('nombre_negocio',        'Tortillería Carmelita', 'Nombre del negocio'),
        ('direccion',             '',                       'Dirección del local'),
        ('telefono_negocio',      '',                       'Teléfono del negocio'),
        ('rfc',                   '',                       'RFC (opcional)'),
        ('precio_tortilla',       '23.0',                  'Precio por kg de tortilla'),
        ('unidad_venta',          'kg',                    'Unidad de medida para venta'),
        ('punto_reorden_default', '10.0',                  'Stock mínimo antes de alertar'),
        # ── Producción ────────────────────────────────────────────────
        ('kg_por_bulto_harina',   '20',                    'Peso en kg de un bulto de harina'),
        ('tortilla_por_bulto',    '40',                    'Kg de tortilla que produce 1 bulto de harina'),
        # ── Caja ──────────────────────────────────────────────────────
        ('fondo_apertura_default','200.0',                 'Fondo con que abre la caja normalmente'),
        ('impresora_ticket',      '',                       'Puerto/nombre de la impresora'),
        ('copias_ticket',         '1',                      'Copias por ticket de venta'),
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
    print("Tablas:")
    print("  • Categoria, Proveedor, Usuarios, Configuracion")
    print("  • Articulo  (TORTILLA001 + HARINA001)")
    print("  • RecetaProduccion  ← nueva  (1 bulto → 40 kg)")
    print("  • Turno, MovimientoCaja")
    print("  • Venta, DetalleVenta")
    print("  • Compra, DetalleCompra")
    print("  • MovimientoInventario  (+ salida_produccion)")


if __name__ == "__main__":
    crear_base_de_datos()