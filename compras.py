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


# ══════════════════════════════════════════════════════════════════════════════
#  NUEVA COMPRA
# ══════════════════════════════════════════════════════════════════════════════
class ComprasNueva:
    def __init__(self, container, usuario):
        self.container = container
        self.usuario   = usuario
        self.db        = conexion.conectar()
        self.cursor    = self.db.cursor()
        self.items     = []   # [{codigo, nombre, cantidad, costo, subtotal}]
        configurar_estilos(container)
        self._build()

    def _get_usuario_id(self):
        self.cursor.execute(
            "SELECT id_usuario FROM Usuarios WHERE nombre = ?", (self.usuario,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def _build(self):
        for w in self.container.winfo_children():
            w.destroy()
        self.container.configure(bg=COLORES_MODULOS["fondo_contenedor"])
        _titulo(self.container, "🚚  Compras — Nueva compra")

        cuerpo = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        cuerpo.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.columnconfigure(1, weight=2)
        cuerpo.rowconfigure(0, weight=1)

        self._form_encabezado(cuerpo)
        self._panel_articulos(cuerpo)

    # ── Encabezado de la compra ───────────────────────────────────────────────

    def _form_encabezado(self, parent):
        card = tk.LabelFrame(parent, text="  Datos de la compra  ",
                             bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"],
                             font=("Tahoma", 10, "bold"),
                             bd=2, relief="groove")
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)

        # Proveedor
        tk.Label(card, text="Proveedor:",
                 font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(14, 2))
        self.cursor.execute("SELECT id_proveedor, nombre FROM Proveedor ORDER BY nombre")
        provs = self.cursor.fetchall()
        self.prov_map = {r[1]: r[0] for r in provs}
        self.var_prov = tk.StringVar()
        self.cb_prov  = ttk.Combobox(card, textvariable=self.var_prov,
                                     values=list(self.prov_map.keys()),
                                     state="readonly", font=("Tahoma", 11), width=26)
        self.cb_prov.pack(padx=16)
        if provs:
            self.cb_prov.current(0)

        # Tipo de documento
        tk.Label(card, text="Tipo de documento:",
                 font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(10, 2))
        self.var_tipodoc = tk.StringVar(value="Remisión")
        ttk.Combobox(card, textvariable=self.var_tipodoc,
                     values=["Factura", "Remisión", "Ticket", "Nota"],
                     state="readonly", font=("Tahoma", 11), width=16).pack(padx=16)

        # Número de documento
        tk.Label(card, text="Núm. documento:",
                 font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(10, 2))
        self.var_numdoc = tk.StringVar()
        ttk.Entry(card, textvariable=self.var_numdoc,
                  font=("Tahoma", 11), width=20).pack(padx=16)

        ttk.Separator(card, orient="horizontal").pack(fill=tk.X, padx=16, pady=14)

        # Agregar artículo a la compra
        tk.Label(card, text="— Agregar artículo —",
                 font=("Tahoma", 10, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_error"]).pack()

        self.cursor.execute(
            "SELECT codigo, nombre FROM Articulo WHERE es_insumo = 1 ORDER BY nombre")
        insumos = self.cursor.fetchall()
        self.ins_map = {r[1]: r[0] for r in insumos}

        tk.Label(card, text="Artículo (insumo):",
                 font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(10, 2))
        self.var_art = tk.StringVar()
        ttk.Combobox(card, textvariable=self.var_art,
                     values=list(self.ins_map.keys()),
                     state="readonly", font=("Tahoma", 11), width=26).pack(padx=16)

        fila = tk.Frame(card, bg=COLORES_MODULOS["fondo_contenedor"])
        fila.pack(padx=16, pady=6, fill=tk.X)

        tk.Label(fila, text="Cantidad:",
                 font=("Tahoma", 10, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).grid(row=0, column=0, sticky="e", padx=4)
        self.var_cant = tk.StringVar()
        ttk.Entry(fila, textvariable=self.var_cant,
                  font=("Tahoma", 10), width=8).grid(row=0, column=1, padx=4)

        tk.Label(fila, text="Costo unit.($):",
                 font=("Tahoma", 10, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).grid(row=0, column=2, sticky="e", padx=4)
        self.var_costo = tk.StringVar()
        ttk.Entry(fila, textvariable=self.var_costo,
                  font=("Tahoma", 10), width=8).grid(row=0, column=3, padx=4)

        ttk.Button(card, text="➕ Agregar al detalle",
                   style="Dorado.TButton", width=22,
                   command=self._agregar_item).pack(pady=8)

        ttk.Separator(card, orient="horizontal").pack(fill=tk.X, padx=16, pady=6)

        # Total y guardar
        self.lbl_total = tk.Label(card, text="Total: $0.00",
                                  font=("Tahoma", 14, "bold"),
                                  bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"])
        self.lbl_total.pack(pady=4)

        ttk.Button(card, text="✔ Guardar compra",
                   style="Exito.TButton", width=22,
                   command=self._guardar).pack(pady=8)

    # ── Panel derecho: tabla de artículos de la compra ────────────────────────

    def _panel_articulos(self, parent):
        frame = tk.Frame(parent, bg=COLORES_MODULOS["fondo_contenedor"])
        frame.grid(row=0, column=1, sticky="nsew", pady=4)

        tk.Label(frame, text="Detalle de la compra",
                 font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", pady=(4, 6))

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

        cols = ("articulo", "cantidad", "costo", "subtotal")
        self.tree = ttk.Treeview(frame, columns=cols,
                                 show="headings", style="Carmelita.Treeview")
        for col, texto, ancho in [
            ("articulo",  "Artículo",   220),
            ("cantidad",  "Cantidad",   110),
            ("costo",     "Costo unit.", 110),
            ("subtotal",  "Subtotal",   110),
        ]:
            self.tree.heading(col, text=texto, anchor="center")
            self.tree.column(col, width=ancho, anchor="center")

        sb = ttk.Scrollbar(frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Button(frame, text="Eliminar seleccionado",
                   style="Peligro.TButton",
                   command=self._eliminar_item).pack(anchor="w", pady=6)

    # ── Lógica ────────────────────────────────────────────────────────────────

    def _agregar_item(self):
        nombre = self.var_art.get()
        if not nombre or nombre not in self.ins_map:
            messagebox.showwarning("Sin artículo", "Selecciona un artículo.")
            return
        try:
            cant  = float(self.var_cant.get().replace(",", "."))
            costo = float(self.var_costo.get().replace(",", "."))
            if cant <= 0 or costo <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Datos inválidos",
                                   "Ingresa cantidad y costo mayores a cero.")
            return

        codigo   = self.ins_map[nombre]
        subtotal = round(cant * costo, 2)
        self.items.append({"codigo": codigo, "nombre": nombre,
                           "cantidad": cant, "costo": costo, "subtotal": subtotal})
        self.var_art.set("")
        self.var_cant.set("")
        self.var_costo.set("")
        self._refrescar()

    def _eliminar_item(self):
        for iid in self.tree.selection():
            idx = self.tree.index(iid)
            if idx < len(self.items):
                self.items.pop(idx)
        self._refrescar()

    def _refrescar(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        total = 0.0
        for item in self.items:
            total += item["subtotal"]
            self.tree.insert('', tk.END, values=(
                item["nombre"],
                f"{item['cantidad']:.3f}",
                f"${item['costo']:.2f}",
                f"${item['subtotal']:.2f}",
            ))
        self.lbl_total.config(text=f"Total: ${total:.2f}")

    def _guardar(self):
        if not self.items:
            messagebox.showwarning("Sin artículos",
                                   "Agrega al menos un artículo a la compra.")
            return
        prov_nombre = self.var_prov.get()
        numdoc      = self.var_numdoc.get().strip()
        tipodoc     = self.var_tipodoc.get()

        if not prov_nombre:
            messagebox.showwarning("Sin proveedor", "Selecciona un proveedor.")
            return
        if not numdoc:
            messagebox.showwarning("Sin documento",
                                   "Ingresa el número de documento.")
            return

        id_prov    = self.prov_map[prov_nombre]
        id_usuario = self._get_usuario_id()
        total      = sum(i["subtotal"] for i in self.items)
        ahora      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        confirmar = messagebox.askyesno(
            "Confirmar compra",
            f"Proveedor: {prov_nombre}\n"
            f"Documento: {tipodoc} {numdoc}\n"
            f"Total: ${total:.2f}\n\n"
            "¿Guardar compra y actualizar inventario?"
        )
        if not confirmar:
            return

        try:
            # Insertar compra
            self.cursor.execute("""
                INSERT INTO Compra (numdoc, tipodoc, fecha, importe,
                                   id_proveedor, id_usuario)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (numdoc, tipodoc, ahora, total, id_prov, id_usuario))
            id_compra = self.cursor.lastrowid

            for item in self.items:
                # Detalle compra
                self.cursor.execute("""
                    INSERT INTO DetalleCompra (id_compra, codigo, cantidad, costo)
                    VALUES (?, ?, ?, ?)
                """, (id_compra, item["codigo"], item["cantidad"], item["costo"]))

                # Actualizar existencia
                self.cursor.execute(
                    "SELECT existencia FROM Articulo WHERE codigo = ?",
                    (item["codigo"],))
                exist_ant  = self.cursor.fetchone()[0]
                exist_nueva = exist_ant + item["cantidad"]

                self.cursor.execute(
                    "UPDATE Articulo SET existencia = ?, costo = ? WHERE codigo = ?",
                    (exist_nueva, item["costo"], item["codigo"]))

                # Movimiento inventario
                self.cursor.execute("""
                    INSERT INTO MovimientoInventario
                        (codigo, tipo, cantidad, existencia_anterior,
                         existencia_nueva, referencia, fecha, id_usuario)
                    VALUES (?, 'entrada_compra', ?, ?, ?, ?, ?, ?)
                """, (item["codigo"], item["cantidad"], exist_ant, exist_nueva,
                      f"Compra {tipodoc} {numdoc}", ahora, id_usuario))

            self.db.commit()
            messagebox.showinfo("Compra guardada",
                                f"✅ Compra registrada.\nInventario actualizado.")
            self.items.clear()
            self._refrescar()
            self.var_numdoc.set("")

        except Exception as e:
            self.db.rollback()
            messagebox.showerror("Error", f"No se pudo guardar la compra:\n{e}")


# ══════════════════════════════════════════════════════════════════════════════
#  HISTORIAL DE COMPRAS
# ══════════════════════════════════════════════════════════════════════════════
class ComprasHistorial:
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
        _titulo(self.container, "🚚  Compras — Historial")

        # Filtros
        filtros = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"], padx=10, pady=8)
        filtros.pack(fill=tk.X)

        tk.Label(filtros, text="Proveedor:",
                 font=("Tahoma", 10, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(side=tk.LEFT, padx=(0, 4))
        self.cursor.execute("SELECT nombre FROM Proveedor ORDER BY nombre")
        provs = ["Todos"] + [r[0] for r in self.cursor.fetchall()]
        self.var_prov = tk.StringVar(value="Todos")
        ttk.Combobox(filtros, textvariable=self.var_prov, values=provs,
                     state="readonly", width=20,
                     font=("Tahoma", 10)).pack(side=tk.LEFT, padx=4)

        tk.Label(filtros, text="Desde:",
                 font=("Tahoma", 10, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(side=tk.LEFT, padx=(12, 4))
        self.var_desde = tk.StringVar()
        ttk.Entry(filtros, textvariable=self.var_desde,
                  width=12, font=("Tahoma", 10)).pack(side=tk.LEFT, padx=4)
        tk.Label(filtros, text="(AAAA-MM-DD)",
                 font=("Tahoma", 8), bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_error"]).pack(side=tk.LEFT)

        tk.Label(filtros, text="Hasta:",
                 font=("Tahoma", 10, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(side=tk.LEFT, padx=(8, 4))
        self.var_hasta = tk.StringVar()
        ttk.Entry(filtros, textvariable=self.var_hasta,
                  width=12, font=("Tahoma", 10)).pack(side=tk.LEFT, padx=4)
        tk.Label(filtros, text="(AAAA-MM-DD)",
                 font=("Tahoma", 8), bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_error"]).pack(side=tk.LEFT)

        ttk.Button(filtros, text="Buscar",
                   style="Dorado.TButton",
                   command=self._cargar).pack(side=tk.LEFT, padx=12)

        # Tabla compras
        tf = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        style = ttk.Style()
        style.theme_use('clam')
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

        cols = ("id", "proveedor", "tipodoc", "numdoc", "fecha", "total", "usuario")
        self.tree = ttk.Treeview(tf, columns=cols,
                                 show="headings", style="Carmelita.Treeview")
        for col, texto, ancho in [
            ("id",        "#",          50),
            ("proveedor", "Proveedor",  180),
            ("tipodoc",   "Tipo doc.",   90),
            ("numdoc",    "Núm. doc.",  120),
            ("fecha",     "Fecha",      150),
            ("total",     "Total",       90),
            ("usuario",   "Registró",   120),
        ]:
            self.tree.heading(col, text=texto, anchor="center")
            self.tree.column(col, width=ancho, anchor="center")

        sb = ttk.Scrollbar(tf, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.LEFT, fill=tk.Y)

        # Detalle al seleccionar
        self.tree.bind("<<TreeviewSelect>>", self._mostrar_detalle)

        # Tabla detalle
        tk.Label(self.container, text="Detalle de la compra seleccionada:",
                 font=("Tahoma", 10, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=12, pady=(6, 2))

        df = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        df.pack(fill=tk.X, padx=10, pady=4)

        cols2 = ("articulo", "cantidad", "costo", "subtotal")
        self.tree_det = ttk.Treeview(df, columns=cols2,
                                     show="headings", style="Carmelita.Treeview",
                                     height=5)
        for col, texto, ancho in [
            ("articulo",  "Artículo",   220),
            ("cantidad",  "Cantidad",   110),
            ("costo",     "Costo unit.", 110),
            ("subtotal",  "Subtotal",   110),
        ]:
            self.tree_det.heading(col, text=texto, anchor="center")
            self.tree_det.column(col, width=ancho, anchor="center")
        self.tree_det.pack(fill=tk.X)

        self._cargar()

    def _cargar(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        query = """
            SELECT c.id_compra, p.nombre, c.tipodoc, c.numdoc,
                   c.fecha, c.importe, u.nombre
            FROM Compra c
            JOIN Proveedor p ON p.id_proveedor = c.id_proveedor
            JOIN Usuarios  u ON u.id_usuario   = c.id_usuario
            WHERE 1=1
        """
        params = []
        prov = self.var_prov.get()
        if prov != "Todos":
            query += " AND p.nombre = ?"
            params.append(prov)
        desde = self.var_desde.get().strip()
        hasta = self.var_hasta.get().strip()
        if desde:
            query += " AND c.fecha >= ?"
            params.append(desde)
        if hasta:
            query += " AND c.fecha <= ?"
            params.append(hasta + " 23:59:59")
        query += " ORDER BY c.fecha DESC"

        self.cursor.execute(query, params)
        for row in self.cursor.fetchall():
            id_c, prov_n, tipo, num, fecha, total, usr = row
            self.tree.insert('', tk.END, iid=str(id_c), values=(
                id_c, prov_n, tipo, num, fecha, f"${total:.2f}", usr))

    def _mostrar_detalle(self, event=None):
        for iid in self.tree_det.get_children():
            self.tree_det.delete(iid)
        sel = self.tree.selection()
        if not sel:
            return
        id_compra = int(sel[0])
        self.cursor.execute("""
            SELECT a.nombre, d.cantidad, d.costo, (d.cantidad * d.costo)
            FROM DetalleCompra d
            JOIN Articulo a ON a.codigo = d.codigo
            WHERE d.id_compra = ?
        """, (id_compra,))
        for nombre, cant, costo, sub in self.cursor.fetchall():
            self.tree_det.insert('', tk.END, values=(
                nombre, f"{cant:.3f}", f"${costo:.2f}", f"${sub:.2f}"))


# ══════════════════════════════════════════════════════════════════════════════
#  PROVEEDORES
# ══════════════════════════════════════════════════════════════════════════════
class ComprasProveedores:
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
        _titulo(self.container, "🚚  Compras — Proveedores")

        cuerpo = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        cuerpo.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.columnconfigure(1, weight=2)
        cuerpo.rowconfigure(0, weight=1)

        self._form(cuerpo)
        self._tabla(cuerpo)

    def _form(self, parent):
        self.card = tk.LabelFrame(parent, text="  Nuevo proveedor  ",
                                  bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"],
                                  font=("Tahoma", 10, "bold"),
                                  bd=2, relief="groove")
        self.card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)

        campos = [
            ("Nombre:",         "var_nombre",  True),
            ("Teléfono:",       "var_tel",     False),
            ("Representante:",  "var_rep",     False),
        ]
        for texto, var_name, requerido in campos:
            lbl = texto + (" *" if requerido else "")
            tk.Label(self.card, text=lbl,
                     font=("Tahoma", 11, "bold"),
                     bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(10, 2))
            var = tk.StringVar()
            setattr(self, var_name, var)
            ttk.Entry(self.card, textvariable=var,
                      font=("Tahoma", 11), width=26).pack(padx=16)

        tk.Label(self.card, text="* Campo obligatorio",
                 font=("Tahoma", 8), bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_error"]).pack(anchor="w", padx=16)

        btn_row = tk.Frame(self.card, bg=COLORES_MODULOS["fondo_contenedor"])
        btn_row.pack(pady=14)
        ttk.Button(btn_row, text="Guardar",
                   style="Exito.TButton", width=12,
                   command=self._guardar).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_row, text="Limpiar",
                   style="Gris.TButton", width=12,
                   command=self._limpiar_form).pack(side=tk.LEFT, padx=6)

        ttk.Separator(self.card, orient="horizontal").pack(fill=tk.X, padx=16, pady=6)

        # Edición del proveedor seleccionado
        tk.Label(self.card, text="Selecciona un proveedor de la tabla\npara editar o ver sus datos.",
                 font=("Tahoma", 9, "italic"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_error"]).pack(padx=16, pady=4)

        ttk.Button(self.card, text="✏ Actualizar seleccionado",
                   style="Dorado.TButton", width=24,
                   command=self._actualizar).pack(pady=4)

    def _tabla(self, parent):
        frame = tk.Frame(parent, bg=COLORES_MODULOS["fondo_contenedor"])
        frame.grid(row=0, column=1, sticky="nsew", pady=4)

        tk.Label(frame, text="Proveedores registrados",
                 font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", pady=(4, 6))

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Carmelita.Treeview",
                        background="#FFFFFF", fieldbackground="#FFFFFF",
                        foreground=COLORES_MODULOS["texto_principal"], rowheight=28,
                        font=("Tahoma", 11))
        style.configure("Carmelita.Treeview.Heading",
                        background=COLORES_MODULOS["tree_heading_bg"], foreground=COLORES_MODULOS["tree_heading_fg"],
                        font=("Tahoma", 11, "bold"))
        style.map("Carmelita.Treeview",
                  background=[("selected", COLORES_MODULOS["tree_selected_bg"])],
                  foreground=[("selected", COLORES_MODULOS["tree_selected_fg"])])

        cols = ("id", "nombre", "telefono", "representante")
        self.tree = ttk.Treeview(frame, columns=cols,
                                 show="headings", style="Carmelita.Treeview")
        for col, texto, ancho in [
            ("id",            "#",              50),
            ("nombre",        "Nombre",        200),
            ("telefono",      "Teléfono",      130),
            ("representante", "Representante", 180),
        ]:
            self.tree.heading(col, text=texto, anchor="center")
            self.tree.column(col, width=ancho, anchor="center")

        sb = ttk.Scrollbar(frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.LEFT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._cargar_en_form)
        self._cargar_tabla()

    def _cargar_tabla(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.cursor.execute(
            "SELECT id_proveedor, nombre, telefono, representante FROM Proveedor ORDER BY nombre")
        for row in self.cursor.fetchall():
            self.tree.insert('', tk.END, iid=str(row[0]), values=row)

    def _cargar_en_form(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        self.var_nombre.set(vals[1])
        self.var_tel.set(vals[2] or "")
        self.var_rep.set(vals[3] or "")
        self.card.config(text="  Editar proveedor  ")

    def _limpiar_form(self):
        self.var_nombre.set("")
        self.var_tel.set("")
        self.var_rep.set("")
        self.card.config(text="  Nuevo proveedor  ")

    def _guardar(self):
        nombre = self.var_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Campo vacío", "El nombre del proveedor es obligatorio.")
            return
        self.cursor.execute(
            "INSERT INTO Proveedor (nombre, telefono, representante) VALUES (?,?,?)",
            (nombre, self.var_tel.get().strip(), self.var_rep.get().strip()))
        self.db.commit()
        messagebox.showinfo("Guardado", f"✅ Proveedor '{nombre}' registrado.")
        self._limpiar_form()
        self._cargar_tabla()

    def _actualizar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Selecciona un proveedor de la tabla para actualizar.")
            return
        nombre = self.var_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Campo vacío", "El nombre no puede estar vacío.")
            return
        id_prov = int(sel[0])
        self.cursor.execute("""
            UPDATE Proveedor SET nombre=?, telefono=?, representante=?
            WHERE id_proveedor=?
        """, (nombre, self.var_tel.get().strip(),
              self.var_rep.get().strip(), id_prov))
        self.db.commit()
        messagebox.showinfo("Actualizado", f"✅ Proveedor actualizado correctamente.")
        self._limpiar_form()
        self._cargar_tabla()