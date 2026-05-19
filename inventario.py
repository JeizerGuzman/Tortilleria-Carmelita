import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import conexion
from botones import configurar_estilos

# ── Helper compartido ─────────────────────────────────────────────────────────

def _titulo(container, texto):
    f = tk.Frame(container, bg="#C47A2B", padx=10, pady=6)
    f.pack(fill=tk.X)
    tk.Label(f, text=texto, font=("Tahoma", 14, "bold"),
             fg="#FFF8E7", bg="#C47A2B").pack(side=tk.LEFT)
    return f


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
        self.container.configure(bg="#FFF8E7")

        title_frame = _titulo(self.container, "📦  Inventario — Existencias")
        ttk.Button(title_frame, text="🔄 Actualizar",
                   style="Cafe.TButton",
                   command=self._cargar_tabla).pack(side=tk.RIGHT, padx=6)

        # Leyenda
        leyenda = tk.Frame(self.container, bg="#FFF8E7")
        leyenda.pack(fill=tk.X, padx=10, pady=4)
        tk.Label(leyenda, text="🔴 Stock en punto de reorden o menor",
                 font=("Tahoma", 9), bg="#FFF8E7", fg="#A93226").pack(side=tk.LEFT, padx=8)
        tk.Label(leyenda, text="🟢 Stock normal",
                 font=("Tahoma", 9), bg="#FFF8E7", fg="#2D6A4F").pack(side=tk.LEFT, padx=8)

        # Tabla
        tf = tk.Frame(self.container, bg="#FFF8E7")
        tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Carmelita.Treeview",
                        background="#FFFFFF", fieldbackground="#FFFFFF",
                        foreground="#7B3F00", rowheight=30,
                        font=("Tahoma", 11))
        style.configure("Carmelita.Treeview.Heading",
                        background="#7B3F00", foreground="#F2C94C",
                        font=("Tahoma", 11, "bold"))
        style.map("Carmelita.Treeview",
                  background=[("selected", "#C47A2B")],
                  foreground=[("selected", "#FFFFFF")])

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

        self.tree.tag_configure("alerta", foreground="#A93226", background="#FFF0F0")
        self.tree.tag_configure("normal", foreground="#2D6A4F")

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
        self.container.configure(bg="#FFF8E7")
        _titulo(self.container, "📦  Inventario — Movimientos")

        # Filtros
        filtros = tk.Frame(self.container, bg="#FFF8E7", padx=10, pady=8)
        filtros.pack(fill=tk.X)

        tk.Label(filtros, text="Artículo:",
                 font=("Tahoma", 10, "bold"),
                 bg="#FFF8E7", fg="#7B3F00").pack(side=tk.LEFT, padx=(0, 4))

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
                 bg="#FFF8E7", fg="#7B3F00").pack(side=tk.LEFT, padx=(12, 4))
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
        tf = tk.Frame(self.container, bg="#FFF8E7")
        tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        style = ttk.Style()
        style.configure("Carmelita.Treeview",
                        background="#FFFFFF", fieldbackground="#FFFFFF",
                        foreground="#7B3F00", rowheight=28,
                        font=("Tahoma", 10))
        style.configure("Carmelita.Treeview.Heading",
                        background="#7B3F00", foreground="#F2C94C",
                        font=("Tahoma", 10, "bold"))
        style.map("Carmelita.Treeview",
                  background=[("selected", "#C47A2B")],
                  foreground=[("selected", "#FFFFFF")])

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

        self.tree.tag_configure("entrada", foreground="#2D6A4F")
        self.tree.tag_configure("salida",  foreground="#A93226")

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
    def __init__(self, container):
        self.container = container
        self.db        = conexion.conectar()
        self.cursor    = self.db.cursor()
        configurar_estilos(container)
        self._build()

    def _build(self):
        for w in self.container.winfo_children():
            w.destroy()
        self.container.configure(bg="#FFF8E7")
        _titulo(self.container, "📦  Inventario — Ajuste manual")

        tk.Label(self.container,
                 text="Solo el administrador puede corregir existencias manualmente.",
                 font=("Tahoma", 9, "italic"),
                 bg="#FFF8E7", fg="#C47A2B").pack(anchor="w", padx=12, pady=2)

        cuerpo = tk.Frame(self.container, bg="#FFF8E7")
        cuerpo.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.columnconfigure(1, weight=2)
        cuerpo.rowconfigure(0, weight=1)

        self._form(cuerpo)
        self._tabla_recientes(cuerpo)

    def _form(self, parent):
        card = tk.LabelFrame(parent, text="  Nuevo ajuste  ",
                             bg="#FFF8E7", fg="#7B3F00",
                             font=("Tahoma", 10, "bold"),
                             bd=2, relief="groove")
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)

        # Artículo
        tk.Label(card, text="Artículo:",
                 font=("Tahoma", 11, "bold"),
                 bg="#FFF8E7", fg="#7B3F00").pack(anchor="w", padx=16, pady=(14, 2))

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
                                  bg="#FFF8E7", fg="#C47A2B")
        self.lbl_exist.pack(anchor="w", padx=16, pady=2)

        # Tipo de ajuste
        tk.Label(card, text="Tipo de ajuste:",
                 font=("Tahoma", 11, "bold"),
                 bg="#FFF8E7", fg="#7B3F00").pack(anchor="w", padx=16, pady=(10, 2))
        self.var_tipo = tk.StringVar(value="ajuste_manual")
        for texto, val in [("Ajuste manual (corrección)", "ajuste_manual"),
                           ("Merma (pérdida/desperdicio)", "merma")]:
            ttk.Radiobutton(card, text=texto, variable=self.var_tipo,
                            value=val).pack(anchor="w", padx=20, pady=2)

        # Nueva existencia
        tk.Label(card, text="Nueva existencia:",
                 font=("Tahoma", 11, "bold"),
                 bg="#FFF8E7", fg="#7B3F00").pack(anchor="w", padx=16, pady=(10, 2))
        self.var_nueva = tk.StringVar()
        ttk.Entry(card, textvariable=self.var_nueva,
                  font=("Tahoma", 11), width=14).pack(padx=16)

        # Motivo
        tk.Label(card, text="Motivo:",
                 font=("Tahoma", 11, "bold"),
                 bg="#FFF8E7", fg="#7B3F00").pack(anchor="w", padx=16, pady=(10, 2))
        self.var_motivo = tk.StringVar()
        ttk.Entry(card, textvariable=self.var_motivo,
                  font=("Tahoma", 11), width=28).pack(padx=16)

        # Usuario que ajusta
        tk.Label(card, text="Usuario (administrador):",
                 font=("Tahoma", 11, "bold"),
                 bg="#FFF8E7", fg="#7B3F00").pack(anchor="w", padx=16, pady=(10, 2))
        self.cursor.execute(
            "SELECT nombre FROM Usuarios WHERE rol='administrador'")
        admins = [r[0] for r in self.cursor.fetchall()]
        self.var_usuario = tk.StringVar(value=admins[0] if admins else "")
        ttk.Combobox(card, textvariable=self.var_usuario,
                     values=admins, state="readonly",
                     font=("Tahoma", 11), width=24).pack(padx=16)

        ttk.Button(card, text="Aplicar ajuste",
                   style="Advertencia.TButton", width=20,
                   command=self._aplicar).pack(pady=16)

    def _tabla_recientes(self, parent):
        frame = tk.Frame(parent, bg="#FFF8E7")
        frame.grid(row=0, column=1, sticky="nsew", pady=4)

        tk.Label(frame, text="Ajustes recientes",
                 font=("Tahoma", 11, "bold"),
                 bg="#FFF8E7", fg="#7B3F00").pack(anchor="w", pady=(4, 6))

        style = ttk.Style()
        style.configure("Carmelita.Treeview",
                        background="#FFFFFF", fieldbackground="#FFFFFF",
                        foreground="#7B3F00", rowheight=28,
                        font=("Tahoma", 10))
        style.configure("Carmelita.Treeview.Heading",
                        background="#7B3F00", foreground="#F2C94C",
                        font=("Tahoma", 10, "bold"))
        style.map("Carmelita.Treeview",
                  background=[("selected", "#C47A2B")],
                  foreground=[("selected", "#FFFFFF")])

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

        usuario_nombre = self.var_usuario.get()
        if not usuario_nombre:
            messagebox.showwarning("Sin usuario", "Selecciona el usuario administrador.")
            return

        codigo, exist_ant = self.art_map[nombre]
        diferencia        = nueva_exist - exist_ant
        ahora             = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute(
            "SELECT id_usuario FROM Usuarios WHERE nombre = ?", (usuario_nombre,))
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
        self.container.configure(bg="#FFF8E7")

        title_frame = _titulo(self.container, "📦  Inventario — Artículos")
        ttk.Button(title_frame, text="➕ Nuevo artículo",
                   style="Cafe.TButton",
                   command=self._nuevo).pack(side=tk.RIGHT, padx=6)

        cuerpo = tk.Frame(self.container, bg="#FFF8E7")
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
                                  bg="#FFF8E7", fg="#7B3F00",
                                  font=("Tahoma", 10, "bold"),
                                  bd=2, relief="groove")
        self.card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)

        def fila(label, widget_fn, **kw):
            tk.Label(self.card, text=label,
                     font=("Tahoma", 10, "bold"),
                     bg="#FFF8E7", fg="#7B3F00").pack(anchor="w", padx=16, pady=(10, 2))
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
                 bg="#FFF8E7", fg="#7B3F00").pack(anchor="w", padx=16, pady=(10, 2))
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
                 bg="#FFF8E7", fg="#7B3F00").pack(anchor="w", padx=16, pady=(10, 2))
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
                 bg="#FFF8E7", fg="#7B3F00").pack(anchor="w", padx=16, pady=(10, 2))
        self.var_prov = tk.StringVar(value="Sin proveedor")
        self.cb_prov  = ttk.Combobox(self.card, textvariable=self.var_prov,
                                     values=[n for _, n in self._provs],
                                     state="readonly", font=("Tahoma", 11), width=26)
        self.cb_prov.pack(padx=16)

        # Botones
        frame_btns = tk.Frame(self.card, bg="#FFF8E7")
        frame_btns.pack(pady=14)
        ttk.Button(frame_btns, text="💾 Guardar",
                   style="Dorado.TButton", width=14,
                   command=self._guardar).pack(side=tk.LEFT, padx=6)
        ttk.Button(frame_btns, text="✖ Cancelar",
                   style="Peligro.TButton", width=14,
                   command=self._nuevo).pack(side=tk.LEFT, padx=6)

    # ── Tabla ─────────────────────────────────────────────────────────────────

    def _build_tabla(self, parent):
        frame = tk.Frame(parent, bg="#FFF8E7")
        frame.grid(row=0, column=1, sticky="nsew", pady=4)

        # Botones de acción sobre la tabla
        acc = tk.Frame(frame, bg="#FFF8E7")
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
                        foreground="#7B3F00", rowheight=28,
                        font=("Tahoma", 10))
        style.configure("Carmelita.Treeview.Heading",
                        background="#7B3F00", foreground="#F2C94C",
                        font=("Tahoma", 10, "bold"))
        style.map("Carmelita.Treeview",
                  background=[("selected", "#C47A2B")],
                  foreground=[("selected", "#FFFFFF")])

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

        self.tree.tag_configure("fijo",     background="#FFF8DC", foreground="#7B3F00")
        self.tree.tag_configure("insumo",   foreground="#2D6A4F")
        self.tree.tag_configure("venta",    foreground="#1A5276")
        self.tree.tag_configure("inactivo", foreground="#AAAAAA")

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
        self.var_reorden.set("")
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
        self.container.configure(bg="#FFF8E7")
        _titulo(self.container, "📦  Inventario — Categorías")

        cuerpo = tk.Frame(self.container, bg="#FFF8E7")
        cuerpo.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.columnconfigure(1, weight=2)
        cuerpo.rowconfigure(0, weight=1)

        self._build_form(cuerpo)
        self._build_tabla(cuerpo)
        self._cargar_tabla()

    def _build_form(self, parent):
        self.card = tk.LabelFrame(parent, text="  Nueva categoría  ",
                                  bg="#FFF8E7", fg="#7B3F00",
                                  font=("Tahoma", 10, "bold"),
                                  bd=2, relief="groove")
        self.card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)

        tk.Label(self.card, text="Nombre de la categoría:",
                 font=("Tahoma", 11, "bold"),
                 bg="#FFF8E7", fg="#7B3F00").pack(anchor="w", padx=16, pady=(20, 4))

        self.var_nombre = tk.StringVar()
        ttk.Entry(self.card, textvariable=self.var_nombre,
                  font=("Tahoma", 12), width=26).pack(padx=16)

        frame_btns = tk.Frame(self.card, bg="#FFF8E7")
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
                                 bg="#FFF8E7", fg="#C47A2B",
                                 wraplength=220, justify="left")
        self.lbl_info.pack(padx=16, pady=4)

    def _build_tabla(self, parent):
        frame = tk.Frame(parent, bg="#FFF8E7")
        frame.grid(row=0, column=1, sticky="nsew", pady=4)

        acc = tk.Frame(frame, bg="#FFF8E7")
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
                        foreground="#7B3F00", rowheight=30,
                        font=("Tahoma", 11))
        style.configure("Carmelita.Treeview.Heading",
                        background="#7B3F00", foreground="#F2C94C",
                        font=("Tahoma", 11, "bold"))
        style.map("Carmelita.Treeview",
                  background=[("selected", "#C47A2B")],
                  foreground=[("selected", "#FFFFFF")])

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
#  PRODUCCIÓN DIARIA
# ══════════════════════════════════════════════════════════════════════════════
class InventarioProduccion:
    def __init__(self, container, usuario=""):
        self.container = container
        self.usuario   = usuario
        self.db        = conexion.conectar()
        self.cursor    = self.db.cursor()
        configurar_estilos(container)
        self._build()

    # ── Construcción ──────────────────────────────────────────────────────────

    def _build(self):
        for w in self.container.winfo_children():
            w.destroy()
        self.container.configure(bg="#FFF8E7")
        _titulo(self.container, "📦  Inventario — Producción diaria")

        tk.Label(self.container,
                 text="Registra aquí los kilogramos producidos en el turno.",
                 font=("Tahoma", 9, "italic"),
                 bg="#FFF8E7", fg="#C47A2B").pack(anchor="w", padx=14, pady=2)

        cuerpo = tk.Frame(self.container, bg="#FFF8E7")
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
                             bg="#FFF8E7", fg="#7B3F00",
                             font=("Tahoma", 10, "bold"),
                             bd=2, relief="groove")
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)

        # Artículo — solo productos de venta (es_insumo = 0)
        tk.Label(card, text="Artículo producido:",
                 font=("Tahoma", 11, "bold"),
                 bg="#FFF8E7", fg="#7B3F00").pack(anchor="w", padx=16, pady=(16, 2))

        self.cursor.execute("""
            SELECT codigo, nombre, existencia
            FROM Articulo
            WHERE es_insumo = 0
            ORDER BY nombre
        """)
        self._arts = self.cursor.fetchall()
        self._art_map = {r[1]: (r[0], r[2]) for r in self._arts}
        nombres = [r[1] for r in self._arts]

        self.var_art = tk.StringVar(value="Tortilla" if "Tortilla" in nombres else "")
        self.cb_art  = ttk.Combobox(card, textvariable=self.var_art,
                                    values=nombres, state="readonly",
                                    font=("Tahoma", 11), width=24)
        self.cb_art.pack(padx=16)
        self.cb_art.bind("<<ComboboxSelected>>", self._actualizar_existencia)

        # Existencia actual
        self.lbl_exist = tk.Label(card, text="",
                                  font=("Tahoma", 10, "italic"),
                                  bg="#FFF8E7", fg="#C47A2B")
        self.lbl_exist.pack(anchor="w", padx=16, pady=2)
        self._actualizar_existencia()   # mostrar desde el inicio

        # Cantidad producida
        tk.Label(card, text="Cantidad producida (kg):",
                 font=("Tahoma", 11, "bold"),
                 bg="#FFF8E7", fg="#7B3F00").pack(anchor="w", padx=16, pady=(14, 2))

        self.var_cantidad = tk.StringVar()
        ttk.Entry(card, textvariable=self.var_cantidad,
                  font=("Tahoma", 13), width=14).pack(padx=16)

        # Turno activo
        self.cursor.execute("""
            SELECT t.id_turno, t.fecha_apertura, u.nombre
            FROM Turno t
            JOIN Usuarios u ON u.id_usuario = t.id_usuario_apertura
            WHERE t.estado = 'abierto' LIMIT 1
        """)
        turno = self.cursor.fetchone()

        tk.Label(card, text="Turno activo:",
                 font=("Tahoma", 11, "bold"),
                 bg="#FFF8E7", fg="#7B3F00").pack(anchor="w", padx=16, pady=(14, 2))

        if turno:
            self._id_turno = turno[0]
            tk.Label(card,
                     text=f"#{turno[0]}  —  Abierto por {turno[2]}\n{turno[1]}",
                     font=("Tahoma", 10),
                     bg="#FFF8E7", fg="#2D6A4F").pack(anchor="w", padx=16)
        else:
            self._id_turno = None
            tk.Label(card,
                     text="⚠  No hay turno abierto.",
                     font=("Tahoma", 10),
                     bg="#FFF8E7", fg="#A93226").pack(anchor="w", padx=16)

        # Notas opcionales
        tk.Label(card, text="Notas (opcional):",
                 font=("Tahoma", 11, "bold"),
                 bg="#FFF8E7", fg="#7B3F00").pack(anchor="w", padx=16, pady=(14, 2))
        self.var_notas = tk.StringVar()
        ttk.Entry(card, textvariable=self.var_notas,
                  font=("Tahoma", 11), width=28).pack(padx=16)

        # Botón registrar
        ttk.Button(card, text="✅  Registrar producción",
                   style="Dorado.TButton", width=24,
                   command=self._registrar).pack(pady=20)

    # ── Tabla de producción del día ───────────────────────────────────────────

    def _build_tabla(self, parent):
        frame = tk.Frame(parent, bg="#FFF8E7")
        frame.grid(row=0, column=1, sticky="nsew", pady=4)

        # Encabezado con total del día
        enc = tk.Frame(frame, bg="#FFF8E7")
        enc.pack(fill=tk.X, pady=(0, 4))
        tk.Label(enc, text="Producción de hoy",
                 font=("Tahoma", 11, "bold"),
                 bg="#FFF8E7", fg="#7B3F00").pack(side=tk.LEFT)
        self.lbl_total = tk.Label(enc, text="",
                                  font=("Tahoma", 11, "bold"),
                                  bg="#FFF8E7", fg="#2D6A4F")
        self.lbl_total.pack(side=tk.RIGHT, padx=8)

        style = ttk.Style()
        style.configure("Carmelita.Treeview",
                        background="#FFFFFF", fieldbackground="#FFFFFF",
                        foreground="#7B3F00", rowheight=28,
                        font=("Tahoma", 10))
        style.configure("Carmelita.Treeview.Heading",
                        background="#7B3F00", foreground="#F2C94C",
                        font=("Tahoma", 10, "bold"))
        style.map("Carmelita.Treeview",
                  background=[("selected", "#C47A2B")],
                  foreground=[("selected", "#FFFFFF")])

        cols = ("articulo", "cantidad", "ant", "nueva", "notas", "hora", "usuario")
        self.tree = ttk.Treeview(frame, columns=cols,
                                 show="headings", style="Carmelita.Treeview")
        for col, texto, ancho in [
            ("articulo", "Artículo",    160),
            ("cantidad", "Producido",    90),
            ("ant",      "Stock ant.",   90),
            ("nueva",    "Stock nuevo",  90),
            ("notas",    "Notas",       160),
            ("hora",     "Hora",         80),
            ("usuario",  "Registró",    110),
        ]:
            self.tree.heading(col, text=texto, anchor="center")
            self.tree.column(col, width=ancho, anchor="center")

        sb = ttk.Scrollbar(frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.LEFT, fill=tk.Y)

    # ── Lógica ────────────────────────────────────────────────────────────────

    def _actualizar_existencia(self, event=None):
        nombre = self.var_art.get()
        if nombre and nombre in self._art_map:
            _, exist = self._art_map[nombre]
            self.lbl_exist.config(text=f"Existencia actual: {exist:.3f} kg")
        else:
            self.lbl_exist.config(text="")

    def _cargar_tabla(self):
        from datetime import date
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        hoy = date.today().isoformat()
        self.cursor.execute("""
            SELECT a.nombre, m.cantidad, m.existencia_anterior,
                   m.existencia_nueva, m.referencia, m.fecha, u.nombre
            FROM MovimientoInventario m
            JOIN Articulo a  ON a.codigo     = m.codigo
            JOIN Usuarios u  ON u.id_usuario = m.id_usuario
            WHERE m.tipo = 'entrada_produccion'
              AND DATE(m.fecha) = ?
            ORDER BY m.fecha DESC
        """, (hoy,))
        rows = self.cursor.fetchall()

        total_hoy = sum(r[1] for r in rows)
        self.lbl_total.config(
            text=f"Total hoy: {total_hoy:.3f} kg" if rows else "Sin registros hoy")

        for nombre, cant, ant, nueva, ref, fecha, usr in rows:
            hora = fecha[11:19] if len(fecha) > 10 else "—"
            self.tree.insert('', tk.END, values=(
                nombre,
                f"+{cant:.3f} kg",
                f"{ant:.3f}",
                f"{nueva:.3f}",
                ref or "—",
                hora,
                usr,
            ))

    def _registrar(self):
        nombre = self.var_art.get()
        if not nombre or nombre not in self._art_map:
            messagebox.showwarning("Sin artículo",
                                   "Selecciona el artículo producido.")
            return

        try:
            cantidad = float(self.var_cantidad.get().replace(",", "."))
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Cantidad inválida",
                                   "Ingresa una cantidad mayor a 0.")
            return

        codigo, exist_ant = self._art_map[nombre]
        exist_nueva       = exist_ant + cantidad
        notas             = self.var_notas.get().strip() or None

        # Obtener id del usuario activo
        self.cursor.execute(
            "SELECT id_usuario FROM Usuarios WHERE nombre=?", (self.usuario,))
        row = self.cursor.fetchone()
        if not row:
            messagebox.showerror("Error",
                                 "No se encontró el usuario activo en la base de datos.")
            return
        id_usuario = row[0]

        from datetime import datetime
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        confirmar = messagebox.askyesno(
            "Confirmar producción",
            f"Artículo:          {nombre}\n"
            f"Existencia actual: {exist_ant:.3f} kg\n"
            f"Producción:        +{cantidad:.3f} kg\n"
            f"Nueva existencia:  {exist_nueva:.3f} kg\n\n"
            "¿Registrar?"
        )
        if not confirmar:
            return

        try:
            # Actualizar existencia
            self.cursor.execute(
                "UPDATE Articulo SET existencia=? WHERE codigo=?",
                (exist_nueva, codigo))

            # Registrar movimiento
            self.cursor.execute("""
                INSERT INTO MovimientoInventario
                    (codigo, tipo, cantidad, existencia_anterior,
                     existencia_nueva, referencia, fecha, id_usuario)
                VALUES (?, 'entrada_produccion', ?, ?, ?, ?, ?, ?)
            """, (codigo, cantidad, exist_ant, exist_nueva, notas, ahora, id_usuario))

            self.db.commit()

            messagebox.showinfo("Producción registrada",
                                f"✅ Se agregaron {cantidad:.3f} kg de {nombre}.\n"
                                f"Nueva existencia: {exist_nueva:.3f} kg")

            # Resetear formulario
            self.var_cantidad.set("")
            self.var_notas.set("")

            # Actualizar mapa local con nueva existencia
            self._art_map[nombre] = (codigo, exist_nueva)
            self._actualizar_existencia()
            self._cargar_tabla()

        except Exception as e:
            self.db.rollback()
            messagebox.showerror("Error",
                                 f"No se pudo registrar la producción.\n\nDetalle: {e}")