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

def _turno_activo(cursor):
    cursor.execute("SELECT id_turno FROM Turno WHERE estado='abierto' LIMIT 1")
    row = cursor.fetchone()
    return row[0] if row else None

def _obtener_config(cursor, clave, default=None):
    """Obtiene un valor de configuración desde la BD."""
    try:
        cursor.execute("SELECT valor FROM Configuracion WHERE clave = ?", (clave,))
        row = cursor.fetchone()
        return row[0] if row else default
    except:
        return default


# ══════════════════════════════════════════════════════════════════════════════
#  ABRIR TURNO
# ══════════════════════════════════════════════════════════════════════════════
class CajaAbrir:
    def __init__(self, container, usuario):
        self.container = container
        self.usuario   = usuario
        self.db        = conexion.conectar()
        self.cursor    = self.db.cursor()
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
        self.container.configure(bg=COLORES_MODULOS['fondo_contenedor'])
        _titulo(self.container, "💰  Caja — Abrir turno")

        id_turno = _turno_activo(self.cursor)

        if id_turno:
            # Ya hay turno abierto → mostrar info
            self.cursor.execute("""
                SELECT t.fecha_apertura, t.fondo_inicial, u.nombre
                FROM Turno t
                JOIN Usuarios u ON u.id_usuario = t.id_usuario_apertura
                WHERE t.id_turno = ?
            """, (id_turno,))
            row = self.cursor.fetchone()
            fecha, fondo, quien = row

            card = tk.Frame(self.container, bg=COLORES_MODULOS['fondo_card'], bd=1, relief="groove")
            card.pack(padx=40, pady=30, ipadx=20, ipady=20)

            tk.Label(card, text="✅  Turno activo",
                     font=("Tahoma", 16, "bold"),
                     bg=COLORES_MODULOS['fondo_card'], fg=COLORES_MODULOS['texto_exito']).pack(pady=(10, 4))
            tk.Label(card, text=f"Apertura: {fecha}",
                     font=("Tahoma", 11), bg=COLORES_MODULOS['fondo_card'], fg=COLORES_MODULOS['texto_principal']).pack()
            tk.Label(card, text=f"Fondo inicial: ${fondo:.2f}",
                     font=("Tahoma", 11), bg=COLORES_MODULOS['fondo_card'], fg=COLORES_MODULOS['texto_principal']).pack()
            tk.Label(card, text=f"Abrió: {quien}",
                     font=("Tahoma", 11), bg=COLORES_MODULOS['fondo_card'], fg=COLORES_MODULOS['texto_principal']).pack(pady=(0, 10))
        else:
            # No hay turno → formulario para abrir
            card = tk.Frame(self.container, bg=COLORES_MODULOS['fondo_card'], bd=1, relief="groove")
            card.pack(padx=40, pady=30, ipadx=20, ipady=20)

            tk.Label(card, text="Abrir nuevo turno",
                     font=("Tahoma", 15, "bold"),
                     bg=COLORES_MODULOS['fondo_card'], fg=COLORES_MODULOS['texto_principal']).pack(pady=(10, 16))

            fila = tk.Frame(card, bg=COLORES_MODULOS['fondo_card'])
            fila.pack()

            tk.Label(fila, text="Fondo inicial ($):",
                     font=("Tahoma", 12, "bold"),
                     bg=COLORES_MODULOS['fondo_card'], fg=COLORES_MODULOS['texto_principal']).grid(row=0, column=0,
                                                      sticky="e", padx=8, pady=6)
            fondo_default = _obtener_config(self.cursor, "fondo_apertura_default", "200.00")
            self.var_fondo = tk.StringVar(value=fondo_default)
            ttk.Entry(fila, textvariable=self.var_fondo,
                      font=("Tahoma", 12), width=14).grid(row=0, column=1, padx=8)

            tk.Label(fila, text="Notas (opcional):",
                     font=("Tahoma", 12, "bold"),
                     bg=COLORES_MODULOS['fondo_card'], fg=COLORES_MODULOS['texto_principal']).grid(row=1, column=0,
                                                      sticky="e", padx=8, pady=6)
            self.var_notas = tk.StringVar()
            ttk.Entry(fila, textvariable=self.var_notas,
                      font=("Tahoma", 12), width=26).grid(row=1, column=1, padx=8)

            ttk.Button(card, text="Abrir turno",
                       style="Exito.TButton", width=18,
                       command=self._abrir).pack(pady=16)

    def _abrir(self):
        try:
            fondo = float(self.var_fondo.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Fondo inválido", "Ingresa un monto válido para el fondo.")
            return

        ahora     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        id_usuario = self._get_usuario_id()

        self.cursor.execute("""
            INSERT INTO Turno (fecha_apertura, fondo_inicial, estado,
                               id_usuario_apertura, notas)
            VALUES (?, ?, 'abierto', ?, ?)
        """, (ahora, fondo, id_usuario, self.var_notas.get().strip()))
        self.db.commit()

        messagebox.showinfo("Turno abierto",
                            f"✅ Turno abierto correctamente.\nFondo inicial: ${fondo:.2f}")
        self._build()


# ══════════════════════════════════════════════════════════════════════════════
#  CORTE DE CAJA
# ══════════════════════════════════════════════════════════════════════════════
class CajaCorte:
    def __init__(self, container, usuario):
        self.container = container
        self.usuario   = usuario
        self.db        = conexion.conectar()
        self.cursor    = self.db.cursor()
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
        self.container.configure(bg=COLORES_MODULOS['fondo_contenedor'])
        _titulo(self.container, "💰  Caja — Corte de caja")

        id_turno = _turno_activo(self.cursor)

        if not id_turno:
            tk.Label(self.container,
                     text="⚠️  No hay turno abierto.\nAbre un turno desde 'Abrir turno'.",
                     font=("Tahoma", 13), bg=COLORES_MODULOS['fondo_contenedor'], fg=COLORES_MODULOS['texto_error']).pack(pady=40)
            return

        # Calcular totales del turno
        self.cursor.execute("""
            SELECT COALESCE(SUM(importe),0)
            FROM Venta WHERE id_turno=? AND estado='completada'
        """, (id_turno,))
        total_ventas = self.cursor.fetchone()[0]

        self.cursor.execute("""
            SELECT COALESCE(SUM(monto), 0)
            FROM MovimientoCaja WHERE id_turno=? AND tipo='entrada'
        """, (id_turno,))
        total_entradas = self.cursor.fetchone()[0]

        self.cursor.execute("""
            SELECT COALESCE(SUM(monto), 0)
            FROM MovimientoCaja WHERE id_turno=? AND tipo='salida'
        """, (id_turno,))
        total_salidas = self.cursor.fetchone()[0]

        self.cursor.execute(
            "SELECT fondo_inicial FROM Turno WHERE id_turno=?", (id_turno,))
        fondo = self.cursor.fetchone()[0]

        efectivo_esperado = fondo + total_ventas + total_entradas - total_salidas

        self.id_turno          = id_turno
        self.efectivo_esperado = efectivo_esperado
        self.total_ventas      = total_ventas
        self.total_entradas    = total_entradas
        self.total_salidas     = total_salidas
        self.fondo             = fondo

        # Tarjeta resumen
        card = tk.Frame(self.container, bg=COLORES_MODULOS['fondo_card'], bd=1, relief="groove")
        card.pack(padx=30, pady=16, fill=tk.X)

        def fila_resumen(texto, valor, color=COLORES_MODULOS['texto_principal']):
            f = tk.Frame(card, bg=COLORES_MODULOS['fondo_card'])
            f.pack(fill=tk.X, padx=20, pady=3)
            tk.Label(f, text=texto, font=("Tahoma", 11),
                     bg=COLORES_MODULOS['fondo_card'], fg=COLORES_MODULOS['texto_principal'], anchor="w").pack(side=tk.LEFT)
            tk.Label(f, text=f"${valor:.2f}", font=("Tahoma", 11, "bold"),
                     bg=COLORES_MODULOS['fondo_card'], fg=color, anchor="e").pack(side=tk.RIGHT)

        tk.Label(card, text="Resumen del turno",
                 font=("Tahoma", 13, "bold"),
                 bg=COLORES_MODULOS['fondo_card'], fg=COLORES_MODULOS['texto_principal']).pack(pady=(12, 8))

        fila_resumen("Fondo inicial:",        fondo)
        fila_resumen("Total ventas:",         total_ventas,   COLORES_MODULOS['texto_exito'])
        fila_resumen("Entradas extra:",       total_entradas, COLORES_MODULOS['texto_exito'])
        fila_resumen("Salidas / gastos:",     total_salidas,  COLORES_MODULOS['texto_error'])
        ttk.Separator(card, orient="horizontal").pack(fill=tk.X, padx=20, pady=6)
        fila_resumen("Efectivo esperado:",    efectivo_esperado, COLORES_MODULOS['encabezado_bg'])

        # Campo efectivo contado
        inp = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        inp.pack(pady=10)
        tk.Label(inp, text="Efectivo contado ($):",
                 font=("Tahoma", 12, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).grid(row=0, column=0,
                                                   sticky="e", padx=8)
        self.var_contado = tk.StringVar()
        self.var_contado.trace_add("write", lambda *a: self._actualizar_diferencia())
        ttk.Entry(inp, textvariable=self.var_contado,
                  font=("Tahoma", 12), width=14).grid(row=0, column=1, padx=8)

        self.lbl_diferencia = tk.Label(self.container, text="Diferencia: —",
                                       font=("Tahoma", 13, "bold"),
                                       bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"])
        self.lbl_diferencia.pack(pady=4)

        ttk.Button(self.container, text="Cerrar turno y guardar corte",
                   style="Peligro.TButton", width=30,
                   command=self._cerrar).pack(pady=12)

    def _actualizar_diferencia(self):
        try:
            contado    = float(self.var_contado.get().replace(",", "."))
            diferencia = contado - self.efectivo_esperado
            color      = COLORES_MODULOS['texto_exito'] if diferencia >= 0 else COLORES_MODULOS['texto_error']
            signo      = "+" if diferencia >= 0 else ""
            self.lbl_diferencia.config(
                text=f"Diferencia: {signo}${diferencia:.2f}", fg=color)
        except ValueError:
            self.lbl_diferencia.config(text="Diferencia: —", fg=COLORES_MODULOS["texto_principal"])

    def _cerrar(self):
        try:
            contado = float(self.var_contado.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Dato inválido",
                                   "Ingresa el efectivo contado para cerrar el turno.")
            return

        diferencia = contado - self.efectivo_esperado
        ahora      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        id_usuario = self._get_usuario_id()

        confirmar = messagebox.askyesno(
            "Confirmar corte",
            f"¿Cerrar el turno?\n\n"
            f"Efectivo esperado: ${self.efectivo_esperado:.2f}\n"
            f"Efectivo contado:  ${contado:.2f}\n"
            f"Diferencia:        ${diferencia:.2f}"
        )
        if not confirmar:
            return

        self.cursor.execute("""
            UPDATE Turno SET
                fecha_cierre      = ?,
                total_ventas      = ?,
                total_movimientos = ?,
                efectivo_esperado = ?,
                efectivo_contado  = ?,
                diferencia        = ?,
                estado            = 'cerrado',
                id_usuario_cierre = ?
            WHERE id_turno = ?
        """, (ahora, self.total_ventas,
              self.total_entradas - self.total_salidas,
              self.efectivo_esperado, contado, diferencia,
              id_usuario, self.id_turno))
        self.db.commit()

        messagebox.showinfo("Corte guardado",
                            f"✅ Turno cerrado correctamente.\nDiferencia: ${diferencia:.2f}")
        self._build()


# ══════════════════════════════════════════════════════════════════════════════
#  MOVIMIENTOS DE CAJA  (gastos y entradas extra)
# ══════════════════════════════════════════════════════════════════════════════
class CajaMovimientos:
    def __init__(self, container, usuario):
        self.container = container
        self.usuario   = usuario
        self.db        = conexion.conectar()
        self.cursor    = self.db.cursor()
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
        _titulo(self.container, "💰  Caja — Movimientos")

        id_turno = _turno_activo(self.cursor)

        if not id_turno:
            tk.Label(self.container,
                     text="⚠️  No hay turno abierto.\nAbre un turno para registrar movimientos.",
                     font=("Tahoma", 13), bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_error"]).pack(pady=40)
            return

        self.id_turno = id_turno

        cuerpo = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        cuerpo.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        cuerpo.columnconfigure(0, weight=2)
        cuerpo.columnconfigure(1, weight=3)
        cuerpo.rowconfigure(0, weight=1)

        self._form(cuerpo)
        self._tabla(cuerpo)

    def _form(self, parent):
        card = tk.LabelFrame(parent, text="  Nuevo movimiento  ",
                             bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"],
                             font=("Tahoma", 10, "bold"),
                             bd=2, relief="groove")
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=4)

        tk.Label(card, text="Tipo:", font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(14, 2))
        self.var_tipo = tk.StringVar(value="salida")
        fr = tk.Frame(card, bg=COLORES_MODULOS["fondo_contenedor"])
        fr.pack(anchor="w", padx=16)
        for texto, val in [("💸 Salida (gasto)", "salida"),
                           ("💵 Entrada (extra)", "entrada")]:
            ttk.Radiobutton(fr, text=texto, variable=self.var_tipo,
                            value=val).pack(anchor="w", pady=2)

        tk.Label(card, text="Concepto:", font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(10, 2))
        self.var_concepto = tk.StringVar()
        ttk.Entry(card, textvariable=self.var_concepto,
                  font=("Tahoma", 11), width=24).pack(padx=16)

        tk.Label(card, text="Monto ($):", font=("Tahoma", 11, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(10, 2))
        self.var_monto = tk.StringVar()
        ttk.Entry(card, textvariable=self.var_monto,
                  font=("Tahoma", 11), width=14).pack(padx=16)

        ttk.Button(card, text="Registrar movimiento",
                   style="Exito.TButton", width=22,
                   command=self._registrar).pack(pady=16)

    def _tabla(self, parent):
        frame = tk.Frame(parent, bg=COLORES_MODULOS["fondo_contenedor"])
        frame.grid(row=0, column=1, sticky="nsew", pady=4)

        tk.Label(frame, text="Movimientos del turno",
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

        cols = ("tipo", "concepto", "monto", "fecha")
        self.tree = ttk.Treeview(frame, columns=cols,
                                 show="headings", style="Carmelita.Treeview")
        for col, texto, ancho in [
            ("tipo",     "Tipo",     90),
            ("concepto", "Concepto", 200),
            ("monto",    "Monto",    90),
            ("fecha",    "Fecha",    140),
        ]:
            self.tree.heading(col, text=texto, anchor="center")
            self.tree.column(col, width=ancho, anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True)
        self._cargar_tabla()

    def _cargar_tabla(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.cursor.execute("""
            SELECT tipo, concepto, monto, fecha
            FROM MovimientoCaja
            WHERE id_turno = ?
            ORDER BY fecha DESC
        """, (self.id_turno,))
        for tipo, concepto, monto, fecha in self.cursor.fetchall():
            color_tipo = "💸 Salida" if tipo == "salida" else "💵 Entrada"
            self.tree.insert('', tk.END, values=(
                color_tipo, concepto, f"${monto:.2f}", fecha))

    def _registrar(self):
        concepto = self.var_concepto.get().strip()
        if not concepto:
            messagebox.showwarning("Concepto vacío", "Escribe el concepto del movimiento.")
            return
        try:
            monto = float(self.var_monto.get().replace(",", "."))
            if monto <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Monto inválido", "Ingresa un monto mayor a cero.")
            return

        ahora      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        id_usuario = self._get_usuario_id()

        self.cursor.execute("""
            INSERT INTO MovimientoCaja (id_turno, tipo, concepto, monto, fecha, id_usuario)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (self.id_turno, self.var_tipo.get(), concepto, monto, ahora, id_usuario))
        self.db.commit()

        self.var_concepto.set("")
        self.var_monto.set("")
        self._cargar_tabla()
        messagebox.showinfo("Registrado", "✅ Movimiento registrado correctamente.")