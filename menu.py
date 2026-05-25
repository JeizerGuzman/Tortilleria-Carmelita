import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import locale
import os
from PIL import Image, ImageTk
import conexion
from contraseña import VentanaLogin
from botones import configurar_estilos, UI

def _obtener_nombre_negocio():
    """Obtiene el nombre del negocio desde la BD."""
    try:
        db = conexion.conectar()
        cursor = db.cursor()
        cursor.execute("SELECT valor FROM Configuracion WHERE clave = 'nombre_negocio'")
        row = cursor.fetchone()
        resultado = row[0] if row else "Tortillería Carmelita"
        db.close()
        return resultado
    except:
        return "Tortillería Carmelita"

class PuntoDeVenta:
    def __init__(self, root=None, usuario="Administrador", rol="administrador"):
        self.usuario = usuario
        self.rol     = rol.lower()
        self.root    = root if root else tk.Tk()
        self.nombre_negocio = _obtener_nombre_negocio()
        self.root.title(f"{self.nombre_negocio} — Punto de Venta")
        self.root.state("zoomed")
        self.root.configure(bg="#FFF8E7")
        self.root.resizable(False, False)
        configurar_estilos(self.root)
        self._cargar_icono()

    # ── Navegación principal ──────────────────────────────────────────────────

    def _cargar_icono(self):
        dir_act = os.path.dirname(os.path.abspath(__file__))
        ruta = os.path.join(dir_act, "imagen", "logoApp.png")
        try:
            icono = Image.open(ruta).resize((48, 48), Image.Resampling.LANCZOS)
            self.icono_img = ImageTk.PhotoImage(icono)
            self.root.iconphoto(True, self.icono_img)
        except Exception:
            pass

    def recargar_nombre_negocio(self):
        """Recarga el nombre del negocio desde la BD y actualiza la UI."""
        self.nombre_negocio = _obtener_nombre_negocio()
        self.root.title(f"{self.nombre_negocio} — Punto de Venta")
        if hasattr(self, 'lbl_nombre_negocio'):
            self.lbl_nombre_negocio.config(text=f"🫓 {self.nombre_negocio}")

    def _limpiar_contenedor(self):
        for w in self.frame_contenedor.winfo_children():
            w.destroy()
        for w in self.frame_secundario.winfo_children():
            w.destroy()
        self.frame_secundario.pack_forget()

    def _mostrar_secundario(self, botones):
        """Muestra una barra secundaria con los botones dados."""
        self.frame_secundario.pack(side=tk.TOP, fill=tk.X)
        for w in self.frame_secundario.winfo_children():
            w.destroy()
        for texto, comando in botones:
            ttk.Button(
                self.frame_secundario,
                text=texto,
                style="Cafe.TButton",
                command=comando,
                width=18
            ).pack(side=tk.LEFT, padx=4, pady=4)

    def _turno_abierto(self):
        """Verifica si hay un turno abierto en la BD."""
        try:
            from conexion import conectar
            db  = conectar()
            cur = db.cursor()
            cur.execute("SELECT id_turno FROM Turno WHERE estado = 'abierto' LIMIT 1")
            row = cur.fetchone()
            db.close()
            return row is not None
        except:
            return False

    def _solo_admin(self):
        """Muestra advertencia y devuelve False si el usuario no es administrador."""
        if self.rol != "administrador":
            messagebox.showwarning(
                "Acceso restringido",
                "Solo el administrador puede acceder a esta sección."
            )
            return False
        return True

    # ── Módulos principales ───────────────────────────────────────────────────

    def on_ventas(self):
        if not self._turno_abierto():
            messagebox.showwarning(
                "Sin turno activo",
                "No hay ningún turno abierto.\n\nVe a Caja → Abrir turno antes de registrar ventas."
            )
            return
        self._limpiar_contenedor()
        from ventas import VentaApp
        VentaApp(self.frame_contenedor, self.usuario)

    def on_inventario(self):
        self._limpiar_contenedor()

        # Botones base (todos los roles)
        botones = [
            ("Ver existencias", self.on_inv_existencias),
            ("Movimientos",     self.on_inv_movimientos),
            ("Producción",      self.on_inv_produccion),
            ("Ajuste manual",   self.on_inv_ajuste),
        ]

        # Botones exclusivos de administrador
        if self.rol == "administrador":
            botones += [
                ("Artículos",  self.on_inv_articulos),
                ("Categorías", self.on_inv_categorias),
            ]

        self._mostrar_secundario(botones)
        self.on_inv_existencias()
    
    def on_inv_produccion(self):
        self._limpiar_frame()
        from inventario import InventarioProduccion
        InventarioProduccion(self.frame_contenedor, self.usuario)


    def on_compras(self):
        if not self._solo_admin():
            return
        self._limpiar_contenedor()
        self._mostrar_secundario([
            ("Nueva compra",         self.on_comp_nueva),
            ("Historial de compras", self.on_comp_historial),
            ("Proveedores",          self.on_comp_proveedores),
        ])
        self.on_comp_nueva()

    def on_caja(self):
        self._limpiar_contenedor()

        # Botones base (todos los roles)
        botones = [
            ("Abrir turno",   self.on_caja_abrir),
            ("Corte de caja", self.on_caja_corte),
        ]

        # Movimientos de caja solo para administrador
        if self.rol == "administrador":
            botones.append(("Movimientos de caja", self.on_caja_movimientos))

        self._mostrar_secundario(botones)
        self.on_caja_abrir()

    def on_reportes(self):
        if not self._solo_admin():
            return
        self._limpiar_contenedor()
        self._mostrar_secundario([
            ("Ventas del día",     self.on_rep_dia),
            ("Ventas por período", self.on_rep_periodo),
            ("Cortes anteriores",  self.on_rep_cortes),
        ])
        self.on_rep_dia()

    def on_configuracion(self):
        self._limpiar_contenedor()
        if self.rol == "administrador":
            self._mostrar_secundario([
                ("General",        self.on_conf_general),
                ("Usuarios",       self.on_conf_usuarios),
                ("Mi contraseña",  self.on_conf_contrasena),
            ])
            self.on_conf_general()
        else:
            self._mostrar_secundario([
                ("Mi contraseña", self.on_conf_contrasena),
            ])
            self.on_conf_contrasena()

    # ── Sub-módulos Inventario ────────────────────────────────────────────────

    def on_inv_existencias(self):
        self._limpiar_frame()
        from inventario import InventarioExistencias
        InventarioExistencias(self.frame_contenedor)

    def on_inv_movimientos(self):
        self._limpiar_frame()
        from inventario import InventarioMovimientos
        InventarioMovimientos(self.frame_contenedor)

    def on_inv_ajuste(self):
        self._limpiar_frame()
        from inventario import InventarioAjuste
        InventarioAjuste(self.frame_contenedor, self.usuario)

    def on_inv_articulos(self):
        self._limpiar_frame()
        from inventario import InventarioArticulos
        InventarioArticulos(self.frame_contenedor)

    def on_inv_categorias(self):
        self._limpiar_frame()
        from inventario import InventarioCategorias
        InventarioCategorias(self.frame_contenedor)

    # ── Sub-módulos Compras ───────────────────────────────────────────────────

    def on_comp_nueva(self):
        self._limpiar_frame()
        from compras import ComprasNueva
        ComprasNueva(self.frame_contenedor, self.usuario)

    def on_comp_historial(self):
        self._limpiar_frame()
        from compras import ComprasHistorial
        ComprasHistorial(self.frame_contenedor)

    def on_comp_proveedores(self):
        self._limpiar_frame()
        from compras import ComprasProveedores
        ComprasProveedores(self.frame_contenedor)

    # ── Sub-módulos Caja ──────────────────────────────────────────────────────

    def on_caja_abrir(self):
        self._limpiar_frame()
        from caja import CajaAbrir
        CajaAbrir(self.frame_contenedor, self.usuario)

    def on_caja_corte(self):
        self._limpiar_frame()
        from caja import CajaCorte
        CajaCorte(self.frame_contenedor, self.usuario)

    def on_caja_movimientos(self):
        self._limpiar_frame()
        from caja import CajaMovimientos
        CajaMovimientos(self.frame_contenedor, self.usuario)

    # ── Sub-módulos Reportes ──────────────────────────────────────────────────

    def on_rep_dia(self):
        self._limpiar_frame()
        from reportes import ReportesDia
        ReportesDia(self.frame_contenedor, self.usuario)  # pasa usuario para cancelaciones

    def on_rep_periodo(self):
        self._limpiar_frame()
        from reportes import ReportesPeriodo
        ReportesPeriodo(self.frame_contenedor)

    def on_rep_cortes(self):
        self._limpiar_frame()
        from reportes import ReportesCortes
        ReportesCortes(self.frame_contenedor)

    # ── Sub-módulos Configuración ─────────────────────────────────────────────

    def on_conf_general(self):
        self._limpiar_frame()
        from configuracion import ConfigGeneral
        ConfigGeneral(self.frame_contenedor, self)

    def on_conf_usuarios(self):
        self._limpiar_frame()
        from configuracion import ConfigUsuarios
        ConfigUsuarios(self.frame_contenedor)

    def on_conf_contrasena(self):
        self._limpiar_frame()
        from configuracion import ConfigContrasena
        ConfigContrasena(self.frame_contenedor, self.usuario)

    # ── Utilidades ────────────────────────────────────────────────────────────

    def _limpiar_frame(self):
        """Limpia solo el contenedor sin tocar la barra secundaria."""
        for w in self.frame_contenedor.winfo_children():
            w.destroy()

    # ── Acciones globales ─────────────────────────────────────────────────────

    def on_salir(self):
        self.root.destroy()

    def cambiar_usuario(self):
        self.root.destroy()
        login = VentanaLogin()
        login.run()

    # ── Fecha y hora ──────────────────────────────────────────────────────────

    def actualizar_fecha_hora(self):
        try:
            locale.setlocale(locale.LC_TIME, "Spanish_Spain.1252")
        except:
            pass
        ahora     = datetime.now()
        fecha_str = ahora.strftime("%A %d de %B de %Y").lower()
        hora      = ahora.strftime("%I:%M:%S")
        indicador = "AM" if ahora.hour < 12 else "PM"
        self.lbl_fecha.config(text=fecha_str)
        self.lbl_hora.config(text=f"{hora} {indicador}")
        self.root.after(1000, self.actualizar_fecha_hora)

    # ── Construcción de la UI ─────────────────────────────────────────────────

    def main(self):
        es_admin = self.rol == "administrador"
 
        # ── Cabecera ──────────────────────────────────────────────────────────
        cabecera = tk.Frame(self.root, bg=UI['cabecera_bg'], height=30)
        cabecera.pack(side=tk.TOP, fill=tk.X)
        self.lbl_nombre_negocio = tk.Label(cabecera, text=f"🫓 {self.nombre_negocio}",
                 font=("Tahoma", 10, "bold"),
                 bg=UI['cabecera_bg'],
                 fg=UI['cabecera_fg'])
        self.lbl_nombre_negocio.pack(side=tk.LEFT, padx=10, pady=5)
        tk.Label(cabecera, text=f"Atiende: {self.usuario}",
                 font=("Tahoma", 10, "bold"),
                 bg=UI['cabecera_bg'],
                 fg=UI['cabecera_fg2']).pack(side=tk.RIGHT, padx=10, pady=5)
 
        # ── Menú principal ────────────────────────────────────────────────────
        menu = tk.Frame(self.root, bg=UI['menu_bg'])
        menu.pack(side=tk.TOP, fill=tk.X)
 
        botones_menu = [
            ("Ventas",        self.on_ventas,        True),
            ("Inventario",    self.on_inventario,    True),
            ("Compras",       self.on_compras,       es_admin),
            ("Caja",          self.on_caja,          True),
            ("Reportes",      self.on_reportes,      es_admin),
            ("Configuración", self.on_configuracion, True),
        ]

        for texto, comando, visible in botones_menu:
            if visible:
                ttk.Button(menu, text=texto,
                           style=UI['menu_btn_style'],
                           command=comando,
                           width=14).pack(side=tk.LEFT, padx=4, pady=5)
 
        ttk.Button(menu, text="Salir",
                   style="Peligro.TButton", width=10,
                   command=self.on_salir).pack(side=tk.RIGHT, padx=5, pady=5)
        ttk.Button(menu, text="Cambiar Usuario",
                   style="Cian.TButton", width=15,
                   command=self.cambiar_usuario).pack(side=tk.RIGHT, padx=5, pady=5)
 
        # ── Barra secundaria (sub-módulos) ────────────────────────────────────
        self.frame_secundario = tk.Frame(self.root, bg=UI['secundario_bg'])
        # No se muestra hasta que se active un módulo con sub-menú
 
        # ── Contenedor principal ──────────────────────────────────────────────
        self.frame_contenedor = tk.Frame(self.root, bg=UI['fondo'])
        self.frame_contenedor.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
 
        # ── Barra inferior de fecha/hora ──────────────────────────────────────
        self.frame_horario = tk.Frame(self.root, bg=UI['horario_bg'], height=35)
        self.frame_horario.pack(side=tk.BOTTOM, fill=tk.X)
 
        self.lbl_fecha = tk.Label(self.frame_horario,
                                  bg=UI['horario_bg'],
                                  fg=UI['horario_fg_fecha'],
                                  font=("Tahoma", 11))
        self.lbl_fecha.pack(side=tk.LEFT, padx=10)
 
        self.lbl_hora = tk.Label(self.frame_horario,
                                 bg=UI['horario_bg'],
                                 fg=UI['horario_fg_hora'],
                                 font=("Tahoma", 11))
        self.lbl_hora.pack(side=tk.RIGHT, padx=10)
 
        self.actualizar_fecha_hora()
 
        # Vista por defecto → Ventas
        self.on_ventas()
 
        self.root.mainloop()
        

if __name__ == "__main__":
    app = PuntoDeVenta()
    app.main()