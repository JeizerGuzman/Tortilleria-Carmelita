import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import conexion
from botones import configurar_estilos, COLORES_MODULOS

# ── Helper compartido ─────────────────────────────────────────────────────────

def _titulo(container, texto):
    f = tk.Frame(container, bg=COLORES_MODULOS['encabezado_bg'], padx=10, pady=6)
    f.pack(fill=tk.X)
    tk.Label(f, text=texto, font=("Tahoma", 14, "bold"),
             fg=COLORES_MODULOS['encabezado_fg_claro'], bg=COLORES_MODULOS['encabezado_bg']).pack(side=tk.LEFT)
    return f

def _estilo_tree():
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

def _card_dato(parent, etiqueta, valor, color_valor=COLORES_MODULOS["texto_principal"]):
    """Tarjeta pequeña para mostrar un dato resumido."""
    f = tk.Frame(parent, bg=COLORES_MODULOS["fondo_card"], bd=1, relief="groove",
                 padx=16, pady=10)
    f.pack(side=tk.LEFT, padx=8, pady=4)
    tk.Label(f, text=etiqueta, font=("Tahoma", 9),
             bg=COLORES_MODULOS["fondo_card"], fg=COLORES_MODULOS["texto_error"]).pack()
    tk.Label(f, text=valor, font=("Tahoma", 15, "bold"),
             bg=COLORES_MODULOS["fondo_card"], fg=color_valor).pack()


# ══════════════════════════════════════════════════════════════════════════════
#  VENTAS DEL DÍA 
# ══════════════════════════════════════════════════════════════════════════════
class ReportesDia:
    def __init__(self, container, usuario=""):
        self.container = container
        self.usuario   = usuario          # nombre del usuario activo (para cancelaciones)
        self.db        = conexion.conectar()
        self.cursor    = self.db.cursor()
        configurar_estilos(container)
        self._build()

    def _build(self):
        for w in self.container.winfo_children():
            w.destroy()
        self.container.configure(bg=COLORES_MODULOS["fondo_contenedor"])

        title_frame = _titulo(self.container, "📊  Reportes — Ventas del día")
        ttk.Button(title_frame, text="🔄 Actualizar",
                   style="Cafe.TButton",
                   command=self._build).pack(side=tk.RIGHT, padx=6)
        ttk.Button(title_frame, text="❌ Cancelar ticket",
                   style="Peligro.TButton",
                   command=self._cancelar_ticket).pack(side=tk.RIGHT, padx=6)

        hoy = date.today().isoformat()

        # ── Resumen del día ───────────────────────────────────────────────────
        self.cursor.execute("""
            SELECT
                COUNT(*),
                COALESCE(SUM(CASE WHEN estado='completada' THEN importe ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN estado='cancelada'  THEN 1 ELSE 0 END), 0)
            FROM Venta
            WHERE DATE(fecha) = ?
        """, (hoy,))
        total_v, importe, canceladas = self.cursor.fetchone()
        completadas = total_v - canceladas

        # Turno activo
        self.cursor.execute("""
            SELECT t.fondo_inicial, t.fecha_apertura, u.nombre, t.id_turno
            FROM Turno t
            JOIN Usuarios u ON u.id_usuario = t.id_usuario_apertura
            WHERE t.estado = 'abierto' LIMIT 1
        """)
        turno = self.cursor.fetchone()

        # Movimientos de caja del turno activo
        entradas = salidas = 0.0
        if turno:
            id_turno = turno[3]
            self.cursor.execute("""
                SELECT COALESCE(SUM(monto),0) FROM MovimientoCaja
                WHERE id_turno=? AND tipo='entrada'
            """, (id_turno,))
            entradas = self.cursor.fetchone()[0]
            self.cursor.execute("""
                SELECT COALESCE(SUM(monto),0) FROM MovimientoCaja
                WHERE id_turno=? AND tipo='salida'
            """, (id_turno,))
            salidas = self.cursor.fetchone()[0]

        # Tarjetas resumen
        resumen = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        resumen.pack(fill=tk.X, padx=10, pady=10)

        _card_dato(resumen, "Ventas completadas", str(completadas),   COLORES_MODULOS['texto_exito'])
        _card_dato(resumen, "Ventas canceladas",  str(canceladas),    COLORES_MODULOS['texto_error'])
        _card_dato(resumen, "Total recaudado",    f"${importe:.2f}",  COLORES_MODULOS['texto_principal'])
        _card_dato(resumen, "Entradas extra",     f"${entradas:.2f}", COLORES_MODULOS['texto_exito'])
        _card_dato(resumen, "Gastos / salidas",   f"${salidas:.2f}",  COLORES_MODULOS['texto_error'])

        if turno:
            fondo, apertura, quien, _ = turno
            efectivo_est = fondo + importe + entradas - salidas
            _card_dato(resumen, "Efectivo esperado", f"${efectivo_est:.2f}", COLORES_MODULOS['texto_error'])

        # Info del turno
        if turno:
            fondo, apertura, quien, _ = turno
            info = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
            info.pack(fill=tk.X, padx=18, pady=2)
            tk.Label(info,
                     text=f"Turno abierto por {quien}  |  Apertura: {apertura}  |  Fondo inicial: ${fondo:.2f}",
                     font=("Tahoma", 9, "italic"),
                     bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_error"]).pack(side=tk.LEFT)
        else:
            tk.Label(self.container,
                     text="ℹ️  No hay turno abierto en este momento.",
                     font=("Tahoma", 9, "italic"),
                     bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_error"]).pack(anchor="w", padx=18)

        ttk.Separator(self.container, orient="horizontal").pack(
            fill=tk.X, padx=10, pady=8)

        # ── Tabla de ventas del día ───────────────────────────────────────────
        tk.Label(self.container, text=f"Ventas del {hoy}",
                 font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=12)

        tf = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        _estilo_tree()

        cols = ("folio", "hora", "kg_total", "importe",
                "recibido", "cambio", "estado", "usuario")
        self.tree = ttk.Treeview(tf, columns=cols,
                                 show="headings", style="Carmelita.Treeview")
        for col, texto, ancho in [
            ("folio",    "Folio",     90),
            ("hora",     "Hora",      80),
            ("kg_total", "Kg total",  90),
            ("importe",  "Total",     90),
            ("recibido", "Recibido",  90),
            ("cambio",   "Cambio",    80),
            ("estado",   "Estado",    90),
            ("usuario",  "Atendió",  110),
        ]:
            self.tree.heading(col, text=texto, anchor="center")
            self.tree.column(col, width=ancho, anchor="center")

        self.tree.tag_configure("cancelada",  foreground=COLORES_MODULOS['texto_error'],
                                background=COLORES_MODULOS['tag_alerta_bg'])
        self.tree.tag_configure("completada", foreground=COLORES_MODULOS["texto_exito"])

        sb = ttk.Scrollbar(tf, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.LEFT, fill=tk.Y)

        self._cargar_tabla(hoy)

    def _cargar_tabla(self, hoy=None):
        if hoy is None:
            hoy = date.today().isoformat()
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        self.cursor.execute("""
            SELECT v.id_venta, v.folio, v.fecha, v.importe,
                   v.monto_recibido, v.cambio, v.estado, u.nombre,
                   COALESCE((
                       SELECT SUM(d.cantidad)
                       FROM DetalleVenta d WHERE d.id_venta = v.id_venta
                   ), 0)
            FROM Venta v
            JOIN Usuarios u ON u.id_usuario = v.id_usuario
            WHERE DATE(v.fecha) = ?
            ORDER BY v.fecha DESC
        """, (hoy,))
        for id_v, folio, fecha, imp, rec, camb, estado, usr, kg in self.cursor.fetchall():
            hora = fecha[11:19] if len(fecha) > 10 else "—"
            tag  = "cancelada" if estado == "cancelada" else "completada"
            # Guardamos id_venta como iid para recuperarlo al cancelar
            self.tree.insert('', tk.END, iid=str(id_v), tags=(tag,), values=(
                folio, hora,
                f"{kg:.3f} kg",
                f"${imp:.2f}",
                f"${rec:.2f}",
                f"${camb:.2f}",
                estado.capitalize(),
                usr,
            ))

    # ── Cancelación de ticket ─────────────────────────────────────────────────

    def _cancelar_ticket(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Selecciona una venta de la lista para cancelarla.")
            return

        id_venta = int(sel[0])

        # Verificar que no esté ya cancelada
        self.cursor.execute(
            "SELECT folio, importe, estado FROM Venta WHERE id_venta=?", (id_venta,))
        row = self.cursor.fetchone()
        if not row:
            return
        folio, importe, estado = row

        if estado == "cancelada":
            messagebox.showwarning("Ya cancelada",
                                   f"El ticket {folio} ya fue cancelado anteriormente.")
            return

        # Ventana de confirmación con motivo
        self._ventana_cancelacion(id_venta, folio, importe)

    def _ventana_cancelacion(self, id_venta, folio, importe):
        """Abre una ventana emergente para capturar el motivo de cancelación."""
        win = tk.Toplevel(self.container)
        win.title("Cancelar ticket")
        win.configure(bg=COLORES_MODULOS["fondo_contenedor"])
        win.resizable(False, False)
        win.grab_set()   # bloquea la ventana principal mientras está abierta

        # Centrar la ventana
        win.update_idletasks()
        w, h = 420, 280
        x = (win.winfo_screenwidth()  // 2) - (w // 2)
        y = (win.winfo_screenheight() // 2) - (h // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")

        tk.Label(win, text="❌  Cancelar ticket",
                 font=("Tahoma", 13, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_error"]).pack(pady=(18, 4))

        tk.Label(win,
                 text=f"Folio: {folio}     Total: ${importe:.2f}",
                 font=("Tahoma", 10),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack()

        tk.Label(win,
                 text="Esta acción no se puede deshacer.\nEl stock de los artículos será restaurado.",
                 font=("Tahoma", 9, "italic"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_error"]).pack(pady=4)

        tk.Label(win, text="Motivo de cancelación (obligatorio):",
                 font=("Tahoma", 10, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=20, pady=(8, 2))

        var_motivo = tk.StringVar()
        ttk.Entry(win, textvariable=var_motivo,
                  font=("Tahoma", 11), width=34).pack(padx=20)

        def confirmar():
            motivo = var_motivo.get().strip()
            if not motivo:
                messagebox.showwarning("Motivo vacío",
                                       "Debes escribir el motivo de la cancelación.",
                                       parent=win)
                return
            win.destroy()
            self._ejecutar_cancelacion(id_venta, motivo)

        frame_btns = tk.Frame(win, bg=COLORES_MODULOS["fondo_contenedor"])
        frame_btns.pack(pady=16)
        ttk.Button(frame_btns, text="Confirmar cancelación",
                   style="Peligro.TButton", width=22,
                   command=confirmar).pack(side=tk.LEFT, padx=8)
        ttk.Button(frame_btns, text="No cancelar",
                   style="Cafe.TButton", width=14,
                   command=win.destroy).pack(side=tk.LEFT, padx=8)

    def _ejecutar_cancelacion(self, id_venta, motivo):
        """Aplica la cancelación en la BD y restaura el inventario."""
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Obtener id del usuario activo
        self.cursor.execute(
            "SELECT id_usuario FROM Usuarios WHERE nombre=?", (self.usuario,))
        row = self.cursor.fetchone()
        id_cancela = row[0] if row else None

        try:
            # 1. Marcar la venta como cancelada
            self.cursor.execute("""
                UPDATE Venta
                SET estado='cancelada', motivo_cancel=?, id_cancela=?
                WHERE id_venta=?
            """, (motivo, id_cancela, id_venta))

            # 2. Restaurar stock de cada artículo del detalle
            self.cursor.execute("""
                SELECT codigo, cantidad FROM DetalleVenta WHERE id_venta=?
            """, (id_venta,))
            detalles = self.cursor.fetchall()

            for codigo, cantidad in detalles:
                self.cursor.execute(
                    "SELECT existencia FROM Articulo WHERE codigo=?", (codigo,))
                exist_ant = self.cursor.fetchone()[0]
                exist_nueva = exist_ant + cantidad

                # Actualizar existencia
                self.cursor.execute(
                    "UPDATE Articulo SET existencia=? WHERE codigo=?",
                    (exist_nueva, codigo))

                # Registrar en MovimientoInventario
                self.cursor.execute("""
                    INSERT INTO MovimientoInventario
                        (codigo, tipo, cantidad, existencia_anterior,
                         existencia_nueva, referencia, fecha, id_usuario)
                    VALUES (?, 'ajuste_manual', ?, ?, ?, ?, ?, ?)
                """, (codigo, cantidad, exist_ant, exist_nueva,
                      f"Cancelación ticket {id_venta} — {motivo}",
                      ahora, id_cancela))

            self.db.commit()
            messagebox.showinfo("Ticket cancelado",
                                f"✅ El ticket fue cancelado correctamente.\n"
                                f"Motivo: {motivo}")
            # Refrescar la vista completa
            self._build()

        except Exception as e:
            self.db.rollback()
            messagebox.showerror("Error",
                                 f"No se pudo cancelar el ticket.\n\nDetalle: {e}")

# ══════════════════════════════════════════════════════════════════════════════
#  VENTAS POR PERÍODO
# ══════════════════════════════════════════════════════════════════════════════
class ReportesPeriodo:
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
        _titulo(self.container, "📊  Reportes — Ventas por período")

        # Filtros
        filtros = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"], padx=10, pady=10)
        filtros.pack(fill=tk.X)

        for texto, var_name, default in [
            ("Desde:", "var_desde", date.today().replace(day=1).isoformat()),
            ("Hasta:", "var_hasta", date.today().isoformat()),
        ]:
            tk.Label(filtros, text=texto,
                     font=("Tahoma", 10, "bold"),
                     bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(side=tk.LEFT, padx=(8, 2))
            var = tk.StringVar(value=default)
            setattr(self, var_name, var)
            ttk.Entry(filtros, textvariable=var,
                      width=12, font=("Tahoma", 10)).pack(side=tk.LEFT, padx=2)
            tk.Label(filtros, text="(AAAA-MM-DD)",
                     font=("Tahoma", 8),
                     bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_error"]).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(filtros, text="Usuario:",
                 font=("Tahoma", 10, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(side=tk.LEFT, padx=(8, 2))
        self.cursor.execute("SELECT nombre FROM Usuarios ORDER BY nombre")
        usuarios = ["Todos"] + [r[0] for r in self.cursor.fetchall()]
        self.var_usr = tk.StringVar(value="Todos")
        ttk.Combobox(filtros, textvariable=self.var_usr,
                     values=usuarios, state="readonly",
                     width=18, font=("Tahoma", 10)).pack(side=tk.LEFT, padx=4)

        ttk.Button(filtros, text="Buscar",
                   style="Dorado.TButton",
                   command=self._cargar).pack(side=tk.LEFT, padx=12)

        # Tarjetas resumen del período
        self.resumen_frame = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        self.resumen_frame.pack(fill=tk.X, padx=10, pady=4)

        # Tabla
        tf = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        _estilo_tree()

        cols = ("fecha", "folio", "kg_total", "importe", "estado", "usuario")
        self.tree = ttk.Treeview(tf, columns=cols,
                                 show="headings", style="Carmelita.Treeview")
        for col, texto, ancho in [
            ("fecha",    "Fecha/Hora",  140),
            ("folio",    "Folio",        90),
            ("kg_total", "Kg total",     90),
            ("importe",  "Total",        90),
            ("estado",   "Estado",       90),
            ("usuario",  "Atendió",     120),
        ]:
            self.tree.heading(col, text=texto, anchor="center")
            self.tree.column(col, width=ancho, anchor="center")

        self.tree.tag_configure("cancelada",  foreground=COLORES_MODULOS["tag_alerta_fg"], background=COLORES_MODULOS["tag_alerta_bg"])
        self.tree.tag_configure("completada", foreground=COLORES_MODULOS["texto_exito"])

        sb = ttk.Scrollbar(tf, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.LEFT, fill=tk.Y)

        self._cargar()

    def _cargar(self):
        for w in self.resumen_frame.winfo_children():
            w.destroy()
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        desde = self.var_desde.get().strip()
        hasta = self.var_hasta.get().strip()
        usr   = self.var_usr.get()

        query = """
            SELECT v.fecha, v.folio, v.importe, v.estado, u.nombre,
                   COALESCE((
                       SELECT SUM(d.cantidad) FROM DetalleVenta d
                       WHERE d.id_venta = v.id_venta
                   ), 0)
            FROM Venta v
            JOIN Usuarios u ON u.id_usuario = v.id_usuario
            WHERE DATE(v.fecha) BETWEEN ? AND ?
        """
        params = [desde, hasta]
        if usr != "Todos":
            query += " AND u.nombre = ?"
            params.append(usr)
        query += " ORDER BY v.fecha DESC"

        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()

        total_imp  = sum(r[2] for r in rows if r[3] == "completada")
        total_kg   = sum(r[5] for r in rows if r[3] == "completada")
        completadas = sum(1 for r in rows if r[3] == "completada")
        canceladas  = sum(1 for r in rows if r[3] == "cancelada")

        _card_dato(self.resumen_frame, "Ventas completadas", str(completadas),  COLORES_MODULOS['texto_exito'])
        _card_dato(self.resumen_frame, "Ventas canceladas",  str(canceladas),   COLORES_MODULOS['texto_error'])
        _card_dato(self.resumen_frame, "Kg vendidos",        f"{total_kg:.3f}", COLORES_MODULOS['texto_principal'])
        _card_dato(self.resumen_frame, "Total recaudado",    f"${total_imp:.2f}",COLORES_MODULOS['texto_error'])

        for fecha, folio, imp, estado, usr_n, kg in rows:
            tag = "cancelada" if estado == "cancelada" else "completada"
            self.tree.insert('', tk.END, tags=(tag,), values=(
                fecha, folio,
                f"{kg:.3f} kg",
                f"${imp:.2f}",
                estado.capitalize(),
                usr_n,
            ))


# ══════════════════════════════════════════════════════════════════════════════
#  CORTES ANTERIORES
# ══════════════════════════════════════════════════════════════════════════════
class ReportesCortes:
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
        _titulo(self.container, "📊  Reportes — Cortes anteriores")

        cuerpo = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        cuerpo.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        cuerpo.columnconfigure(0, weight=2)
        cuerpo.columnconfigure(1, weight=3)
        cuerpo.rowconfigure(0, weight=1)

        self._tabla_cortes(cuerpo)
        self._detalle_corte(cuerpo)

    def _tabla_cortes(self, parent):
        frame = tk.Frame(parent, bg=COLORES_MODULOS["fondo_contenedor"])
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(frame, text="Cortes de caja",
                 font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", pady=(4, 6))

        _estilo_tree()
        cols = ("id", "apertura", "cierre", "ventas", "diferencia")
        self.tree = ttk.Treeview(frame, columns=cols,
                                 show="headings", style="Carmelita.Treeview")
        for col, texto, ancho in [
            ("id",          "#",          40),
            ("apertura",    "Apertura",  140),
            ("cierre",      "Cierre",    140),
            ("ventas",      "Ventas",     90),
            ("diferencia",  "Diferencia", 90),
        ]:
            self.tree.heading(col, text=texto, anchor="center")
            self.tree.column(col, width=ancho, anchor="center")

        self.tree.tag_configure("positivo", foreground=COLORES_MODULOS["texto_exito"])
        self.tree.tag_configure("negativo", foreground=COLORES_MODULOS["texto_error"])
        self.tree.tag_configure("abierto",  foreground=COLORES_MODULOS["encabezado_bg"],
                                background="#FFFBE6")

        sb = ttk.Scrollbar(frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.LEFT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._mostrar_detalle)
        self._cargar_cortes()

    def _cargar_cortes(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        self.cursor.execute("""
            SELECT id_turno, fecha_apertura, fecha_cierre,
                   total_ventas, diferencia, estado
            FROM Turno
            ORDER BY id_turno DESC
        """)
        for id_t, apertura, cierre, ventas, dif, estado in self.cursor.fetchall():
            if estado == "abierto":
                tag = "abierto"
                cierre_txt = "🔓 Abierto"
                dif_txt    = "—"
            else:
                tag        = "positivo" if (dif or 0) >= 0 else "negativo"
                cierre_txt = cierre or "—"
                dif_txt    = f"${dif:.2f}" if dif is not None else "—"

            self.tree.insert('', tk.END, iid=str(id_t), tags=(tag,), values=(
                id_t,
                apertura,
                cierre_txt,
                f"${(ventas or 0):.2f}",
                dif_txt,
            ))

    def _detalle_corte(self, parent):
        self.frame_det = tk.Frame(parent, bg=COLORES_MODULOS["fondo_contenedor"])
        self.frame_det.grid(row=0, column=1, sticky="nsew")

        tk.Label(self.frame_det,
                 text="Selecciona un corte para ver el detalle.",
                 font=("Tahoma", 10, "italic"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_error"]).pack(pady=20)

    def _mostrar_detalle(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        id_turno = int(sel[0])

        for w in self.frame_det.winfo_children():
            w.destroy()

        self.cursor.execute("""
            SELECT t.fecha_apertura, t.fecha_cierre, t.fondo_inicial,
                   t.total_ventas, t.total_movimientos, t.efectivo_esperado,
                   t.efectivo_contado, t.diferencia, t.estado, t.notas,
                   ua.nombre, uc.nombre
            FROM Turno t
            JOIN Usuarios ua ON ua.id_usuario = t.id_usuario_apertura
            LEFT JOIN Usuarios uc ON uc.id_usuario = t.id_usuario_cierre
            WHERE t.id_turno = ?
        """, (id_turno,))
        row = self.cursor.fetchone()
        if not row:
            return

        (apertura, cierre, fondo, ventas, movs, esperado,
         contado, diferencia, estado, notas, usr_a, usr_c) = row

        # Card de resumen
        card = tk.LabelFrame(self.frame_det,
                             text=f"  Detalle — Turno #{id_turno}  ",
                             bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"],
                             font=("Tahoma", 10, "bold"),
                             bd=2, relief="groove")
        card.pack(fill=tk.X, padx=4, pady=8, ipadx=10, ipady=6)

        def fila(txt, val, color=COLORES_MODULOS['texto_principal']):
            f = tk.Frame(card, bg=COLORES_MODULOS["fondo_contenedor"])
            f.pack(fill=tk.X, padx=16, pady=2)
            tk.Label(f, text=txt, font=("Tahoma", 10),
                     bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"], anchor="w").pack(side=tk.LEFT)
            tk.Label(f, text=val, font=("Tahoma", 10, "bold"),
                     bg=COLORES_MODULOS["fondo_contenedor"], fg=color, anchor="e").pack(side=tk.RIGHT)

        fila("Estado:",            estado.capitalize())
        fila("Apertura:",          apertura)
        fila("Cierre:",            cierre or "—")
        fila("Abrió:",             usr_a or "—")
        fila("Cerró:",             usr_c or "—")
        ttk.Separator(card, orient="horizontal").pack(fill=tk.X, padx=16, pady=4)
        fila("Fondo inicial:",     f"${(fondo or 0):.2f}")
        fila("Total ventas:",      f"${(ventas or 0):.2f}",      COLORES_MODULOS['texto_exito'])
        fila("Movimientos netos:", f"${(movs or 0):.2f}")
        fila("Efectivo esperado:", f"${(esperado or 0):.2f}",    COLORES_MODULOS['texto_error'])
        fila("Efectivo contado:",  f"${(contado or 0):.2f}")
        color_dif = COLORES_MODULOS['texto_exito'] if (diferencia or 0) >= 0 else COLORES_MODULOS['texto_error']
        fila("Diferencia:",        f"${(diferencia or 0):.2f}",  color_dif)
        if notas:
            ttk.Separator(card, orient="horizontal").pack(fill=tk.X, padx=16, pady=4)
            fila("Notas:", notas)

        # Ventas del turno
        tk.Label(self.frame_det, text="Ventas del turno:",
                 font=("Tahoma", 10, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=6, pady=(8, 2))

        _estilo_tree()
        vf = tk.Frame(self.frame_det, bg=COLORES_MODULOS["fondo_contenedor"])
        vf.pack(fill=tk.BOTH, expand=True, padx=4)

        cols = ("folio", "fecha", "importe", "estado")
        tv = ttk.Treeview(vf, columns=cols,
                          show="headings", style="Carmelita.Treeview", height=7)
        for col, texto, ancho in [
            ("folio",   "Folio",   90),
            ("fecha",   "Fecha",  140),
            ("importe", "Total",   90),
            ("estado",  "Estado",  90),
        ]:
            tv.heading(col, text=texto, anchor="center")
            tv.column(col, width=ancho, anchor="center")

        tv.tag_configure("cancelada",  foreground=COLORES_MODULOS["tag_alerta_fg"], background=COLORES_MODULOS["tag_alerta_bg"])
        tv.tag_configure("completada", foreground=COLORES_MODULOS["texto_exito"])

        sb2 = ttk.Scrollbar(vf, command=tv.yview)
        tv.configure(yscrollcommand=sb2.set)
        tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb2.pack(side=tk.LEFT, fill=tk.Y)

        self.cursor.execute("""
            SELECT folio, fecha, importe, estado
            FROM Venta WHERE id_turno = ?
            ORDER BY fecha
        """, (id_turno,))
        for folio, fecha, imp, est in self.cursor.fetchall():
            tag = "cancelada" if est == "cancelada" else "completada"
            tv.insert('', tk.END, tags=(tag,), values=(
                folio, fecha, f"${imp:.2f}", est.capitalize()))