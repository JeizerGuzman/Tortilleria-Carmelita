import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import os
import conexion
from botones import configurar_estilos


class VentanaLogin:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Tortillería Carmelita — Iniciar Sesión")
        self.ventana.state("zoomed")
        self.ventana.config(bg="#FFF8E7")
        self.ventana.resizable(False, False)
        configurar_estilos(self.ventana)

        # Conexión SQLite
        self.db     = conexion.conectar()
        self.cursor = self.db.cursor()

        # Fondo
        self._cargar_fondo()

        # ── Contenedor centrado con place ─────────────────────────────────────
        self.widget = tk.LabelFrame(
            self.ventana,
            width=420,
            height=520,
            bg="#FFF8E7",
            bd=2,
            relief="groove",
            highlightbackground="#C47A2B",
            highlightcolor="#C47A2B",
        )
        # Centrar horizontalmente y verticalmente con place
        self.widget.place(relx=0.5, rely=0.5, anchor="center")
        self.widget.pack_propagate(False)

        self._cargar_logo()

        # ── Estilos ───────────────────────────────────────────────────────────
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Enhanced.TCombobox',
                        font=('Tahoma', 12),
                        foreground='#7B3F00',
                        background='#FFF8E7',
                        bordercolor='#C47A2B',
                        arrowsize=14,
                        padding=(6, 4),
                        relief='solid',
                        borderwidth=1)
        style.map('Enhanced.TCombobox',
                  fieldbackground=[('readonly', '#FFF8E7')],
                  selectbackground=[('readonly', '#F2C94C')],
                  selectforeground=[('readonly', '#7B3F00')],
                  bordercolor=[('focus', '#7B3F00')],
                  arrowsize=[('pressed', 12), ('!pressed', 14)])

        style.configure('Modern.TEntry',
                        font=('Tahoma', 12),
                        foreground='#7B3F00',
                        background='#FFF8E7',
                        bordercolor='#C47A2B',
                        padding=(6, 4),
                        relief='solid',
                        borderwidth=1)
        style.map('Modern.TEntry',
                  bordercolor=[('focus', '#7B3F00')],
                  fieldbackground=[('!disabled', '#FFF8E7')])

        # ── Usuario ───────────────────────────────────────────────────────────
        tk.Label(self.widget, text="Usuario",
                 font=("Tahoma", 12, "bold"),
                 bg="#FFF8E7", fg="#7B3F00").pack(pady=(15, 0))

        self.nombre_var = tk.StringVar()

        # Nueva consulta compatible con la BD actualizada (campo 'activo')
        self.cursor.execute(
            "SELECT nombre FROM Usuarios WHERE activo = 1 ORDER BY nombre"
        )
        nombres = [r[0] for r in self.cursor.fetchall()]

        self.cmb_usuario = ttk.Combobox(
            self.widget,
            values=nombres,
            textvariable=self.nombre_var,
            font=('Tahoma', 12),
            width=23,
            style='Enhanced.TCombobox',
            state="readonly"
        )
        self.cmb_usuario.bind("<<ComboboxSelected>>", self._mostrar_rol)

        if not nombres:
            self.cmb_usuario.set("-- Sin usuarios registrados --")
            self.cmb_usuario['state'] = 'disabled'
        else:
            self.cmb_usuario.current(0)
        self.cmb_usuario.pack(pady=5)

        # Rol mostrado
        self.rol_label = tk.Label(self.widget, text="Rol: ",
                                  font=("Tahoma", 12),
                                  bg="#FFF8E7", fg="#C47A2B")
        self.rol_label.pack(pady=5)

        # ── Contraseña ────────────────────────────────────────────────────────
        tk.Label(self.widget, text="Contraseña",
                 font=("Tahoma", 12, "bold"),
                 bg="#FFF8E7", fg="#7B3F00").pack()

        self.entry_pwd = ttk.Entry(
            self.widget,
            show="*",
            style='Modern.TEntry',
            width=25,
            font=('Tahoma', 12)
        )
        self.entry_pwd.pack(pady=5)
        self.entry_pwd.bind("<Return>", lambda e: self._iniciar_sesion())

        self.var_show = tk.BooleanVar()
        tk.Checkbutton(self.widget, text="Ver contraseña",
                       variable=self.var_show,
                       command=self._ver_contraseña,
                       font=("Tahoma", 12),
                       bg="#FFF8E7", fg="#7B3F00",
                       activebackground="#FFF8E7",
                       selectcolor="#F2C94C").pack(pady=10)

        # Botón Iniciar
        ttk.Button(self.widget, text="Iniciar Sesión",
                   command=self._iniciar_sesion,
                   style="Exito.TButton",
                   width=15).pack(pady=20)

        # Mostrar rol del primer usuario por defecto
        if nombres:
            self._mostrar_rol(None)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _cargar_fondo(self):
        dir_act = os.path.dirname(os.path.abspath(__file__))
        ruta = os.path.join(dir_act, "imagen", "fondoLogin.png")
        try:
            img = Image.open(ruta)
            w = self.ventana.winfo_screenwidth()
            h = self.ventana.winfo_screenheight()
            img = img.resize((w, h), Image.Resampling.LANCZOS)
            self.bg_img = ImageTk.PhotoImage(img)
            tk.Label(self.ventana, image=self.bg_img).place(x=0, y=0, relwidth=1, relheight=1)
        except Exception:
            pass

    def _cargar_logo(self):
        dir_act = os.path.dirname(os.path.abspath(__file__))
        ruta = os.path.join(dir_act, "imagen", "logoTortilleria.png")
        try:
            logo = Image.open(ruta).resize((280, 160), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(logo)
            frame = tk.Frame(self.widget, bg="#FFF8E7", width=300, height=200)
            frame.pack()
            frame.pack_propagate(False)
            tk.Label(frame, image=self.logo_img, bg="#FFF8E7").pack(pady=20)
        except Exception:
            pass

    def _mostrar_rol(self, event):
        nombre = self.nombre_var.get()
        # Consulta actualizada: usa columna 'rol' de la tabla Usuarios
        self.cursor.execute(
            "SELECT rol FROM Usuarios WHERE nombre = ? AND activo = 1",
            (nombre,)
        )
        row = self.cursor.fetchone()
        rol = row[0].capitalize() if row else ''
        self.rol_label.config(text=f"Rol: {rol}")

    def _ver_contraseña(self):
        self.entry_pwd.config(show='' if self.var_show.get() else '*')

    def _iniciar_sesion(self):
        nombre = self.nombre_var.get().strip()
        pwd    = self.entry_pwd.get().strip()

        if not nombre or nombre == "-- Sin usuarios registrados --":
            messagebox.showerror("Error", "Selecciona un usuario.")
            return
        if not pwd:
            messagebox.showerror("Error", "La contraseña no puede estar vacía.")
            return

        # Consulta actualizada: columna 'contrasena' (sin tilde) según la nueva BD
        self.cursor.execute(
            "SELECT contrasena FROM Usuarios WHERE nombre = ? AND activo = 1",
            (nombre,)
        )
        row = self.cursor.fetchone()

        if not row:
            messagebox.showerror("Error", "Usuario no encontrado o dado de baja.")
            return
        if pwd != row[0]:
            messagebox.showerror("Error", "Contraseña incorrecta.")
            return

        # Login exitoso → abrir menú principal
        from menu import PuntoDeVenta
        self.widget.destroy()
        PuntoDeVenta(self.ventana, usuario=nombre).main()

    def run(self):
        self.ventana.mainloop()


if __name__ == "__main__":
    app = VentanaLogin()
    app.run()