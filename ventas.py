import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import conexion
from botones import configurar_estilos, COLORES_MODULOS

CODIGO_TORTILLA = "TORTILLA001"


class VentaApp:
    def __init__(self, container, usuario_nombre=None):
        self.container      = container
        self.usuario_nombre = usuario_nombre or "Trabajador General"
        self.db             = conexion.conectar()
        self.cursor         = self.db.cursor()
        self.usuario_id     = self._get_usuario_id(self.usuario_nombre)
        self.id_turno       = self._get_turno_abierto()
        self.precio_por_kg  = self._get_precio_tortilla()
        self.items          = []   # [{nombre, kg, subtotal}]

        configurar_estilos(self.container)
        self._build_ui()

    # ── BD helpers ────────────────────────────────────────────────────────────

    def _get_usuario_id(self, nombre):
        try:
            self.cursor.execute(
                "SELECT id_usuario FROM Usuarios WHERE nombre = ?", (nombre,))
            row = self.cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo obtener ID de usuario: {e}")
            return None

    def _get_turno_abierto(self):
        try:
            self.cursor.execute(
                "SELECT id_turno FROM Turno WHERE estado = 'abierto' LIMIT 1")
            row = self.cursor.fetchone()
            return row[0] if row else None
        except:
            return None

    def _get_precio_tortilla(self):
        try:
            self.cursor.execute(
                "SELECT precio FROM Articulo WHERE codigo = ?", (CODIGO_TORTILLA,))
            row = self.cursor.fetchone()
            return float(row[0]) if row else 18.0
        except:
            return 18.0

    def _limpiar(self):
        for w in self.container.winfo_children():
            w.destroy()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._limpiar()
        self.container.configure(bg=COLORES_MODULOS['fondo_contenedor'])

        # Título
        title = tk.Frame(self.container, bg=COLORES_MODULOS['encabezado_bg'], padx=10, pady=6)
        title.pack(fill=tk.X)
        tk.Label(title, text="🛒  VENTAS",
                 font=("Tahoma", 14, "bold"),
                 fg=COLORES_MODULOS['encabezado_fg_claro'], bg=COLORES_MODULOS['encabezado_bg']).pack(side=tk.LEFT)
        tk.Label(title, text=f"Precio: ${self.precio_por_kg:.2f} / kg",
                 font=("Tahoma", 11),
                 fg=COLORES_MODULOS['encabezado_fg_accent'], bg=COLORES_MODULOS['encabezado_bg']).pack(side=tk.RIGHT)

        # Cuerpo en dos columnas
        cuerpo = tk.Frame(self.container, bg=COLORES_MODULOS['fondo_contenedor'])
        cuerpo.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        cuerpo.columnconfigure(0, weight=3)
        cuerpo.columnconfigure(1, weight=2)
        cuerpo.rowconfigure(0, weight=1)

        self._panel_ticket(cuerpo)
        self._panel_cobro(cuerpo)

    def _panel_ticket(self, parent):
        """Columna izquierda: entrada de kg/precio + tabla del ticket."""
        left = tk.Frame(parent, bg=COLORES_MODULOS['fondo_contenedor'])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # ── Entrada ───────────────────────────────────────────────────────────
        entrada = tk.LabelFrame(left, text="  Agregar venta  ",
                                bg=COLORES_MODULOS['fondo_contenedor'], fg=COLORES_MODULOS['texto_principal'],
                                font=("Tahoma", 10, "bold"),
                                bd=2, relief="groove")
        entrada.pack(fill=tk.X, pady=(0, 8))

        fila = tk.Frame(entrada, bg=COLORES_MODULOS['fondo_contenedor'])
        fila.pack(padx=10, pady=10)

        # Kilogramos
        tk.Label(fila, text="Kilogramos:",
                 font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS['fondo_contenedor'], fg=COLORES_MODULOS['texto_principal']).grid(row=0, column=0, sticky="e", padx=6, pady=4)
        self.var_kg = tk.StringVar()
        self.entry_kg = ttk.Entry(fila, textvariable=self.var_kg,
                                  font=("Tahoma", 12), width=10)
        self.entry_kg.grid(row=0, column=1, padx=6, pady=4)
        self.entry_kg.bind("<Return>",   lambda e: (self._calc_desde_kg(), self.entry_precio.focus()))
        self.entry_kg.bind("<FocusOut>", lambda e: self._calc_desde_kg())

        tk.Label(fila, text="↔", font=("Tahoma", 14),
                 bg=COLORES_MODULOS['fondo_contenedor'], fg=COLORES_MODULOS['encabezado_bg']).grid(row=0, column=2, padx=4)

        # Precio
        tk.Label(fila, text="Precio ($):",
                 font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS['fondo_contenedor'], fg=COLORES_MODULOS['texto_principal']).grid(row=0, column=3, sticky="e", padx=6, pady=4)
        self.var_precio_item = tk.StringVar()
        self.entry_precio = ttk.Entry(fila, textvariable=self.var_precio_item,
                                      font=("Tahoma", 12), width=10)
        self.entry_precio.grid(row=0, column=4, padx=6, pady=4)
        self.entry_precio.bind("<FocusOut>", lambda e: self._calc_desde_precio())
        self.entry_precio.bind("<Return>",   lambda e: (self._calc_desde_precio(), self._agregar()))

        ttk.Button(fila, text="➕ Agregar",
                   style="Dorado.TButton",
                   command=self._agregar).grid(row=0, column=5, padx=16)

        tk.Label(entrada,
                 text="Escribe kg → se calcula el precio  |  Escribe precio → se calculan los kg",
                 font=("Tahoma", 8), bg=COLORES_MODULOS['fondo_contenedor'], fg=COLORES_MODULOS['encabezado_bg']).pack(pady=(0, 6))

        # ── Tabla ticket ──────────────────────────────────────────────────────
        tabla_frame = tk.Frame(left, bg=COLORES_MODULOS['fondo_contenedor'])
        tabla_frame.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Carmelita.Treeview",
                        background=COLORES_MODULOS['fondo_card'], fieldbackground=COLORES_MODULOS['fondo_card'],
                        foreground=COLORES_MODULOS['texto_principal'], rowheight=30,
                        font=("Tahoma", 11))
        style.configure("Carmelita.Treeview.Heading",
                        background=COLORES_MODULOS['tree_heading_bg'], foreground=COLORES_MODULOS['tree_heading_fg'],
                        font=("Tahoma", 11, "bold"))
        style.map("Carmelita.Treeview",
                  background=[("selected", COLORES_MODULOS['tree_selected_bg'])],
                  foreground=[("selected", COLORES_MODULOS['tree_selected_fg'])])

        cols = ("producto", "kilogramos", "precio")
        self.tree = ttk.Treeview(tabla_frame, columns=cols,
                                 show="headings", style="Carmelita.Treeview")
        for col, texto, ancho in [
            ("producto",   "Producto",   200),
            ("kilogramos", "Kilogramos", 140),
            ("precio",     "Precio",     140),
        ]:
            self.tree.heading(col, text=texto, anchor="center")
            self.tree.column(col, width=ancho, anchor="center")

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Scrollbar(tabla_frame, command=self.tree.yview).pack(side=tk.LEFT, fill=tk.Y)
        self.tree.configure(yscrollcommand=lambda f, s: None)

        # Botones ticket
        btn_row = tk.Frame(left, bg=COLORES_MODULOS['fondo_contenedor'])
        btn_row.pack(fill=tk.X, pady=4)
        ttk.Button(btn_row, text="Eliminar seleccionado",
                   style="Peligro.TButton",
                   command=self._eliminar).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Vaciar ticket",
                   style="Peligro.TButton",
                   command=self._vaciar).pack(side=tk.LEFT, padx=4)

        self.entry_kg.focus()

    def _panel_cobro(self, parent):
        """Columna derecha: total, monto recibido, cambio y botón cobrar."""
        right = tk.Frame(parent, bg=COLORES_MODULOS['fondo_contenedor'])
        right.grid(row=0, column=1, sticky="nsew")

        cobro = tk.LabelFrame(right, text="  Cobro  ",
                               bg=COLORES_MODULOS['fondo_contenedor'], fg=COLORES_MODULOS['texto_principal'],
                               font=("Tahoma", 10, "bold"),
                               bd=2, relief="groove")
        cobro.pack(fill=tk.BOTH, expand=True)

        # Total
        tk.Label(cobro, text="Total a cobrar:",
                 font=("Tahoma", 11), bg=COLORES_MODULOS['fondo_contenedor'], fg=COLORES_MODULOS['texto_principal']).pack(pady=(20, 4))
        self.lbl_total = tk.Label(cobro, text="$0.00",
                                  font=("Tahoma", 28, "bold"),
                                  bg=COLORES_MODULOS['fondo_contenedor'], fg=COLORES_MODULOS['texto_principal'])
        self.lbl_total.pack()

        ttk.Separator(cobro, orient="horizontal").pack(fill=tk.X, padx=20, pady=15)

        # Monto recibido
        tk.Label(cobro, text="Monto recibido ($):",
                 font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS['fondo_contenedor'], fg=COLORES_MODULOS['texto_principal']).pack(pady=(0, 4))
        self.var_recibido = tk.StringVar()
        self.entry_recibido = ttk.Entry(cobro, textvariable=self.var_recibido,
                                        font=("Tahoma", 14), width=14,
                                        justify="center")
        self.entry_recibido.pack()
        self.var_recibido.trace_add("write", lambda *a: self._calcular_cambio())
        self.entry_recibido.bind("<Return>", lambda e: self._cobrar())

        # Cambio
        tk.Label(cobro, text="Cambio:",
                 font=("Tahoma", 11), bg=COLORES_MODULOS['fondo_contenedor'], fg=COLORES_MODULOS['texto_principal']).pack(pady=(16, 4))
        self.lbl_cambio = tk.Label(cobro, text="$0.00",
                                   font=("Tahoma", 22, "bold"),
                                   bg=COLORES_MODULOS['fondo_contenedor'], fg=COLORES_MODULOS['texto_exito'])
        self.lbl_cambio.pack()

        ttk.Separator(cobro, orient="horizontal").pack(fill=tk.X, padx=20, pady=15)

        # Botones
        ttk.Button(cobro, text="✔  Cobrar",
                   style="Exito.TButton", width=18,
                   command=self._cobrar).pack(pady=6)
        ttk.Button(cobro, text="✖  Cancelar venta",
                   style="Peligro.TButton", width=18,
                   command=self._vaciar).pack(pady=6)

    # ── Lógica kg ↔ precio ────────────────────────────────────────────────────

    def _calc_desde_kg(self):
        try:
            kg = float(self.var_kg.get().replace(",", "."))
            self.var_precio_item.set(f"{kg * self.precio_por_kg:.2f}")
        except ValueError:
            pass

    def _calc_desde_precio(self):
        try:
            precio = float(self.var_precio_item.get().replace(",", "."))
            self.var_kg.set(f"{precio / self.precio_por_kg:.3f}")
        except ValueError:
            pass

    def _agregar(self):
        self._calc_desde_kg()
        try:
            kg     = float(self.var_kg.get().replace(",", "."))
            precio = float(self.var_precio_item.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Datos incompletos",
                                   "Escribe los kilogramos o el precio antes de agregar.")
            return
        if kg <= 0 or precio <= 0:
            messagebox.showwarning("Valor inválido", "Los valores deben ser mayores a cero.")
            return

        subtotal = round(precio, 2)
        for item in self.items:
            if item["nombre"] == "Tortilla":
                item["kg"] += kg
                item["subtotal"] = round(item["subtotal"] + subtotal, 2)
                break
        else:
            self.items.append({"nombre": "Tortilla", "kg": kg, "subtotal": subtotal})

        self.var_kg.set("")
        self.var_precio_item.set("")
        self.entry_kg.focus()
        self._refrescar()

    def _refrescar(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        total = 0.0
        for item in self.items:
            total += item["subtotal"]
            self.tree.insert('', tk.END, values=(
                item["nombre"],
                f"{item['kg']:.3f} kg",
                f"${item['subtotal']:.2f}",
            ))
        self.lbl_total.config(text=f"${total:.2f}")
        self._calcular_cambio()

    def _eliminar(self):
        seleccion = self.tree.selection()
        if not seleccion:
            return
        indices = sorted([self.tree.index(i) for i in seleccion], reverse=True)
        for idx in indices:
            if idx < len(self.items):
                self.items.pop(idx)
        self._refrescar()

    def _vaciar(self):
        self.items.clear()
        self.var_recibido.set("")
        self._refrescar()

    # ── Cobro ─────────────────────────────────────────────────────────────────

    def _calcular_cambio(self):
        try:
            total    = sum(i["subtotal"] for i in self.items)
            recibido = float(self.var_recibido.get().replace(",", "."))
            cambio   = recibido - total
            color    = COLORES_MODULOS['texto_exito'] if cambio >= 0 else COLORES_MODULOS['texto_error']
            self.lbl_cambio.config(text=f"${max(cambio, 0):.2f}", fg=color)
        except ValueError:
            self.lbl_cambio.config(text="$0.00", fg=COLORES_MODULOS['texto_exito'])

    def _cobrar(self):
        if not self.items:
            messagebox.showwarning("Ticket vacío", "Agrega al menos una venta antes de cobrar.")
            return

        total = sum(i["subtotal"] for i in self.items)

        try:
            recibido = float(self.var_recibido.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Monto inválido", "Ingresa el monto recibido del cliente.")
            return

        if recibido < total:
            messagebox.showwarning("Monto insuficiente",
                                   f"El monto recibido (${recibido:.2f}) es menor al total (${total:.2f}).")
            return

        cambio = round(recibido - total, 2)

        try:
            self._guardar_venta(total, recibido, cambio)
            messagebox.showinfo("Venta registrada",
                                f"✔ Venta completada\n\nTotal: ${total:.2f}\nRecibido: ${recibido:.2f}\nCambio: ${cambio:.2f}")
            self._vaciar()
        except Exception as e:
            messagebox.showerror("Error al guardar", f"No se pudo registrar la venta:\n{e}")

    def _guardar_venta(self, total, recibido, cambio):
        ahora  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fecha_solo = datetime.now().strftime("%Y-%m-%d")

        # Generar folio: TRT-00001
        self.cursor.execute("SELECT COUNT(*) FROM Venta")
        n = self.cursor.fetchone()[0] + 1
        folio = f"TRT-{n:05d}"

        self.cursor.execute("""
            INSERT INTO Venta (folio, fecha, importe, monto_recibido, cambio,
                               estado, id_turno, id_usuario)
            VALUES (?, ?, ?, ?, ?, 'completada', ?, ?)
        """, (folio, ahora, total, recibido, cambio, self.id_turno, self.usuario_id))

        id_venta = self.cursor.lastrowid

        for item in self.items:
            self.cursor.execute("""
                INSERT INTO DetalleVenta (id_venta, codigo, cantidad, precio)
                VALUES (?, ?, ?, ?)
            """, (id_venta, CODIGO_TORTILLA, item["kg"], item["subtotal"]))

            # Registrar movimiento de inventario
            self.cursor.execute(
                "SELECT existencia FROM Articulo WHERE codigo = ?", (CODIGO_TORTILLA,))
            exist_ant = self.cursor.fetchone()[0]
            exist_nueva = exist_ant - item["kg"]

            self.cursor.execute("""
                INSERT INTO MovimientoInventario
                    (codigo, tipo, cantidad, existencia_anterior,
                     existencia_nueva, referencia, fecha, id_usuario)
                VALUES (?, 'salida_venta', ?, ?, ?, ?, ?, ?)
            """, (CODIGO_TORTILLA, -item["kg"], exist_ant, exist_nueva,
                  f"Venta {folio}", ahora, self.usuario_id))

            self.cursor.execute(
                "UPDATE Articulo SET existencia = ? WHERE codigo = ?",
                (exist_nueva, CODIGO_TORTILLA))

        self.db.commit()


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Ventas — Tortillería Carmelita')
    root.state('zoomed')
    VentaApp(root, usuario_nombre='Administrador')
    root.mainloop()