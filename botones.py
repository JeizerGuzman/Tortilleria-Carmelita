"""
Módulo de estilos y paleta de colores — Tortillería Carmelita.
Paleta: Verde campo × Amarillo maíz × Blanco limpio.
"""
import tkinter as tk
from tkinter import ttk

# ── Paleta de colores ─────────────────────────────────────────────────────────
PALETA_COLORES = {
    # ── Verdes ────────────────────────────────────────────────────────────────
    'VERDE_OSCURO':     '#1B5E20',   # Verde profundo — cabecera, títulos
    'VERDE_MEDIO':      '#2E7D32',   # Verde medio — menú principal
    'VERDE_CLARO':      '#4CAF50',   # Verde brillante — acentos / hover
    'VERDE_SUAVE':      '#A5D6A7',   # Verde muy claro — fondos secundarios
    'VERDE_MENTA':      '#C8E6C9',   # Verde menta — barra secundaria

    # ── Amarillos / Maíz ──────────────────────────────────────────────────────
    'AMARILLO_MAIZ':    '#F9A825',   # Amarillo maíz maduro — highlight
    'AMARILLO_CLARO':   '#FFF176',   # Amarillo suave — fondos de tarjetas
    'AMARILLO_DORADO':  '#F57F17',   # Dorado intenso — acentos fuertes
    'AMARILLO_PALIDO':  '#FFFDE7',   # Casi blanco amarillento — fondo general

    # ── Blancos / Neutros ─────────────────────────────────────────────────────
    'BLANCO':           '#FFFFFF',   # Blanco puro — tablas, cards
    'BLANCO_CALIDO':    '#FAFAFA',   # Blanco cálido — fondos alternos
    'GRIS_SUAVE':       '#757575',   # Gris medio — textos secundarios
    'GRIS_CLARO':       '#E8F5E9',   # Gris verdoso — separadores

    # ── Funcionales del sistema ───────────────────────────────────────────────
    'ROJO':             '#C62828',   # Eliminar / Cancelar — rojo oscuro
    'ROJO_SUAVE':       '#EF9A9A',   # Fondo de filas canceladas
    'AZUL':             '#1565C0',   # Info / secundario
    'TEXTO_OSCURO':     '#1B2F1B',   # Texto principal — verde muy oscuro
    'FONDO_PRINCIPAL':  '#FFFDE7',   # Amarillo muy pálido — fondo base
}

# ── Botones disponibles ───────────────────────────────────────────────────────
COLORES_BOTONES = [
    # Principales de la paleta
    ('VerdOscuro',  'VERDE_OSCURO'),
    ('VerdMedio',   'VERDE_MEDIO'),
    ('VerdClaro',   'VERDE_CLARO'),
    ('Maiz',        'AMARILLO_MAIZ'),
    ('Dorado',      'AMARILLO_DORADO'),

    # Funcionales
    ('Cafe',        'VERDE_OSCURO'),    # alias para compatibilidad con código existente
    ('Indigo',      'VERDE_MEDIO'),     # alias — botones de navegación
    ('Cian',        'VERDE_CLARO'),     # alias — cambiar usuario
    ('Advertencia', 'AMARILLO_MAIZ'),   # advertencias
    ('Naranja',     'AMARILLO_DORADO'), # cobrar sin imprimir
    ('Turquesa',    'VERDE_OSCURO'),    # cobrar e imprimir
    ('Azul Oscuro', 'VERDE_OSCURO'),
    ('Verde Oscuro','VERDE_OSCURO'),
    ('Azul',        'AZUL'),
    ('Gris',        'GRIS_SUAVE'),
    ('Exito',       'VERDE_MEDIO'),
    ('Peligro',     'ROJO'),
    ('Verde',       'VERDE_CLARO'),
    ('Dorad',       'AMARILLO_DORADO'),
    ('Morado',      'VERDE_OSCURO'),
    ('Rosa',        'AMARILLO_MAIZ'),
]

# ── Configuración global de estilos ──────────────────────────────────────────
def configurar_estilos(raiz):
    estilo = ttk.Style(raiz)
    estilo.theme_use('clam')

    fuente_btn  = ('Tahoma', 10, 'bold')
    padding_btn = (10, 6)
    radio       = 5
    fondo_base  = PALETA_COLORES['FONDO_PRINCIPAL']

    for nombre, clave in COLORES_BOTONES:
        style_name = f"{nombre}.TButton"
        base_color = PALETA_COLORES[clave]

        # Outline: fondo amarillo pálido, texto y borde del color
        estilo.configure(
            style_name,
            font=fuente_btn,
            padding=padding_btn,
            background=fondo_base,
            foreground=base_color,
            bordercolor=base_color,
            relief='solid',
            borderwidth=1,
            borderradius=radio,
        )
        # Hover: relleno del color, texto blanco
        estilo.map(
            style_name,
            background=[('active', base_color)],
            foreground=[('active', '#FFFFFF')],
            relief=[('pressed', 'flat')]
        )

    # ── Estilo especial para Dorado (hover texto oscuro por legibilidad) ──────
    estilo.map(
        "Maiz.TButton",
        background=[('active', PALETA_COLORES['AMARILLO_MAIZ'])],
        foreground=[('active', PALETA_COLORES['TEXTO_OSCURO'])],
    )
    estilo.map(
        "Dorado.TButton",
        background=[('active', PALETA_COLORES['AMARILLO_DORADO'])],
        foreground=[('active', '#FFFFFF')],
    )

# ── Colores de UI no-botones (cabeceras, barras, fondo) ──────────────────────
# Importa este dict en menu.py para mantener consistencia visual

UI = {
    # Cabecera superior y barra inferior
    'cabecera_bg':      '#1B5E20',   # verde oscuro profundo
    'cabecera_fg':      '#F9A825',   # amarillo maíz — título del negocio
    'cabecera_fg2':     '#FFFFFF',   # blanco — "Atiende: usuario"

    # Barra de menú principal
    'menu_bg':          '#2E7D32',   # verde medio
    'menu_btn_style':   'Maiz.TButton',  # botones amarillo maíz sobre verde

    # Barra secundaria (sub-módulos)
    'secundario_bg':    '#C8E6C9',   # verde menta suave
    'secundario_btn':   'VerdOscuro.TButton',

    # Fondo general
    'fondo':            '#FFFDE7',   # amarillo muy pálido

    # Barra de fecha/hora (inferior)
    'horario_bg':       '#1B5E20',   # mismo que cabecera
    'horario_fg_fecha': '#F9A825',   # amarillo maíz
    'horario_fg_hora':  '#FFFFFF',   # blanco
}

# ── Colores para tablas Treeview ──────────────────────────────────────────────
# Úsalos en cualquier módulo que configure ttk.Style para Treeview

TREE = {
    'background':       '#FFFFFF',
    'fieldbackground':  '#FFFFFF',
    'foreground':       '#1B5E20',   # verde oscuro
    'heading_bg':       '#2E7D32',   # verde medio
    'heading_fg':       '#F9A825',   # amarillo maíz
    'selected_bg':      '#4CAF50',   # verde claro
    'selected_fg':      '#FFFFFF',
    'tag_alerta_fg':    '#C62828',   # rojo
    'tag_alerta_bg':    '#FFEBEE',   # rojo muy pálido
    'tag_ok_fg':        '#1B5E20',
    'tag_cancel_bg':    '#FFEBEE',
    'tag_cancel_fg':    '#C62828',
}

# ── Helper para crear botones desde otros módulos ─────────────────────────────
def crear_boton(padre, texto, color_nombre, comando=None):
    nombre_estilo = next(
        (n for n, _ in COLORES_BOTONES if n.lower() == color_nombre.lower()),
        'VerdMedio'
    )
    return ttk.Button(
        padre,
        text=texto,
        style=f"{nombre_estilo}.TButton",
        command=comando
    )

# ── Demo ──────────────────────────────────────────────────────────────────────
def _demo_botones():
    raiz = tk.Tk()
    raiz.title('Demo — Tortillería Carmelita · Verde × Amarillo × Blanco')
    raiz.configure(bg=PALETA_COLORES['FONDO_PRINCIPAL'])
    raiz.geometry("750x620")
    configurar_estilos(raiz)

    # Cabecera
    cab = tk.Frame(raiz, bg=UI['cabecera_bg'], height=36)
    cab.pack(fill=tk.X)
    tk.Label(cab, text="🫓 Tortillería Carmelita",
             font=("Tahoma", 11, "bold"),
             bg=UI['cabecera_bg'],
             fg=UI['cabecera_fg']).pack(side=tk.LEFT, padx=12, pady=6)
    tk.Label(cab, text="Atiende: Administrador",
             font=("Tahoma", 11, "bold"),
             bg=UI['cabecera_bg'],
             fg=UI['cabecera_fg2']).pack(side=tk.RIGHT, padx=12, pady=6)

    # Menú principal
    menu = tk.Frame(raiz, bg=UI['menu_bg'])
    menu.pack(fill=tk.X)
    for txt in ["🛒 Ventas", "📦 Inventario", "🚚 Compras",
                "💰 Caja", "📊 Reportes", "⚙️ Config"]:
        ttk.Button(menu, text=txt,
                   style="Maiz.TButton",
                   width=12).pack(side=tk.LEFT, padx=4, pady=5)
    ttk.Button(menu, text="Salir",
               style="Peligro.TButton",
               width=10).pack(side=tk.RIGHT, padx=5, pady=5)
    ttk.Button(menu, text="Cambiar Usuario",
               style="Dorado.TButton",
               width=15).pack(side=tk.RIGHT, padx=5, pady=5)

    # Barra secundaria
    sub = tk.Frame(raiz, bg=UI['secundario_bg'])
    sub.pack(fill=tk.X)
    for txt in ["Ver existencias", "Movimientos", "Producción", "Artículos", "Categorías"]:
        ttk.Button(sub, text=txt,
                   style="VerdOscuro.TButton",
                   width=16).pack(side=tk.LEFT, padx=4, pady=4)

    # Fondo con botones de demo
    cont = tk.Frame(raiz, bg=PALETA_COLORES['FONDO_PRINCIPAL'], padx=20, pady=10)
    cont.pack(fill=tk.BOTH, expand=True)

    tk.Label(cont,
             text="Paleta completa — pasa el cursor para ver hover",
             font=("Tahoma", 10, "bold"),
             bg=PALETA_COLORES['FONDO_PRINCIPAL'],
             fg=PALETA_COLORES['VERDE_OSCURO']).pack(pady=(0, 10))

    frame_btns = tk.Frame(cont, bg=PALETA_COLORES['FONDO_PRINCIPAL'])
    frame_btns.pack()

    unicos = list(dict.fromkeys(COLORES_BOTONES))  # sin duplicados visuales
    col1 = tk.Frame(frame_btns, bg=PALETA_COLORES['FONDO_PRINCIPAL'])
    col2 = tk.Frame(frame_btns, bg=PALETA_COLORES['FONDO_PRINCIPAL'])
    col1.pack(side=tk.LEFT, padx=20)
    col2.pack(side=tk.LEFT, padx=20)

    for i, (nombre, _) in enumerate(unicos):
        col = col1 if i % 2 == 0 else col2
        ttk.Button(col, text=nombre,
                   style=f"{nombre}.TButton",
                   width=18).pack(fill=tk.X, pady=4)

    # Barra inferior
    horario = tk.Frame(raiz, bg=UI['horario_bg'], height=32)
    horario.pack(side=tk.BOTTOM, fill=tk.X)
    tk.Label(horario, text="lunes 18 de mayo de 2026",
             font=("Tahoma", 11),
             bg=UI['horario_bg'],
             fg=UI['horario_fg_fecha']).pack(side=tk.LEFT, padx=10, pady=4)
    tk.Label(horario, text="10:30:00 AM",
             font=("Tahoma", 11),
             bg=UI['horario_bg'],
             fg=UI['horario_fg_hora']).pack(side=tk.RIGHT, padx=10, pady=4)

    raiz.mainloop()


if __name__ == '__main__':
    _demo_botones()