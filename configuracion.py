import tkinter as tk
from tkinter import ttk, messagebox
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
                    foreground=COLORES_MODULOS["texto_principal"], rowheight=30,
                    font=("Tahoma", 11))
    style.configure("Carmelita.Treeview.Heading",
                    background=COLORES_MODULOS["tree_heading_bg"], foreground=COLORES_MODULOS["tree_heading_fg"],
                    font=("Tahoma", 11, "bold"))
    style.map("Carmelita.Treeview",
              background=[("selected", COLORES_MODULOS["tree_selected_bg"])],
              foreground=[("selected", COLORES_MODULOS["tree_selected_fg"])])


# ══════════════════════════════════════════════════════════════════════════════
#  GENERAL 
# ══════════════════════════════════════════════════════════════════════════════
class ConfigGeneral:
    CAMPOS = [
        # Del negocio
        ("nombre_negocio",        "Nombre del negocio",                    False),
        ("direccion",             "Dirección",                             False),
        ("telefono_negocio",      "Teléfono del negocio",                  False),
        ("rfc",                   "RFC (opcional)",                        False),
        # De operación
        ("precio_tortilla",       "Precio por kg de tortilla $",           True),
        ("fondo_apertura_default","Fondo de apertura por defecto $",       True),
        # Producción — relación harina/tortilla
        ("kg_por_bulto_harina",   "Peso de un bulto de harina (kg)",       True),
        ("tortilla_por_bulto",    "Kg de tortilla por bulto de harina",    True),
    ]

    def __init__(self, container, menu_principal=None):
        self.container = container
        self.menu_principal = menu_principal  # Referencia al menú para actualizar nombre
        self.db        = conexion.conectar()
        self.cursor    = self.db.cursor()
        self.vars      = {}
        configurar_estilos(container)
        self._build()

    def _build(self):
        for w in self.container.winfo_children():
            w.destroy()
        self.container.configure(bg="#FFFDE7")
        _titulo(self.container, "⚙️  Configuración — General")

        tk.Label(self.container,
                 text="Los cambios se aplican de inmediato en todo el sistema.",
                 font=("Tahoma", 9, "italic"),
                 bg="#FFFDE7", fg="#F57F17").pack(anchor="w", padx=14, pady=4)

        # Scroll
        canvas = tk.Canvas(self.container, bg="#FFFDE7", highlightthickness=0)
        sb     = ttk.Scrollbar(self.container, orient="vertical",
                               command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        frame = tk.Frame(canvas, bg="#FFFDE7")
        canvas.create_window((0, 0), window=frame, anchor="nw")
        frame.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Cargar valores actuales
        self.cursor.execute("SELECT clave, valor FROM Configuracion")
        bd_vals = dict(self.cursor.fetchall())

        # Separador visual antes de la sección de producción
        seccion_anterior = None
        secciones = {
            "nombre_negocio":        "🏪  Datos del negocio",
            "precio_tortilla":       "🫓  Operación",
            "kg_por_bulto_harina":   "⚙️  Producción — relación harina / tortilla",
        }

        for clave, etiqueta, solo_num in self.CAMPOS:
            # Encabezado de sección si aplica
            if clave in secciones:
                sec = tk.Frame(frame, bg="#C8E6C9", padx=10, pady=4)
                sec.pack(fill=tk.X, padx=10, pady=(14, 2))
                tk.Label(sec, text=secciones[clave],
                         font=("Tahoma", 10, "bold"),
                         bg="#C8E6C9", fg="#1B5E20").pack(side=tk.LEFT)

            fila = tk.Frame(frame, bg="#FFFDE7")
            fila.pack(fill=tk.X, padx=30, pady=5)

            tk.Label(fila, text=etiqueta + ":",
                     font=("Tahoma", 11, "bold"),
                     bg="#FFFDE7", fg="#1B5E20",
                     width=36, anchor="w").pack(side=tk.LEFT)

            var = tk.StringVar(value=bd_vals.get(clave, ""))
            self.vars[clave] = var

            ent = ttk.Entry(fila, textvariable=var,
                            font=("Tahoma", 11), width=24)
            ent.pack(side=tk.LEFT, padx=6)

            if solo_num:
                tk.Label(fila, text="(número)",
                         font=("Tahoma", 8, "italic"),
                         bg="#FFFDE7", fg="#F57F17").pack(side=tk.LEFT)

        # Nota explicativa de la relación harina/tortilla
        nota = tk.Frame(frame, bg="#E8F5E9", padx=12, pady=8)
        nota.pack(fill=tk.X, padx=30, pady=(0, 8))
        tk.Label(nota,
                 text="ℹ️  Ejemplo: si un bulto pesa 20 kg y produce 40 kg de tortilla,\n"
                      "escribe 20 en 'Peso del bulto' y 40 en 'Kg de tortilla por bulto'.\n"
                      "El sistema usará estos valores al registrar producción.",
                 font=("Tahoma", 9, "italic"),
                 bg="#E8F5E9", fg="#2E7D32",
                 justify="left").pack(anchor="w")

        tk.Frame(frame, bg="#FFFDE7", height=10).pack()
        ttk.Button(frame, text="💾  Guardar cambios",
                   style="Dorado.TButton", width=22,
                   command=self._guardar).pack(pady=10)

    def _guardar(self):
        errores = []
        for clave, etiqueta, solo_num in self.CAMPOS:
            valor = self.vars[clave].get().strip()
            if solo_num and valor:
                try:
                    v = float(valor)
                    if v < 0:
                        raise ValueError
                except ValueError:
                    errores.append(f"• {etiqueta}: debe ser un número positivo.")

        # Validación extra: relación de producción debe ser > 0
        for clave in ("kg_por_bulto_harina", "tortilla_por_bulto"):
            try:
                if float(self.vars[clave].get()) <= 0:
                    errores.append(f"• '{clave}' debe ser mayor a 0.")
            except ValueError:
                pass

        if errores:
            messagebox.showwarning("Valores inválidos",
                                   "Corrige los siguientes campos:\n\n" +
                                   "\n".join(errores))
            return

        for clave, _, _ in self.CAMPOS:
            valor = self.vars[clave].get().strip()
            self.cursor.execute("""
                INSERT INTO Configuracion (clave, valor, descripcion)
                VALUES (?, ?, '')
                ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor
            """, (clave, valor))

        # Sincronizar precio_tortilla en Articulo
        precio_str = self.vars.get("precio_tortilla", tk.StringVar()).get().strip()
        if precio_str:
            try:
                self.cursor.execute(
                    "UPDATE Articulo SET precio=? WHERE codigo='TORTILLA001'",
                    (float(precio_str),))
            except ValueError:
                pass

        # Sincronizar relación en RecetaProduccion
        try:
            tortilla_por_bulto = float(self.vars["tortilla_por_bulto"].get())
            self.cursor.execute("""
                UPDATE RecetaProduccion
                SET cantidad_producto = ?
                WHERE codigo_producto = 'TORTILLA001'
                  AND codigo_insumo   = 'HARINA001'
            """, (tortilla_por_bulto,))
        except ValueError:
            pass

        self.db.commit()
        
        # Recargar nombre del negocio en el menú si cambió
        if self.menu_principal and hasattr(self.menu_principal, 'recargar_nombre_negocio'):
            self.menu_principal.recargar_nombre_negocio()
        
        messagebox.showinfo("Guardado", "✅ Configuración guardada correctamente.")

# ══════════════════════════════════════════════════════════════════════════════
#  USUARIOS  —  lista, nuevo, editar, dar de baja  (solo administrador)
# ══════════════════════════════════════════════════════════════════════════════
class ConfigUsuarios:
    def __init__(self, container):
        self.container = container
        self.db        = conexion.conectar()
        self.cursor    = self.db.cursor()
        self._id_edit  = None        # id del usuario en edición (None = nuevo)
        configurar_estilos(container)
        self._build()

    # ── Construcción ──────────────────────────────────────────────────────────

    def _build(self):
        for w in self.container.winfo_children():
            w.destroy()
        self.container.configure(bg=COLORES_MODULOS["fondo_contenedor"])
        _titulo(self.container, "⚙️  Configuración — Usuarios")

        cuerpo = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        cuerpo.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.columnconfigure(1, weight=2)
        cuerpo.rowconfigure(0, weight=1)

        self._build_form(cuerpo)
        self._build_tabla(cuerpo)
        self._cargar_tabla()

    def _build_form(self, parent):
        self.card = tk.LabelFrame(parent, text="  Nuevo usuario  ",
                                  bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"],
                                  font=("Tahoma", 10, "bold"),
                                  bd=2, relief="groove")
        self.card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)

        def campo(label, var_name, ancho=24, show=None):
            tk.Label(self.card, text=label,
                     font=("Tahoma", 10, "bold"),
                     bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(10, 2))
            var = tk.StringVar()
            setattr(self, var_name, var)
            kw = {"textvariable": var, "font": ("Tahoma", 11), "width": ancho}
            if show:
                kw["show"] = show
            ttk.Entry(self.card, **kw).pack(padx=16)

        campo("Nombre completo:",   "var_nombre")
        campo("Teléfono (opcional):","var_telefono")

        # Rol
        tk.Label(self.card, text="Rol:",
                 font=("Tahoma", 10, "bold"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w", padx=16, pady=(10, 2))
        self.var_rol = tk.StringVar(value="trabajador")
        for texto, val in [("Trabajador", "trabajador"),
                           ("Administrador", "administrador")]:
            ttk.Radiobutton(self.card, text=texto,
                            variable=self.var_rol,
                            value=val).pack(anchor="w", padx=24, pady=2)

        # Contraseña
        campo("Contraseña:",         "var_pass1", show="•")
        campo("Confirmar contraseña:","var_pass2", show="•")

        # Nota para edición
        self.lbl_pass_nota = tk.Label(
            self.card,
            text="",
            font=("Tahoma", 8, "italic"),
            bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_error"], wraplength=200)
        self.lbl_pass_nota.pack(anchor="w", padx=16)

        # Botones
        frame_btns = tk.Frame(self.card, bg=COLORES_MODULOS["fondo_contenedor"])
        frame_btns.pack(pady=14)
        ttk.Button(frame_btns, text="💾 Guardar",
                   style="Dorado.TButton", width=13,
                   command=self._guardar).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_btns, text="✖ Cancelar",
                   style="Peligro.TButton", width=13,
                   command=self._limpiar).pack(side=tk.LEFT, padx=5)

    def _build_tabla(self, parent):
        frame = tk.Frame(parent, bg=COLORES_MODULOS["fondo_contenedor"])
        frame.grid(row=0, column=1, sticky="nsew", pady=4)

        acc = tk.Frame(frame, bg=COLORES_MODULOS["fondo_contenedor"])
        acc.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(acc, text="✏️ Editar",
                   style="Cafe.TButton", width=12,
                   command=self._editar).pack(side=tk.LEFT, padx=4)
        ttk.Button(acc, text="🚫 Dar de baja",
                   style="Advertencia.TButton", width=14,
                   command=self._dar_de_baja).pack(side=tk.LEFT, padx=4)
        ttk.Button(acc, text="✅ Reactivar",
                   style="Dorado.TButton", width=12,
                   command=self._reactivar).pack(side=tk.LEFT, padx=4)

        _estilo_tree()
        cols = ("id", "nombre", "rol", "telefono", "estado")
        self.tree = ttk.Treeview(frame, columns=cols,
                                 show="headings", style="Carmelita.Treeview")
        for col, texto, ancho in [
            ("id",       "#",         40),
            ("nombre",   "Nombre",   200),
            ("rol",      "Rol",      120),
            ("telefono", "Teléfono", 130),
            ("estado",   "Estado",    90),
        ]:
            self.tree.heading(col, text=texto, anchor="center")
            self.tree.column(col, width=ancho, anchor="center")

        self.tree.tag_configure("activo",   foreground=COLORES_MODULOS['texto_exito'])
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
            SELECT id_usuario, nombre, rol, telefono, activo
            FROM Usuarios ORDER BY nombre
        """)
        for id_, nom, rol, tel, activo in self.cursor.fetchall():
            tag    = "activo" if activo else "inactivo"
            estado = "Activo" if activo else "Baja"
            self.tree.insert('', tk.END, iid=str(id_), tags=(tag,), values=(
                id_, nom, rol.capitalize(), tel or "—", estado))

    def _limpiar(self):
        self._id_edit = None
        self.card.config(text="  Nuevo usuario  ")
        self.var_nombre.set("")
        self.var_telefono.set("")
        self.var_rol.set("trabajador")
        self.var_pass1.set("")
        self.var_pass2.set("")
        self.lbl_pass_nota.config(text="")

    def _editar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Selecciona un usuario para editar.")
            return
        self._id_edit = int(sel[0])
        self.cursor.execute("""
            SELECT nombre, rol, telefono FROM Usuarios WHERE id_usuario=?
        """, (self._id_edit,))
        row = self.cursor.fetchone()
        if not row:
            return
        nom, rol, tel = row
        self.card.config(text=f"  Editando: {nom}  ")
        self.var_nombre.set(nom)
        self.var_telefono.set(tel or "")
        self.var_rol.set(rol)
        self.var_pass1.set("")
        self.var_pass2.set("")
        self.lbl_pass_nota.config(
            text="Deja contraseña vacía para no cambiarla.")

    def _guardar(self):
        nombre   = self.var_nombre.get().strip()
        telefono = self.var_telefono.get().strip()
        rol      = self.var_rol.get()
        pass1    = self.var_pass1.get()
        pass2    = self.var_pass2.get()

        if not nombre:
            messagebox.showwarning("Nombre vacío",
                                   "Escribe el nombre del usuario.")
            return

        if self._id_edit is None:
            # Nuevo usuario — contraseña obligatoria
            if not pass1:
                messagebox.showwarning("Sin contraseña",
                                       "Debes establecer una contraseña.")
                return
            if pass1 != pass2:
                messagebox.showwarning("No coinciden",
                                       "Las contraseñas no coinciden.")
                return
            self.cursor.execute("""
                INSERT INTO Usuarios (nombre, rol, telefono, contrasena, activo)
                VALUES (?, ?, ?, ?, 1)
            """, (nombre, rol, telefono or None, pass1))
            msg = f"✅ Usuario '{nombre}' creado correctamente."

        else:
            # Edición — contraseña opcional
            if pass1 or pass2:
                if pass1 != pass2:
                    messagebox.showwarning("No coinciden",
                                           "Las contraseñas no coinciden.")
                    return
                self.cursor.execute("""
                    UPDATE Usuarios
                    SET nombre=?, rol=?, telefono=?, contrasena=?
                    WHERE id_usuario=?
                """, (nombre, rol, telefono or None, pass1, self._id_edit))
            else:
                self.cursor.execute("""
                    UPDATE Usuarios
                    SET nombre=?, rol=?, telefono=?
                    WHERE id_usuario=?
                """, (nombre, rol, telefono or None, self._id_edit))
            msg = f"✅ Usuario '{nombre}' actualizado."

        self.db.commit()
        messagebox.showinfo("Guardado", msg)
        self._limpiar()
        self._cargar_tabla()

    def _dar_de_baja(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Selecciona un usuario para dar de baja.")
            return
        id_usr = int(sel[0])

        self.cursor.execute(
            "SELECT nombre, rol, activo FROM Usuarios WHERE id_usuario=?",
            (id_usr,))
        row = self.cursor.fetchone()
        if not row:
            return
        nombre, rol, activo = row

        if not activo:
            messagebox.showinfo("Ya inactivo",
                                f"'{nombre}' ya está dado de baja.")
            return

        # No permitir dar de baja al último administrador activo
        if rol == "administrador":
            self.cursor.execute("""
                SELECT COUNT(*) FROM Usuarios
                WHERE rol='administrador' AND activo=1
            """)
            if self.cursor.fetchone()[0] <= 1:
                messagebox.showwarning(
                    "Operación no permitida",
                    "No puedes dar de baja al único administrador activo.")
                return

        if not messagebox.askyesno("Confirmar",
                                   f"¿Dar de baja a '{nombre}'?\n\n"
                                   "El usuario no podrá iniciar sesión, "
                                   "pero su historial se conserva."):
            return

        self.cursor.execute(
            "UPDATE Usuarios SET activo=0 WHERE id_usuario=?", (id_usr,))
        self.db.commit()
        messagebox.showinfo("Baja aplicada",
                            f"'{nombre}' fue dado de baja correctamente.")
        self._cargar_tabla()

    def _reactivar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Selecciona un usuario para reactivar.")
            return
        id_usr = int(sel[0])
        self.cursor.execute(
            "SELECT nombre, activo FROM Usuarios WHERE id_usuario=?", (id_usr,))
        row = self.cursor.fetchone()
        if not row:
            return
        nombre, activo = row

        if activo:
            messagebox.showinfo("Ya activo",
                                f"'{nombre}' ya está activo.")
            return

        self.cursor.execute(
            "UPDATE Usuarios SET activo=1 WHERE id_usuario=?", (id_usr,))
        self.db.commit()
        messagebox.showinfo("Reactivado",
                            f"✅ '{nombre}' fue reactivado correctamente.")
        self._cargar_tabla()


# ══════════════════════════════════════════════════════════════════════════════
#  MI CONTRASEÑA  —  cualquier rol puede cambiar la suya
# ══════════════════════════════════════════════════════════════════════════════
class ConfigContrasena:
    def __init__(self, container, usuario=""):
        self.container = container
        self.usuario   = usuario      # nombre del usuario activo
        self.db        = conexion.conectar()
        self.cursor    = self.db.cursor()
        configurar_estilos(container)
        self._build()

    def _build(self):
        for w in self.container.winfo_children():
            w.destroy()
        self.container.configure(bg=COLORES_MODULOS["fondo_contenedor"])
        _titulo(self.container, "⚙️  Configuración — Mi contraseña")

        # Card centrado
        wrapper = tk.Frame(self.container, bg=COLORES_MODULOS["fondo_contenedor"])
        wrapper.pack(expand=True)

        card = tk.LabelFrame(wrapper,
                             text=f"  Cambiar contraseña — {self.usuario}  ",
                             bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"],
                             font=("Tahoma", 11, "bold"),
                             bd=2, relief="groove")
        card.pack(padx=40, pady=30, ipadx=20, ipady=10)

        def campo(label, var_name):
            tk.Label(card, text=label,
                     font=("Tahoma", 11, "bold"),
                     bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_principal"]).pack(anchor="w",
                                                      padx=20, pady=(14, 2))
            var = tk.StringVar()
            setattr(self, var_name, var)
            ttk.Entry(card, textvariable=var, show="•",
                      font=("Tahoma", 12), width=26).pack(padx=20)

        campo("Contraseña actual:",      "var_actual")
        campo("Nueva contraseña:",       "var_nueva")
        campo("Confirmar nueva contraseña:", "var_confirmar")

        tk.Label(card,
                 text="Mínimo 2 caracteres.",
                 font=("Tahoma", 8, "italic"),
                 bg=COLORES_MODULOS["fondo_contenedor"], fg=COLORES_MODULOS["texto_error"]).pack(anchor="w", padx=22)

        ttk.Button(card, text="🔒  Cambiar contraseña",
                   style="Dorado.TButton", width=24,
                   command=self._cambiar).pack(pady=20)

    def _cambiar(self):
        actual    = self.var_actual.get()
        nueva     = self.var_nueva.get()
        confirmar = self.var_confirmar.get()

        if not actual or not nueva or not confirmar:
            messagebox.showwarning("Campos vacíos",
                                   "Completa todos los campos.")
            return

        if len(nueva) < 2:
            messagebox.showwarning("Contraseña muy corta",
                                   "La nueva contraseña debe tener al menos 2 caracteres.")
            return

        if nueva != confirmar:
            messagebox.showwarning("No coinciden",
                                   "La nueva contraseña y la confirmación no coinciden.")
            return

        # Verificar contraseña actual
        self.cursor.execute("""
            SELECT id_usuario FROM Usuarios
            WHERE nombre=? AND contrasena=?
        """, (self.usuario, actual))
        row = self.cursor.fetchone()

        if not row:
            messagebox.showerror("Contraseña incorrecta",
                                 "La contraseña actual no es correcta.")
            return

        # Aplicar el cambio
        self.cursor.execute("""
            UPDATE Usuarios SET contrasena=? WHERE id_usuario=?
        """, (nueva, row[0]))
        self.db.commit()

        messagebox.showinfo("Contraseña actualizada",
                            "✅ Tu contraseña fue cambiada correctamente.")

        # Limpiar campos
        self.var_actual.set("")
        self.var_nueva.set("")
        self.var_confirmar.set("")