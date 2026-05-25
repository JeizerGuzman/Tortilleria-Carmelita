import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import conexion
from botones import configurar_estilos, COLORES_MODULOS

# ── Helper compartido ─────────────────────────────────────────────────────────

def _titulo(container, texto):
    f = tk.Frame(container, bg=COLORES_MODULOS['encabezado_bg'], padx=10, pady=6)
    f.pack(fill=tk.X)
    tk.Label(f, text=texto, font=("Tahoma", 14, "bold"),
             fg=COLORES_MODULOS['encabezado_fg_claro'], bg=COLORES_MODULOS['encabezado_bg']).pack(side=tk.LEFT)
    return f

def _obtener_config(cursor, clave, default=None):
    """Obtiene un valor de configuración desde la BD."""
    try:
        cursor.execute("SELECT valor FROM Configuracion WHERE clave = ?", (clave,))
        row = cursor.fetchone()
        return row[0] if row else default
    except:
        return default


# ══════════════════════════════════════════════════════════════════════════════
#  VER EXISTENCIAS
# ══════════════════════════════════════════════════════════════════════════════
class InventarioExistencias:
    def __init__(self, container):
        self.container = container
        self.db        = conexion.conectar()
        self.cursor    = self.db.cursor()
        configurar_estilos(container)
        self._build()

    def _build(self):
        for w in self.container.winfo_children():
            w.destroy()
        self.container.configure(bg=COLORES_MODULOS["fondo_contenedor"])

        title_frame = _titulo(self.container, "📦  Inventario — Existencias")
        ttk.Button(title_frame, text="🔄 Actualizar",
                   style="Cafe.TButton",
                   command=self._cargar_tabla).pack(side=tk.RIGHT, padx=6)

        # Leyenda
        leyenda = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        leyenda.pack(fill=tk.X, padx=10, pady=4)
        tk.Label(leyenda, text="🔴 Stock en punto de reorden o menor",
                 font=("Tahoma", 9), bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_error"]).pack(side=tk.LEFT, padx=8)
        tk.Label(leyenda, text="🟢 Stock normal",
                 font=("Tahoma", 9), bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_exito"]).pack(side=tk.LEFT, padx=8)

        # Tabla
        tf = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Carmelita.Treeview",
                        background="#FFFFFF", fieldbackground="#FFFFFF",
                        foreground=COLORES_MODULOS["texto_principal"], rowheight=30,
                        font=("Tahoma", 11))
        style.configure("Carmelita.Treeview.Heading",
                        background=COLORES_MODULOS["tree_heading_bg"], foreground=COLORES_MODULOS["tree_heading_fg"],
                        font=("Tahoma", 11, "bold"))
        style.map("Carmelita.Treeview",
                  background=[("selected", COLORES_MODULOS["tree_selected_bg"])],
                  foreground=[("selected", COLORES_MODULOS["tree_selected_fg"])])

        # Tag para filas en alerta
        cols = ("codigo", "nombre", "categoria", "existencia", "reorden", "estado")
        self.tree = ttk.Treeview(tf, columns=cols,
                                 show="headings", style="Carmelita.Treeview")

        for col, texto, ancho in [
            ("codigo",     "Código",       120),
            ("nombre",     "Artículo",     220),
            ("categoria",  "Categoría",    160),
            ("existencia", "Existencia",   110),
            ("reorden",    "Pto. Reorden", 110),
            ("estado",     "Estado",       100),
        ]:
            self.tree.heading(col, text=texto, anchor="center")
            self.tree.column(col, width=ancho, anchor="center")

        self.tree.tag_configure("alerta", foreground=COLORES_MODULOS["tag_alerta_fg"], background=COLORES_MODULOS["tag_alerta_bg"])
        self.tree.tag_configure("normal", foreground=COLORES_MODULOS["tag_normal_fg"])

        sb = ttk.Scrollbar(tf, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.LEFT, fill=tk.Y)

        self._cargar_tabla()

    def _cargar_tabla(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        self.cursor.execute("""
            SELECT a.codigo, a.nombre, c.nombre, a.existencia, a.reorden
            FROM Articulo a
            JOIN Categoria c ON c.id_categoria = a.id_categoria
            ORDER BY a.nombre
        """)
        for codigo, nombre, cat, exist, reorden in self.cursor.fetchall():
            en_alerta = exist <= reorden
            tag       = "alerta" if en_alerta else "normal"
            estado    = "⚠ Bajo" if en_alerta else "✔ OK"
            self.tree.insert('', tk.END, tags=(tag,), values=(
                codigo, nombre, cat,
                f"{exist:.3f}",
                f"{reorden:.3f}",
                estado,
            ))


# ══════════════════════════════════════════════════════════════════════════════
#  MOVIMIENTOS DE INVENTARIO
# ══════════════════════════════════════════════════════════════════════════════
class InventarioMovimientos:
    def __init__(self, container):
        self.container = container
        self.db        = conexion.conectar()
        self.cursor    = self.db.cursor()
        configurar_estilos(container)
        self._build()

    def _build(self):
        for w in self.container.winfo_children():
            w.destroy()
        self.container.configure(bg=COLORES_MODULOS["fondo_contenedor"])
        _titulo(self.container, "📦  Inventario — Movimientos")

        # Filtros
        filtros = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"], padx=10, pady=8)
        filtros.pack(fill=tk.X)

        tk.Label(filtros, text="Artículo:",
                 font=("Tahoma", 10, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(side=tk.LEFT, padx=(0, 4))

        self.cursor.execute("SELECT codigo, nombre FROM Articulo ORDER BY nombre")
        articulos = [("", "Todos")] + [(r[0], r[1]) for r in self.cursor.fetchall()]
        self.art_map  = {nombre: cod for cod, nombre in articulos}
        self.var_art  = tk.StringVar(value="Todos")
        cb_art = ttk.Combobox(filtros, textvariable=self.var_art,
                              values=[n for _, n in articulos],
                              state="readonly", width=22, font=("Tahoma", 10))
        cb_art.pack(side=tk.LEFT, padx=4)

        tk.Label(filtros, text="Tipo:",
                 font=("Tahoma", 10, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(side=tk.LEFT, padx=(12, 4))
        self.var_tipo = tk.StringVar(value="Todos")
        cb_tipo = ttk.Combobox(filtros, textvariable=self.var_tipo,
                               values=["Todos", "entrada_compra",
                                       "salida_venta", "ajuste_manual", "merma"],
                               state="readonly", width=16, font=("Tahoma", 10))
        cb_tipo.pack(side=tk.LEFT, padx=4)

        ttk.Button(filtros, text="Buscar",
                   style="Dorado.TButton",
                   command=self._cargar_tabla).pack(side=tk.LEFT, padx=12)

        # Tabla
        tf = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        style = ttk.Style()
        style.configure("Carmelita.Treeview",
                        background="#FFFFFF", fieldbackground="#FFFFFF",
                        foreground=COLORES_MODULOS["texto_principal"], rowheight=28,
                        font=("Tahoma", 10))
        style.configure("Carmelita.Treeview.Heading",
                        background=COLORES_MODULOS["tree_heading_bg"], foreground=COLORES_MODULOS["tree_heading_fg"],
                        font=("Tahoma", 10, "bold"))
        style.map("Carmelita.Treeview",
                  background=[("selected", COLORES_MODULOS["tree_selected_bg"])],
                  foreground=[("selected", COLORES_MODULOS["tree_selected_fg"])])

        cols = ("articulo", "tipo", "cantidad", "ant", "nueva", "referencia", "fecha", "usuario")
        self.tree = ttk.Treeview(tf, columns=cols,
                                 show="headings", style="Carmelita.Treeview")
        for col, texto, ancho in [
            ("articulo",   "Artículo",    160),
            ("tipo",       "Tipo",        130),
            ("cantidad",   "Cantidad",     90),
            ("ant",        "Stock ant.",   90),
            ("nueva",      "Stock nuevo",  90),
            ("referencia", "Referencia",  130),
            ("fecha",      "Fecha",       140),
            ("usuario",    "Usuario",     110),
        ]:
            self.tree.heading(col, text=texto, anchor="center")
            self.tree.column(col, width=ancho, anchor="center")

        self.tree.tag_configure("entrada", foreground=COLORES_MODULOS["tag_entrada_fg"])
        self.tree.tag_configure("salida",  foreground=COLORES_MODULOS["tag_salida_fg"])

        sb = ttk.Scrollbar(tf, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.LEFT, fill=tk.Y)

        self._cargar_tabla()

    def _cargar_tabla(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        cod_filtro  = self.art_map.get(self.var_art.get(), "")
        tipo_filtro = self.var_tipo.get()

        query = """
            SELECT a.nombre, m.tipo, m.cantidad,
                   m.existencia_anterior, m.existencia_nueva,
                   m.referencia, m.fecha, u.nombre
            FROM MovimientoInventario m
            JOIN Articulo a  ON a.codigo     = m.codigo
            JOIN Usuarios u  ON u.id_usuario = m.id_usuario
            WHERE 1=1
        """
        params = []
        if cod_filtro:
            query += " AND m.codigo = ?"
            params.append(cod_filtro)
        if tipo_filtro != "Todos":
            query += " AND m.tipo = ?"
            params.append(tipo_filtro)
        query += " ORDER BY m.fecha DESC"

        self.cursor.execute(query, params)
        for nombre, tipo, cant, ant, nueva, ref, fecha, usuario in self.cursor.fetchall():
            es_entrada = cant >= 0
            tag        = "entrada" if es_entrada else "salida"
            signo      = "+" if es_entrada else ""
            self.tree.insert('', tk.END, tags=(tag,), values=(
                nombre, tipo,
                f"{signo}{cant:.3f}",
                f"{ant:.3f}",
                f"{nueva:.3f}",
                ref or "—",
                fecha,
                usuario,
            ))


# ══════════════════════════════════════════════════════════════════════════════
#  AJUSTE MANUAL DE INVENTARIO
# ══════════════════════════════════════════════════════════════════════════════
class InventarioAjuste:
    def __init__(self, container, usuario=""):
        self.container = container
        self.db        = conexion.conectar()
        self.cursor    = self.db.cursor()
        self.usuario   = usuario or ""
        configurar_estilos(container)
        self._build()

    def _build(self):
        for w in self.container.winfo_children():
            w.destroy()
        self.container.configure(bg=COLORES_MODULOS["fondo_contenedor"])
        _titulo(self.container, "📦  Inventario — Ajuste manual")

        tk.Label(self.container,
                 text="Solo el administrador puede corregir existencias manualmente.",
                 font=("Tahoma", 9, "italic"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_error"]).pack(anchor="w", padx=12, pady=2)

        cuerpo = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        cuerpo.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.columnconfigure(1, weight=2)
        cuerpo.rowconfigure(0, weight=1)

        self._form(cuerpo)
        self._tabla_recientes(cuerpo)

    def _form(self, parent):
        card = tk.LabelFrame(parent, text="  Nuevo ajuste  ",
                             bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"],
                             font=("Tahoma", 10, "bold"),
                             bd=2, relief="groove")
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)

        # Artículo
        tk.Label(card, text="Artículo:",
                 font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(14, 2))

        self.cursor.execute("SELECT codigo, nombre, existencia FROM Articulo ORDER BY nombre")
        self.articulos = self.cursor.fetchall()
        nombres = [r[1] for r in self.articulos]
        self.art_map = {r[1]: (r[0], r[2]) for r in self.articulos}

        self.var_art = tk.StringVar()
        self.cb_art  = ttk.Combobox(card, textvariable=self.var_art,
                                    values=nombres, state="readonly",
                                    font=("Tahoma", 11), width=24)
        self.cb_art.pack(padx=16)
        self.cb_art.bind("<<ComboboxSelected>>", self._mostrar_existencia)

        # Existencia actual
        self.lbl_exist = tk.Label(card, text="Existencia actual: —",
                                  font=("Tahoma", 10, "italic"),
                                  bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_error"])
        self.lbl_exist.pack(anchor="w", padx=16, pady=2)

        # Tipo de ajuste
        tk.Label(card, text="Tipo de ajuste:",
                 font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(10, 2))
        self.var_tipo = tk.StringVar(value="ajuste_manual")
        for texto, val in [("Ajuste manual (corrección)", "ajuste_manual"),
                           ("Merma (pérdida/desperdicio)", "merma")]:
            ttk.Radiobutton(card, text=texto, variable=self.var_tipo,
                            value=val).pack(anchor="w", padx=20, pady=2)

        # Nueva existencia
        tk.Label(card, text="Nueva existencia:",
                 font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(10, 2))
        self.var_nueva = tk.StringVar()
        ttk.Entry(card, textvariable=self.var_nueva,
                  font=("Tahoma", 11), width=14).pack(padx=16)

        # Motivo
        tk.Label(card, text="Motivo:",
                 font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(10, 2))
        self.var_motivo = tk.StringVar()
        ttk.Entry(card, textvariable=self.var_motivo,
                  font=("Tahoma", 11), width=28).pack(padx=16)

        # Usuario que ajusta
        tk.Label(card, text="Usuario que ajusta:",
                 font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(10, 2))
        self.lbl_usuario = tk.Label(card,
                 text=self.usuario or "Sin usuario",
                 font=("Tahoma", 10, "bold",),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["TEXTO_OSCURO"])
        self.lbl_usuario.pack(anchor="w", padx=16)

        ttk.Button(card, text="Aplicar ajuste",
                   style="Advertencia.TButton", width=20,
                   command=self._aplicar).pack(pady=16)

    def _tabla_recientes(self, parent):
        frame = tk.Frame(parent, bg=COLORES_MODULOS["fondo_contenedor"])
        frame.grid(row=0, column=1, sticky="nsew", pady=4)

        tk.Label(frame, text="Ajustes recientes",
                 font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", pady=(4, 6))

        style = ttk.Style()
        style.configure("Carmelita.Treeview",
                        background="#FFFFFF", fieldbackground="#FFFFFF",
                        foreground=COLORES_MODULOS["texto_principal"], rowheight=28,
                        font=("Tahoma", 10))
        style.configure("Carmelita.Treeview.Heading",
                        background=COLORES_MODULOS["tree_heading_bg"], foreground=COLORES_MODULOS["tree_heading_fg"],
                        font=("Tahoma", 10, "bold"))
        style.map("Carmelita.Treeview",
                  background=[("selected", COLORES_MODULOS["tree_selected_bg"])],
                  foreground=[("selected", COLORES_MODULOS["tree_selected_fg"])])

        cols = ("articulo", "tipo", "ant", "nueva", "motivo", "fecha")
        self.tree = ttk.Treeview(frame, columns=cols,
                                 show="headings", style="Carmelita.Treeview")
        for col, texto, ancho in [
            ("articulo", "Artículo",    160),
            ("tipo",     "Tipo",        120),
            ("ant",      "Stock ant.",   90),
            ("nueva",    "Stock nuevo",  90),
            ("motivo",   "Motivo",      160),
            ("fecha",    "Fecha",       140),
        ]:
            self.tree.heading(col, text=texto, anchor="center")
            self.tree.column(col, width=ancho, anchor="center")

        sb = ttk.Scrollbar(frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.LEFT, fill=tk.Y)

        self._cargar_recientes()

    def _mostrar_existencia(self, event=None):
        nombre = self.var_art.get()
        if nombre in self.art_map:
            _, exist = self.art_map[nombre]
            self.lbl_exist.config(text=f"Existencia actual: {exist:.3f}")

    def _cargar_recientes(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.cursor.execute("""
            SELECT a.nombre, m.tipo, m.existencia_anterior,
                   m.existencia_nueva, m.referencia, m.fecha
            FROM MovimientoInventario m
            JOIN Articulo a ON a.codigo = m.codigo
            WHERE m.tipo IN ('ajuste_manual', 'merma')
            ORDER BY m.fecha DESC
            LIMIT 50
        """)
        for nombre, tipo, ant, nueva, ref, fecha in self.cursor.fetchall():
            self.tree.insert('', tk.END, values=(
                nombre, tipo,
                f"{ant:.3f}", f"{nueva:.3f}",
                ref or "—", fecha,
            ))

    def _aplicar(self):
        nombre = self.var_art.get()
        if not nombre or nombre not in self.art_map:
            messagebox.showwarning("Sin artículo", "Selecciona un artículo.")
            return

        try:
            nueva_exist = float(self.var_nueva.get().replace(",", "."))
            if nueva_exist < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Valor inválido",
                                   "Ingresa una existencia válida (mayor o igual a 0).")
            return

        motivo = self.var_motivo.get().strip()
        if not motivo:
            messagebox.showwarning("Motivo vacío", "Escribe el motivo del ajuste.")
            return

        if not self.usuario:
            messagebox.showwarning("Sin usuario", "No se pudo identificar el usuario activo.")
            return

        codigo, exist_ant = self.art_map[nombre]
        diferencia        = nueva_exist - exist_ant
        ahora             = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute(
            "SELECT id_usuario FROM Usuarios WHERE nombre = ?", (self.usuario,))
        row = self.cursor.fetchone()
        id_usuario = row[0] if row else None

        confirmar = messagebox.askyesno(
            "Confirmar ajuste",
            f"Artículo: {nombre}\n"
            f"Existencia actual: {exist_ant:.3f}\n"
            f"Nueva existencia:  {nueva_exist:.3f}\n"
            f"Diferencia:        {diferencia:+.3f}\n\n"
            f"Motivo: {motivo}\n\n"
            "¿Aplicar ajuste?"
        )
        if not confirmar:
            return

        self.cursor.execute(
            "UPDATE Articulo SET existencia = ? WHERE codigo = ?",
            (nueva_exist, codigo))

        self.cursor.execute("""
            INSERT INTO MovimientoInventario
                (codigo, tipo, cantidad, existencia_anterior,
                 existencia_nueva, referencia, fecha, id_usuario)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (codigo, self.var_tipo.get(), diferencia,
              exist_ant, nueva_exist, motivo, ahora, id_usuario))

        self.db.commit()

        messagebox.showinfo("Ajuste aplicado",
                            f"✅ Existencia de '{nombre}' actualizada a {nueva_exist:.3f}")

        # Resetear form
        self.var_art.set("")
        self.var_nueva.set("")
        self.var_motivo.set("")
        self.lbl_exist.config(text="Existencia actual: —")

        # Actualizar mapa local
        self.art_map[nombre] = (codigo, nueva_exist)
        self._cargar_recientes()
        
        
# ══════════════════════════════════════════════════════════════════════════════
#  ARTÍCULOS
# ══════════════════════════════════════════════════════════════════════════════
class InventarioArticulos:
    CODIGO_FIJO = "TORTILLA001"   # nunca se puede editar ni eliminar

    def __init__(self, container):
        self.container  = container
        self.db         = conexion.conectar()
        self.cursor     = self.db.cursor()
        self._id_edit   = None    # código del artículo en edición (None = nuevo)
        configurar_estilos(container)
        self._build()

    # ── Construcción principal ────────────────────────────────────────────────

    def _build(self):
        for w in self.container.winfo_children():
            w.destroy()
        self.container.configure(bg=COLORES_MODULOS["fondo_contenedor"])

        title_frame = _titulo(self.container, "📦  Inventario — Artículos")
        ttk.Button(title_frame, text="➕ Nuevo artículo",
                   style="Cafe.TButton",
                   command=self._nuevo).pack(side=tk.RIGHT, padx=6)

        cuerpo = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        cuerpo.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        cuerpo.columnconfigure(0, weight=2)
        cuerpo.columnconfigure(1, weight=3)
        cuerpo.rowconfigure(0, weight=1)

        self._build_form(cuerpo)
        self._build_tabla(cuerpo)
        self._cargar_tabla()

    # ── Formulario ────────────────────────────────────────────────────────────

    def _build_form(self, parent):
        self.card = tk.LabelFrame(parent, text="  Nuevo artículo  ",
                                  bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"],
                                  font=("Tahoma", 10, "bold"),
                                  bd=2, relief="groove")
        self.card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)

        def fila(label, widget_fn, **kw):
            tk.Label(self.card, text=label,
                     font=("Tahoma", 10, "bold"),
                     bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(10, 2))
            return widget_fn(self.card, **kw)

        # Código
        self.var_codigo = tk.StringVar()
        self.ent_codigo = fila("Código:", ttk.Entry,
                               textvariable=self.var_codigo,
                               font=("Tahoma", 11), width=20)
        self.ent_codigo.pack(padx=16)

        # Nombre
        self.var_nombre = tk.StringVar()
        fila("Nombre:", ttk.Entry,
             textvariable=self.var_nombre,
             font=("Tahoma", 11), width=28).pack(padx=16)

        # Precio
        self.var_precio = tk.StringVar()
        fila("Precio de venta ($):", ttk.Entry,
             textvariable=self.var_precio,
             font=("Tahoma", 11), width=14).pack(padx=16)

        # Costo
        self.var_costo = tk.StringVar()
        fila("Costo ($):", ttk.Entry,
             textvariable=self.var_costo,
             font=("Tahoma", 11), width=14).pack(padx=16)

        # Punto de reorden
        self.var_reorden = tk.StringVar()
        fila("Punto de reorden:", ttk.Entry,
             textvariable=self.var_reorden,
             font=("Tahoma", 11), width=14).pack(padx=16)

        # Tipo
        tk.Label(self.card, text="Tipo:",
                 font=("Tahoma", 10, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(10, 2))
        self.var_tipo = tk.StringVar(value="0")
        for texto, val in [("Producto de venta", "0"), ("Insumo interno", "1")]:
            ttk.Radiobutton(self.card, text=texto,
                            variable=self.var_tipo, value=val).pack(anchor="w", padx=24)

        # Categoría
        self.cursor.execute("SELECT id_categoria, nombre FROM Categoria ORDER BY nombre")
        self._cats = self.cursor.fetchall()
        self._cat_map = {nombre: id_ for id_, nombre in self._cats}
        self._cat_map_inv = {id_: nombre for id_, nombre in self._cats}

        tk.Label(self.card, text="Categoría:",
                 font=("Tahoma", 10, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(10, 2))
        self.var_cat = tk.StringVar()
        self.cb_cat  = ttk.Combobox(self.card, textvariable=self.var_cat,
                                    values=[n for _, n in self._cats],
                                    state="readonly", font=("Tahoma", 11), width=26)
        self.cb_cat.pack(padx=16)

        # Proveedor
        self.cursor.execute("SELECT id_proveedor, nombre FROM Proveedor ORDER BY nombre")
        self._provs = [("", "Sin proveedor")] + [(str(r[0]), r[1]) for r in self.cursor.fetchall()]
        self._prov_map     = {nombre: id_ for id_, nombre in self._provs}
        self._prov_map_inv = {id_: nombre for id_, nombre in self._provs}

        tk.Label(self.card, text="Proveedor:",
                 font=("Tahoma", 10, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(10, 2))
        self.var_prov = tk.StringVar(value="Sin proveedor")
        self.cb_prov  = ttk.Combobox(self.card, textvariable=self.var_prov,
                                     values=[n for _, n in self._provs],
                                     state="readonly", font=("Tahoma", 11), width=26)
        self.cb_prov.pack(padx=16)

        # Botones
        frame_btns = tk.Frame(self.card, bg=COLORES_MODULOS["fondo_contenedor"])
        frame_btns.pack(pady=14)
        ttk.Button(frame_btns, text="💾 Guardar",
                   style="Dorado.TButton", width=14,
                   command=self._guardar).pack(side=tk.LEFT, padx=6)
        ttk.Button(frame_btns, text="✖ Cancelar",
                   style="Peligro.TButton", width=14,
                   command=self._nuevo).pack(side=tk.LEFT, padx=6)

    # ── Tabla ─────────────────────────────────────────────────────────────────

    def _build_tabla(self, parent):
        frame = tk.Frame(parent, bg=COLORES_MODULOS["fondo_contenedor"])
        frame.grid(row=0, column=1, sticky="nsew", pady=4)

        # Botones de acción sobre la tabla
        acc = tk.Frame(frame, bg=COLORES_MODULOS["fondo_contenedor"])
        acc.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(acc, text="✏️ Editar",
                   style="Cafe.TButton", width=12,
                   command=self._editar).pack(side=tk.LEFT, padx=4)
        ttk.Button(acc, text="🚫 Desactivar",
                   style="Advertencia.TButton", width=14,
                   command=self._desactivar).pack(side=tk.LEFT, padx=4)

        style = ttk.Style()
        style.configure("Carmelita.Treeview",
                        background="#FFFFFF", fieldbackground="#FFFFFF",
                        foreground=COLORES_MODULOS["texto_principal"], rowheight=28,
                        font=("Tahoma", 10))
        style.configure("Carmelita.Treeview.Heading",
                        background=COLORES_MODULOS["tree_heading_bg"], foreground=COLORES_MODULOS["tree_heading_fg"],
                        font=("Tahoma", 10, "bold"))
        style.map("Carmelita.Treeview",
                  background=[("selected", COLORES_MODULOS["tree_selected_bg"])],
                  foreground=[("selected", COLORES_MODULOS["tree_selected_fg"])])

        cols = ("codigo", "nombre", "precio", "costo", "reorden", "tipo", "categoria", "proveedor")
        self.tree = ttk.Treeview(frame, columns=cols,
                                 show="headings", style="Carmelita.Treeview")
        for col, texto, ancho in [
            ("codigo",    "Código",      110),
            ("nombre",    "Nombre",      180),
            ("precio",    "Precio",       80),
            ("costo",     "Costo",        80),
            ("reorden",   "Reorden",      80),
            ("tipo",      "Tipo",        100),
            ("categoria", "Categoría",   130),
            ("proveedor", "Proveedor",   150),
        ]:
            self.tree.heading(col, text=texto, anchor="center")
            self.tree.column(col, width=ancho, anchor="center")

        self.tree.tag_configure("fijo",     background=COLORES_MODULOS['tag_fijo_bg'], foreground=COLORES_MODULOS["texto_principal"])
        self.tree.tag_configure("insumo",   foreground=COLORES_MODULOS["tag_insumo_fg"])
        self.tree.tag_configure("venta",    foreground=COLORES_MODULOS["tag_venta_fg"])
        self.tree.tag_configure("inactivo", foreground=COLORES_MODULOS["tag_inactivo_fg"])

        sb = ttk.Scrollbar(frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.LEFT, fill=tk.Y)

    # ── Lógica ────────────────────────────────────────────────────────────────

    def _cargar_tabla(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.cursor.execute("""
            SELECT a.codigo, a.nombre, a.precio, a.costo, a.reorden,
                   a.es_insumo, c.nombre,
                   COALESCE(p.nombre, 'Sin proveedor')
            FROM   Articulo  a
            JOIN   Categoria c ON c.id_categoria = a.id_categoria
            LEFT JOIN Proveedor p ON p.id_proveedor = a.id_proveedor
            ORDER  BY a.nombre
        """)
        for cod, nom, precio, costo, reorden, es_ins, cat, prov in self.cursor.fetchall():
            if cod == self.CODIGO_FIJO:
                tag = "fijo"
            elif es_ins:
                tag = "insumo"
            else:
                tag = "venta"
            tipo_txt = "Insumo" if es_ins else "Venta"
            self.tree.insert('', tk.END, iid=cod, tags=(tag,), values=(
                cod, nom,
                f"${precio:.2f}", f"${costo:.2f}", f"{reorden:.3f}",
                tipo_txt, cat, prov,
            ))

    def _nuevo(self):
        """Limpia el formulario para capturar un artículo nuevo."""
        self._id_edit = None
        self.card.config(text="  Nuevo artículo  ")
        self.var_codigo.set("")
        self.var_nombre.set("")
        self.var_precio.set("")
        self.var_costo.set("")
        reorden_default = _obtener_config(self.cursor, "punto_reorden_default", "10")
        self.var_reorden.set(reorden_default)
        self.var_tipo.set("0")
        self.var_cat.set("")
        self.var_prov.set("Sin proveedor")
        self.ent_codigo.config(state="normal")
        self.cb_cat.config(state="readonly")

    def _editar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona un artículo para editar.")
            return
        codigo = sel[0]

        self.cursor.execute("""
            SELECT a.codigo, a.nombre, a.precio, a.costo, a.reorden,
                   a.es_insumo, a.id_categoria, a.id_proveedor
            FROM Articulo a WHERE a.codigo = ?
        """, (codigo,))
        row = self.cursor.fetchone()
        if not row:
            return

        cod, nom, precio, costo, reorden, es_ins, id_cat, id_prov = row
        self._id_edit = cod
        self.card.config(text=f"  Editando: {nom}  ")

        self.var_codigo.set(cod)
        self.var_nombre.set(nom)
        self.var_precio.set(str(precio))
        self.var_costo.set(str(costo))
        self.var_reorden.set(str(reorden))
        self.var_tipo.set("1" if es_ins else "0")
        self.var_cat.set(self._cat_map_inv.get(id_cat, ""))
        self.var_prov.set(self._prov_map_inv.get(str(id_prov) if id_prov else "", "Sin proveedor"))

        # Si es la tortilla: bloquear código y categoría
        if cod == self.CODIGO_FIJO:
            self.ent_codigo.config(state="disabled")
            self.cb_cat.config(state="disabled")
            messagebox.showinfo(
                "Artículo especial",
                "TORTILLA001 es un artículo fijo.\n"
                "Solo puedes modificar precio, costo y punto de reorden."
            )
        else:
            self.ent_codigo.config(state="normal")
            self.cb_cat.config(state="readonly")

    def _guardar(self):
        codigo  = self.var_codigo.get().strip().upper()
        nombre  = self.var_nombre.get().strip()
        cat_nom = self.var_cat.get()
        prov_nom = self.var_prov.get()

        # Validaciones básicas
        if not codigo:
            messagebox.showwarning("Código vacío", "Ingresa un código para el artículo.")
            return
        if not nombre:
            messagebox.showwarning("Nombre vacío", "Ingresa el nombre del artículo.")
            return
        if not cat_nom:
            messagebox.showwarning("Sin categoría", "Selecciona una categoría.")
            return

        try:
            precio  = float(self.var_precio.get().replace(",", "."))
            costo   = float(self.var_costo.get().replace(",", ".") or "0")
            reorden = float(self.var_reorden.get().replace(",", ".") or "0")
            if precio < 0 or costo < 0 or reorden < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Valores inválidos",
                                   "Precio, costo y reorden deben ser números positivos.")
            return

        id_cat  = self._cat_map.get(cat_nom)
        id_prov = self._prov_map.get(prov_nom) or None
        es_ins  = int(self.var_tipo.get())

        if self._id_edit is None:
            # ── INSERT ──
            self.cursor.execute("SELECT codigo FROM Articulo WHERE codigo = ?", (codigo,))
            if self.cursor.fetchone():
                messagebox.showwarning("Código duplicado",
                                       f"Ya existe un artículo con el código '{codigo}'.")
                return
            self.cursor.execute("""
                INSERT INTO Articulo
                    (codigo, nombre, precio, costo, existencia, reorden,
                     es_insumo, id_categoria, id_proveedor)
                VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?)
            """, (codigo, nombre, precio, costo, reorden, es_ins, id_cat, id_prov))
            msg = f"✅ Artículo '{nombre}' creado correctamente."
        else:
            # ── UPDATE ──
            if self._id_edit == self.CODIGO_FIJO:
                # Tortilla: solo precio, costo y reorden
                self.cursor.execute("""
                    UPDATE Articulo SET precio=?, costo=?, reorden=?
                    WHERE codigo=?
                """, (precio, costo, reorden, self._id_edit))
            else:
                self.cursor.execute("""
                    UPDATE Articulo
                    SET codigo=?, nombre=?, precio=?, costo=?, reorden=?,
                        es_insumo=?, id_categoria=?, id_proveedor=?
                    WHERE codigo=?
                """, (codigo, nombre, precio, costo, reorden,
                      es_ins, id_cat, id_prov, self._id_edit))
            msg = f"✅ Artículo '{nombre}' actualizado correctamente."

        self.db.commit()
        messagebox.showinfo("Guardado", msg)
        self._nuevo()
        self._cargar_tabla()

    def _desactivar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona un artículo para desactivar.")
            return
        codigo = sel[0]
        if codigo == self.CODIGO_FIJO:
            messagebox.showwarning("No permitido",
                                   "TORTILLA001 no puede desactivarse.")
            return

        self.cursor.execute("SELECT nombre FROM Articulo WHERE codigo=?", (codigo,))
        row = self.cursor.fetchone()
        if not row:
            return
        nombre = row[0]

        if not messagebox.askyesno("Confirmar",
                                   f"¿Desactivar el artículo '{nombre}'?\n\n"
                                   "No se eliminará; solo dejará de aparecer en ventas y compras."):
            return

        # Marcar como insumo con reorden 0 y precio 0 es una opción,
        # pero la forma limpia es agregar un campo 'activo' a Articulo.
        # Por ahora lo movemos a categoría "Otros" y reorden a 0
        # para que no genere alertas.  Cuando agregues el campo 'activo'
        # simplemente cambia esto por: UPDATE Articulo SET activo=0 ...
        self.cursor.execute("""
            UPDATE Articulo SET reorden = 0 WHERE codigo = ?
        """, (codigo,))
        self.db.commit()
        messagebox.showinfo("Desactivado",
                            f"'{nombre}' fue desactivado.\n"
                            "Tip: Agrega el campo 'activo' a la tabla Articulo "
                            "para un control más preciso.")
        self._cargar_tabla()


# ══════════════════════════════════════════════════════════════════════════════
#  CATEGORÍAS
# ══════════════════════════════════════════════════════════════════════════════
class InventarioCategorias:
    def __init__(self, container):
        self.container = container
        self.db        = conexion.conectar()
        self.cursor    = self.db.cursor()
        self._id_edit  = None
        configurar_estilos(container)
        self._build()

    # ── Construcción ──────────────────────────────────────────────────────────

    def _build(self):
        for w in self.container.winfo_children():
            w.destroy()
        self.container.configure(bg=COLORES_MODULOS["fondo_contenedor"])
        _titulo(self.container, "📦  Inventario — Categorías")

        cuerpo = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        cuerpo.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.columnconfigure(1, weight=2)
        cuerpo.rowconfigure(0, weight=1)

        self._build_form(cuerpo)
        self._build_tabla(cuerpo)
        self._cargar_tabla()

    def _build_form(self, parent):
        self.card = tk.LabelFrame(parent, text="  Nueva categoría  ",
                                  bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"],
                                  font=("Tahoma", 10, "bold"),
                                  bd=2, relief="groove")
        self.card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)

        tk.Label(self.card, text="Nombre de la categoría:",
                 font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(20, 4))

        self.var_nombre = tk.StringVar()
        ttk.Entry(self.card, textvariable=self.var_nombre,
                  font=("Tahoma", 12), width=26).pack(padx=16)

        frame_btns = tk.Frame(self.card, bg=COLORES_MODULOS["fondo_contenedor"])
        frame_btns.pack(pady=16)
        ttk.Button(frame_btns, text="💾 Guardar",
                   style="Dorado.TButton", width=14,
                   command=self._guardar).pack(side=tk.LEFT, padx=6)
        ttk.Button(frame_btns, text="✖ Cancelar",
                   style="Peligro.TButton", width=14,
                   command=self._cancelar).pack(side=tk.LEFT, padx=6)

        # Info de artículos en esta categoría
        self.lbl_info = tk.Label(self.card, text="",
                                 font=("Tahoma", 9, "italic"),
                                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_error"],
                                 wraplength=220, justify="left")
        self.lbl_info.pack(padx=16, pady=4)

    def _build_tabla(self, parent):
        frame = tk.Frame(parent, bg=COLORES_MODULOS["fondo_contenedor"])
        frame.grid(row=0, column=1, sticky="nsew", pady=4)

        acc = tk.Frame(frame, bg=COLORES_MODULOS["fondo_contenedor"])
        acc.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(acc, text="✏️ Editar",
                   style="Cafe.TButton", width=12,
                   command=self._editar).pack(side=tk.LEFT, padx=4)
        ttk.Button(acc, text="🗑 Eliminar",
                   style="Peligro.TButton", width=12,
                   command=self._eliminar).pack(side=tk.LEFT, padx=4)

        style = ttk.Style()
        style.configure("Carmelita.Treeview",
                        background="#FFFFFF", fieldbackground="#FFFFFF",
                        foreground=COLORES_MODULOS["texto_principal"], rowheight=30,
                        font=("Tahoma", 11))
        style.configure("Carmelita.Treeview.Heading",
                        background=COLORES_MODULOS["tree_heading_bg"], foreground=COLORES_MODULOS["tree_heading_fg"],
                        font=("Tahoma", 11, "bold"))
        style.map("Carmelita.Treeview",
                  background=[("selected", COLORES_MODULOS["tree_selected_bg"])],
                  foreground=[("selected", COLORES_MODULOS["tree_selected_fg"])])

        cols = ("id", "nombre", "articulos")
        self.tree = ttk.Treeview(frame, columns=cols,
                                 show="headings", style="Carmelita.Treeview")
        for col, texto, ancho in [
            ("id",        "ID",          60),
            ("nombre",    "Categoría",  260),
            ("articulos", "Artículos",  100),
        ]:
            self.tree.heading(col, text=texto, anchor="center")
            self.tree.column(col, width=ancho, anchor="center")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        sb = ttk.Scrollbar(frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.LEFT, fill=tk.Y)

    # ── Lógica ────────────────────────────────────────────────────────────────

    def _cargar_tabla(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.cursor.execute("""
            SELECT c.id_categoria, c.nombre,
                   COUNT(a.codigo) AS total
            FROM   Categoria c
            LEFT JOIN Articulo a ON a.id_categoria = c.id_categoria
            GROUP BY c.id_categoria
            ORDER BY c.nombre
        """)
        for id_, nombre, total in self.cursor.fetchall():
            self.tree.insert('', tk.END, iid=str(id_), values=(id_, nombre, total))

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            self.lbl_info.config(text="")
            return
        id_cat = int(sel[0])
        self.cursor.execute("""
            SELECT nombre FROM Articulo WHERE id_categoria=? LIMIT 5
        """, (id_cat,))
        arts = [r[0] for r in self.cursor.fetchall()]
        if arts:
            self.lbl_info.config(
                text="Artículos en esta categoría:\n" + ", ".join(arts) +
                     ("…" if len(arts) == 5 else ""))
        else:
            self.lbl_info.config(text="Sin artículos en esta categoría.")

    def _cancelar(self):
        self._id_edit = None
        self.card.config(text="  Nueva categoría  ")
        self.var_nombre.set("")
        self.lbl_info.config(text="")

    def _editar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona una categoría para editar.")
            return
        self._id_edit = int(sel[0])
        self.cursor.execute("SELECT nombre FROM Categoria WHERE id_categoria=?",
                            (self._id_edit,))
        row = self.cursor.fetchone()
        if row:
            self.var_nombre.set(row[0])
            self.card.config(text=f"  Editando categoría #{self._id_edit}  ")

    def _guardar(self):
        nombre = self.var_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Nombre vacío", "Escribe el nombre de la categoría.")
            return

        if self._id_edit is None:
            # Verificar que no exista igual
            self.cursor.execute(
                "SELECT id_categoria FROM Categoria WHERE nombre=?", (nombre,))
            if self.cursor.fetchone():
                messagebox.showwarning("Duplicada",
                                       f"Ya existe una categoría llamada '{nombre}'.")
                return
            self.cursor.execute(
                "INSERT INTO Categoria (nombre) VALUES (?)", (nombre,))
            msg = f"✅ Categoría '{nombre}' creada."
        else:
            self.cursor.execute(
                "UPDATE Categoria SET nombre=? WHERE id_categoria=?",
                (nombre, self._id_edit))
            msg = f"✅ Categoría actualizada a '{nombre}'."

        self.db.commit()
        messagebox.showinfo("Guardado", msg)
        self._cancelar()
        self._cargar_tabla()

    def _eliminar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona una categoría para eliminar.")
            return
        id_cat = int(sel[0])

        # Verificar que no tenga artículos asociados
        self.cursor.execute(
            "SELECT COUNT(*) FROM Articulo WHERE id_categoria=?", (id_cat,))
        total = self.cursor.fetchone()[0]
        if total > 0:
            messagebox.showwarning(
                "No se puede eliminar",
                f"Esta categoría tiene {total} artículo(s) asociado(s).\n"
                "Reasigna o elimina esos artículos primero.")
            return

        self.cursor.execute(
            "SELECT nombre FROM Categoria WHERE id_categoria=?", (id_cat,))
        nombre = self.cursor.fetchone()[0]

        if not messagebox.askyesno("Confirmar",
                                   f"¿Eliminar la categoría '{nombre}'?"):
            return

        self.cursor.execute(
            "DELETE FROM Categoria WHERE id_categoria=?", (id_cat,))
        self.db.commit()
        messagebox.showinfo("Eliminada", f"Categoría '{nombre}' eliminada.")
        self._cancelar()
        self._cargar_tabla()
        

# ══════════════════════════════════════════════════════════════════════════════
#  PRODUCCIÓN DIARIA  —  reemplaza la clase InventarioProduccion en inventario.py
# ══════════════════════════════════════════════════════════════════════════════
class InventarioProduccion:
    def __init__(self, container, usuario=""):
        self.container = container
        self.usuario   = usuario
        self.db        = conexion.conectar()
        self.cursor    = self.db.cursor()
        self._modo     = tk.StringVar(value="kg")   # 'kg' o 'bultos'
        configurar_estilos(container)
        self._cargar_config()
        self._build()

    # ── Cargar configuración y existencias desde BD ───────────────────────────

    def _cargar_config(self):
        self.cursor.execute(
            "SELECT clave, valor FROM Configuracion WHERE clave IN "
            "('kg_por_bulto_harina','tortilla_por_bulto')"
        )
        cfg = dict(self.cursor.fetchall())
        self.kg_por_bulto       = float(cfg.get('kg_por_bulto_harina', 20))
        self.tortilla_por_bulto = float(cfg.get('tortilla_por_bulto',  40))

        self.cursor.execute(
            "SELECT existencia FROM Articulo WHERE codigo='TORTILLA001'")
        row = self.cursor.fetchone()
        self.exist_tortilla = row[0] if row else 0.0

        self.cursor.execute(
            "SELECT existencia FROM Articulo WHERE codigo='HARINA001'")
        row = self.cursor.fetchone()
        self.exist_harina = row[0] if row else 0.0

    # ── Construcción ──────────────────────────────────────────────────────────

    def _build(self):
        for w in self.container.winfo_children():
            w.destroy()
        self.container.configure(bg="#FFFDE7")
        _titulo(self.container, "📦  Inventario — Producción diaria")

        tk.Label(self.container,
                 text="Registra la producción del turno. "
                      "El sistema descuenta la harina automáticamente.",
                 font=("Tahoma", 9, "italic"),
                 bg="#FFFDE7", fg="#F57F17").pack(anchor="w", padx=14, pady=2)

        cuerpo = tk.Frame(self.container, bg="#FFFDE7")
        cuerpo.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.columnconfigure(1, weight=2)
        cuerpo.rowconfigure(0, weight=1)

        self._build_form(cuerpo)
        self._build_tabla(cuerpo)
        self._cargar_tabla()

    # ── Formulario ────────────────────────────────────────────────────────────

    def _build_form(self, parent):
        card = tk.LabelFrame(parent, text="  Nuevo registro de producción  ",
                             bg="#FFFDE7", fg="#1B5E20",
                             font=("Tahoma", 10, "bold"),
                             bd=2, relief="groove")
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)

        # ── Stock actual ──────────────────────────────────────────────────────
        stock_frame = tk.Frame(card, bg="#E8F5E9", padx=10, pady=8)
        stock_frame.pack(fill=tk.X, padx=12, pady=(12, 6))

        tk.Label(stock_frame, text="Stock actual",
                 font=("Tahoma", 9, "bold"),
                 bg="#E8F5E9", fg="#1B5E20").grid(row=0, column=0,
                                                   columnspan=2, sticky="w")
        tk.Label(stock_frame, text="🫓 Tortilla:",
                 font=("Tahoma", 10),
                 bg="#E8F5E9", fg="#1B5E20").grid(row=1, column=0,
                                                   sticky="w", pady=2)
        self.lbl_stock_tortilla = tk.Label(stock_frame,
                 text=f"{self.exist_tortilla:.3f} kg",
                 font=("Tahoma", 10, "bold"),
                 bg="#E8F5E9", fg="#2E7D32")
        self.lbl_stock_tortilla.grid(row=1, column=1, sticky="e", padx=8)

        tk.Label(stock_frame, text="🌾 Harina:",
                 font=("Tahoma", 10),
                 bg="#E8F5E9", fg="#1B5E20").grid(row=2, column=0,
                                                   sticky="w", pady=2)
        self.lbl_stock_harina = tk.Label(stock_frame,
                 text=f"{self.exist_harina:.3f} bultos",
                 font=("Tahoma", 10, "bold"),
                 bg="#E8F5E9", fg="#2E7D32")
        self.lbl_stock_harina.grid(row=2, column=1, sticky="e", padx=8)

        tk.Label(stock_frame,
                 text=f"Relación: 1 bulto ({self.kg_por_bulto:.0f} kg harina)"
                      f" → {self.tortilla_por_bulto:.0f} kg tortilla",
                 font=("Tahoma", 8, "italic"),
                 bg="#E8F5E9", fg="#F57F17").grid(row=3, column=0,
                                                   columnspan=2, sticky="w",
                                                   pady=(4, 0))

        # ── Selector de modo ──────────────────────────────────────────────────
        tk.Label(card, text="¿Cómo quieres registrar?",
                 font=("Tahoma", 10, "bold"),
                 bg="#FFFDE7", fg="#1B5E20").pack(anchor="w",
                                                  padx=16, pady=(10, 2))
        modos = tk.Frame(card, bg="#FFFDE7")
        modos.pack(anchor="w", padx=20)
        ttk.Radiobutton(modos,
                        text="Capturar kg de tortilla producidos",
                        variable=self._modo, value="kg",
                        command=self._actualizar_modo).pack(anchor="w", pady=2)
        ttk.Radiobutton(modos,
                        text="Capturar bultos de harina usados",
                        variable=self._modo, value="bultos",
                        command=self._actualizar_modo).pack(anchor="w", pady=2)

        # ── Contenedor de campos de captura (cambia según modo) ───────────────
        self.frame_campos = tk.Frame(card, bg="#FFFDE7")
        self.frame_campos.pack(fill=tk.X, padx=12, pady=(8, 0))

        # Variables de captura
        self.var_kg_tortilla = tk.StringVar()
        self.var_bultos      = tk.StringVar()
        self.var_kg_extra    = tk.StringVar()

        self.var_kg_tortilla.trace_add("write", self._calcular)
        self.var_bultos.trace_add("write",      self._calcular)
        self.var_kg_extra.trace_add("write",    self._calcular)

        # Se dejó el panel de solo lectura desactivado para ahorrar espacio.
        self.lbl_res_tortilla = None
        self.lbl_res_harina   = None
        self.lbl_alerta       = None

        self._build_campos_kg()     # vista inicial: modo kg

        # ── Turno activo ──────────────────────────────────────────────────────
        self.cursor.execute("""
            SELECT t.id_turno, t.fecha_apertura, u.nombre
            FROM Turno t
            JOIN Usuarios u ON u.id_usuario = t.id_usuario_apertura
            WHERE t.estado = 'abierto' LIMIT 1
        """)
        turno = self.cursor.fetchone()

        tk.Label(card, text="Turno activo:",
                 font=("Tahoma", 10, "bold"),
                 bg="#FFFDE7", fg="#1B5E20").pack(anchor="w",
                                                  padx=16, pady=(4, 2))
        if turno:
            self._id_turno = turno[0]
            tk.Label(card,
                     text=f"#{turno[0]}  —  {turno[2]}\n{turno[1]}",
                     font=("Tahoma", 9),
                     bg="#FFFDE7", fg="#2E7D32").pack(anchor="w", padx=20)
        else:
            self._id_turno = None
            tk.Label(card, text="⚠  No hay turno abierto.",
                     font=("Tahoma", 9),
                     bg="#FFFDE7", fg="#C62828").pack(anchor="w", padx=20)

        # ── Notas ─────────────────────────────────────────────────────────────
        tk.Label(card, text="Notas (opcional):",
                 font=("Tahoma", 10, "bold"),
                 bg="#FFFDE7", fg="#1B5E20").pack(anchor="w",
                                                  padx=16, pady=(10, 2))
        self.var_notas = tk.StringVar()
        ttk.Entry(card, textvariable=self.var_notas,
                  font=("Tahoma", 11), width=28).pack(padx=16)

        ttk.Button(card, text="✅  Registrar producción",
                   style="Exito.TButton", width=24,
                   command=self._registrar).pack(pady=16)

    # ── Campos según modo ─────────────────────────────────────────────────────

    def _build_campos_kg(self):
        """Modo A: el trabajador captura kg de tortilla producidos."""
        for w in self.frame_campos.winfo_children():
            w.destroy()

        tk.Label(self.frame_campos, text="Kg de tortilla producidos:",
                 font=("Tahoma", 11, "bold"),
                 bg="#FFFDE7", fg="#1B5E20").pack(anchor="w", pady=(0, 2))
        ttk.Entry(self.frame_campos, textvariable=self.var_kg_tortilla,
                  font=("Tahoma", 14), width=14).pack(anchor="w")

    def _build_campos_bultos(self):
        """Modo B: el trabajador captura bultos + kg extra de harina."""
        for w in self.frame_campos.winfo_children():
            w.destroy()

        tk.Label(self.frame_campos, text="Bultos de harina usados:",
                 font=("Tahoma", 11, "bold"),
                 bg="#FFFDE7", fg="#1B5E20").pack(anchor="w", pady=(0, 2))

        fila_bultos = tk.Frame(self.frame_campos, bg="#FFFDE7")
        fila_bultos.pack(anchor="w")
        ttk.Entry(fila_bultos, textvariable=self.var_bultos,
                  font=("Tahoma", 14), width=8).pack(side=tk.LEFT)
        tk.Label(fila_bultos, text="bultos",
                 font=("Tahoma", 11),
                 bg="#FFFDE7", fg="#1B5E20").pack(side=tk.LEFT, padx=6)

        tk.Label(self.frame_campos,
                 text="Más kg extra (del siguiente bulto):",
                 font=("Tahoma", 10, "bold"),
                 bg="#FFFDE7", fg="#1B5E20").pack(anchor="w", pady=(10, 2))

        fila_extra = tk.Frame(self.frame_campos, bg="#FFFDE7")
        fila_extra.pack(anchor="w")
        ttk.Entry(fila_extra, textvariable=self.var_kg_extra,
                  font=("Tahoma", 14), width=8).pack(side=tk.LEFT)
        tk.Label(fila_extra, text="kg  (0 si no hay extra)",
                 font=("Tahoma", 10, "italic"),
                 bg="#FFFDE7", fg="#F57F17").pack(side=tk.LEFT, padx=6)

        # Ejemplo visual
        tk.Label(self.frame_campos,
                 text=f"Ej: 2 bultos + 5 kg → "
                      f"2 + (5 ÷ {self.kg_por_bulto:.0f}) = 2.25 bultos",
                 font=("Tahoma", 8, "italic"),
                 bg="#FFFDE7", fg="#757575").pack(anchor="w", pady=(4, 0))

    # ── Lógica ────────────────────────────────────────────────────────────────

    def _actualizar_modo(self):
        """Reconstruye los campos de captura según el modo seleccionado."""
        self.var_kg_tortilla.set("")
        self.var_bultos.set("")
        self.var_kg_extra.set("")

        if self.lbl_res_tortilla is not None:
            self.lbl_res_tortilla.config(text="🫓  — kg tortilla")
        if self.lbl_res_harina is not None:
            self.lbl_res_harina.config(text="🌾  — bultos harina a descontar")
        if self.lbl_alerta is not None:
            self.lbl_alerta.config(text="")

        if self._modo.get() == "kg":
            self._build_campos_kg()
        else:
            self._build_campos_bultos()

    def _calcular(self, *args):
        """Calcula automáticamente el complemento según el modo."""
        try:
            if self._modo.get() == "kg":
                # Modo A: captura kg tortilla → calcula bultos harina
                kg_tortilla = float(self.var_kg_tortilla.get().replace(",", "."))
                if kg_tortilla <= 0:
                    raise ValueError
                bultos_harina = kg_tortilla / self.tortilla_por_bulto

            else:
                # Modo B: captura bultos + kg extra → calcula kg tortilla
                bultos   = float(self.var_bultos.get().replace(",", ".") or "0")
                kg_extra = float(self.var_kg_extra.get().replace(",", ".") or "0")

                if bultos < 0 or kg_extra < 0:
                    raise ValueError
                if bultos == 0 and kg_extra == 0:
                    raise ValueError

                # Conversión: kg extra → fracción de bulto
                fraccion      = kg_extra / self.kg_por_bulto
                bultos_harina = bultos + fraccion
                kg_tortilla   = bultos_harina * self.tortilla_por_bulto

        except (ValueError, ZeroDivisionError):
            if self.lbl_res_tortilla is not None:
                self.lbl_res_tortilla.config(text="🫓  — kg tortilla")
            if self.lbl_res_harina is not None:
                self.lbl_res_harina.config(text="🌾  — bultos harina a descontar")
            if self.lbl_alerta is not None:
                self.lbl_alerta.config(text="")
            return

        if self.lbl_res_tortilla is not None:
            self.lbl_res_tortilla.config(
                text=f"🫓  +{kg_tortilla:.3f} kg tortilla")
        if self.lbl_res_harina is not None:
            self.lbl_res_harina.config(
                text=f"🌾  -{bultos_harina:.3f} bultos harina"
                     + (f"  ({bultos_harina * self.kg_por_bulto:.2f} kg)"
                        if self._modo.get() == "bultos" else ""))

        # Guardar valores calculados para usarlos en _registrar
        self._kg_tortilla_calc   = kg_tortilla
        self._bultos_harina_calc = bultos_harina

        # Alerta de stock
        if self.lbl_alerta is not None:
            if bultos_harina > self.exist_harina:
                self.lbl_alerta.config(
                    text=f"⚠ Solo hay {self.exist_harina:.3f} bultos disponibles.")
            else:
                self.lbl_alerta.config(text="")

    def _cargar_tabla(self):
        from datetime import date
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        hoy = date.today().isoformat()
        self.cursor.execute("""
            SELECT m.cantidad, m.existencia_anterior, m.existencia_nueva,
                   m.referencia, m.fecha, u.nombre
            FROM MovimientoInventario m
            JOIN Usuarios u ON u.id_usuario = m.id_usuario
            WHERE m.tipo   = 'entrada_produccion'
              AND m.codigo = 'TORTILLA001'
              AND DATE(m.fecha) = ?
            ORDER BY m.fecha DESC
        """, (hoy,))
        rows = self.cursor.fetchall()

        total_kg     = sum(r[0] for r in rows)
        total_bultos = total_kg / self.tortilla_por_bulto if self.tortilla_por_bulto else 0
        self.lbl_total.config(
            text=f"Total: {total_kg:.3f} kg  |  ~{total_bultos:.2f} bultos"
            if rows else "Sin registros hoy")

        for cant, ant, nueva, ref, fecha, usr in rows:
            hora          = fecha[11:19] if len(fecha) > 10 else "—"
            bultos_usados = cant / self.tortilla_por_bulto if self.tortilla_por_bulto else 0
            self.tree.insert('', tk.END, values=(
                f"+{cant:.3f} kg",
                f"{ant:.3f}",
                f"{nueva:.3f}",
                f"{bultos_usados:.3f} bultos",
                ref or "—",
                hora,
                usr,
            ))

    # ── Tabla ─────────────────────────────────────────────────────────────────

    def _build_tabla(self, parent):
        frame = tk.Frame(parent, bg="#FFFDE7")
        frame.grid(row=0, column=1, sticky="nsew", pady=4)

        enc = tk.Frame(frame, bg="#FFFDE7")
        enc.pack(fill=tk.X, pady=(0, 4))
        tk.Label(enc, text="Producción de hoy",
                 font=("Tahoma", 11, "bold"),
                 bg="#FFFDE7", fg="#1B5E20").pack(side=tk.LEFT)
        self.lbl_total = tk.Label(enc, text="",
                                  font=("Tahoma", 11, "bold"),
                                  bg="#FFFDE7", fg="#2E7D32")
        self.lbl_total.pack(side=tk.RIGHT, padx=8)

        style = ttk.Style()
        style.configure("Carmelita.Treeview",
                        background="#FFFFFF", fieldbackground="#FFFFFF",
                        foreground="#1B5E20", rowheight=28,
                        font=("Tahoma", 10))
        style.configure("Carmelita.Treeview.Heading",
                        background="#2E7D32", foreground="#F9A825",
                        font=("Tahoma", 10, "bold"))
        style.map("Carmelita.Treeview",
                  background=[("selected", "#4CAF50")],
                  foreground=[("selected", "#FFFFFF")])

        cols = ("cantidad", "ant", "nueva",
                "harina_usada", "notas", "hora", "usuario")
        self.tree = ttk.Treeview(frame, columns=cols,
                                 show="headings", style="Carmelita.Treeview")
        for col, texto, ancho in [
            ("cantidad",     "Kg producidos",  110),
            ("ant",          "Stock ant.",       90),
            ("nueva",        "Stock nuevo",      90),
            ("harina_usada", "Harina usada",    120),
            ("notas",        "Notas",           150),
            ("hora",         "Hora",             75),
            ("usuario",      "Registró",        110),
        ]:
            self.tree.heading(col, text=texto, anchor="center")
            self.tree.column(col, width=ancho, anchor="center")

        sb = ttk.Scrollbar(frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.LEFT, fill=tk.Y)

    # ── Registrar ─────────────────────────────────────────────────────────────

    def _registrar(self):
        # Verificar que el cálculo esté hecho
        kg_tortilla   = getattr(self, '_kg_tortilla_calc',   None)
        bultos_harina = getattr(self, '_bultos_harina_calc', None)

        if not kg_tortilla or not bultos_harina or kg_tortilla <= 0:
            messagebox.showwarning("Sin datos",
                                   "Ingresa los valores de producción primero.")
            return

        # Advertir si no hay harina suficiente pero permitir continuar
        if bultos_harina > self.exist_harina:
            if not messagebox.askyesno(
                "Stock insuficiente",
                f"Se necesitan {bultos_harina:.3f} bultos de harina\n"
                f"pero solo hay {self.exist_harina:.3f} disponibles.\n\n"
                "¿Registrar de todas formas?\n"
                "(El stock de harina quedará negativo)"
            ):
                return

        # Id del usuario activo
        self.cursor.execute(
            "SELECT id_usuario FROM Usuarios WHERE nombre=?", (self.usuario,))
        row = self.cursor.fetchone()
        if not row:
            messagebox.showerror("Error",
                                 "No se encontró el usuario activo en la BD.")
            return
        id_usuario = row[0]

        from datetime import datetime
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        notas = self.var_notas.get().strip()
        ref   = f"Producción {ahora[:10]}" + (f" — {notas}" if notas else "")

        # Detalle legible para la confirmación según modo
        if self._modo.get() == "bultos":
            try:
                bultos   = float(self.var_bultos.get() or "0")
                kg_extra = float(self.var_kg_extra.get() or "0")
                detalle  = (f"Bultos: {bultos:.0f}  +  {kg_extra:.1f} kg extra\n"
                            f"Total harina: {bultos_harina:.3f} bultos\n")
            except ValueError:
                detalle = ""
        else:
            detalle = ""

        if not messagebox.askyesno(
            "Confirmar producción",
            f"{detalle}"
            f"Tortilla a registrar:  +{kg_tortilla:.3f} kg\n"
            f"Harina a descontar:    -{bultos_harina:.3f} bultos\n\n"
            f"Stock tortilla:  {self.exist_tortilla:.3f} → "
            f"{self.exist_tortilla + kg_tortilla:.3f} kg\n"
            f"Stock harina:    {self.exist_harina:.3f} → "
            f"{self.exist_harina - bultos_harina:.3f} bultos\n\n"
            "¿Registrar?"
        ):
            return

        try:
            nueva_tortilla = self.exist_tortilla + kg_tortilla
            nueva_harina   = self.exist_harina   - bultos_harina

            # Tortilla → entrada_produccion
            self.cursor.execute(
                "UPDATE Articulo SET existencia=? WHERE codigo='TORTILLA001'",
                (nueva_tortilla,))
            self.cursor.execute("""
                INSERT INTO MovimientoInventario
                    (codigo, tipo, cantidad, existencia_anterior,
                     existencia_nueva, referencia, fecha, id_usuario)
                VALUES ('TORTILLA001','entrada_produccion',?,?,?,?,?,?)
            """, (kg_tortilla, self.exist_tortilla,
                  nueva_tortilla, ref, ahora, id_usuario))

            # Harina → salida_produccion (negativo)
            self.cursor.execute(
                "UPDATE Articulo SET existencia=? WHERE codigo='HARINA001'",
                (nueva_harina,))
            self.cursor.execute("""
                INSERT INTO MovimientoInventario
                    (codigo, tipo, cantidad, existencia_anterior,
                     existencia_nueva, referencia, fecha, id_usuario)
                VALUES ('HARINA001','salida_produccion',?,?,?,?,?,?)
            """, (-bultos_harina, self.exist_harina,
                  nueva_harina, ref, ahora, id_usuario))

            self.db.commit()

            messagebox.showinfo("Producción registrada",
                                f"✅ +{kg_tortilla:.3f} kg de tortilla\n"
                                f"🌾  -{bultos_harina:.3f} bultos de harina descontados")

            # Actualizar estado local
            self.exist_tortilla = nueva_tortilla
            self.exist_harina   = nueva_harina
            self.lbl_stock_tortilla.config(text=f"{nueva_tortilla:.3f} kg")
            self.lbl_stock_harina.config(text=f"{nueva_harina:.3f} bultos")

            # Limpiar valores calculados y form
            self._kg_tortilla_calc   = None
            self._bultos_harina_calc = None
            self.var_kg_tortilla.set("")
            self.var_bultos.set("")
            self.var_kg_extra.set("")
            self.var_notas.set("")
            if self.lbl_res_tortilla is not None:
                self.lbl_res_tortilla.config(text="🫓  — kg tortilla")
            if self.lbl_res_harina is not None:
                self.lbl_res_harina.config(text="🌾  — bultos harina a descontar")
            if self.lbl_alerta is not None:
                self.lbl_alerta.config(text="")
            self._cargar_tabla()

        except Exception as e:
            self.db.rollback()
            messagebox.showerror("Error",
                                 f"No se pudo registrar.\n\nDetalle: {e}")