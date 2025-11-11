import os 
import platform
import tempfile
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, colorchooser 
import datetime
import json
from pathlib import Path
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None
from Modulos.Repo import (
    # Productos
    obtener_productos_para_gui, guardar_nuevo_producto,
    obtener_categorias_existentes, obtener_productos_para_venta_gui,
    # Clientes
    obtener_lista_clientes_para_combobox, guardar_nuevo_cliente_desde_gui,
    obtener_clientes_para_tabla_gui,
    obtener_historial_compras_cliente_gui,
    # Ventas
    procesar_nueva_venta_gui, obtener_ventas_para_historial_gui, generar_texto_factura, obtener_venta_para_factura,
    # Proveedores
    obtener_lista_proveedores_para_combobox, obtener_historial_proveedor_gui, guardar_nuevo_proveedor_desde_gui,
    obtener_proveedores_para_tabla_gui,
    actualizar_proveedor, obtener_proveedor_por_id,
    # Usuarios
    autenticar_usuario, crear_usuario, obtener_usuarios_para_gui, eliminar_usuario_por_id, actualizar_password_usuario,
    # Configuracion
    obtener_configuracion_app, guardar_configuracion_app,
    # Productos extra
    obtener_producto_por_id, actualizar_producto,
)
from Modulos.ui_styles import configure_app_styles, get_available_themes, get_theme_palette


BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE_PATH = BASE_DIR / "configuracion_app.json"
DEFAULT_APP_CONFIG = {
    "tema": "sistema",
    "empresa": {
        "nombre": "PyColmado",
        "rnc": "101-00000-1",
        "direccion": "Avenida Ejemplo #123",
        "ciudad": "La Vega, Republica Dominicana",
        "telefono": "809-000-0000",
        "correo": "contacto@pycolmado.com",
        "tagline": "Gestiona inventario, ventas y proveedores desde un solo lugar",
        "logo_path": ""
    },
    "colores_botones": {}
}

def _load_logo_image(path: str, max_size: int = 200):
    if not path:
        return None
    try:
        full_path = Path(path).expanduser()
        if not full_path.exists():
            return None
        if Image and ImageTk:
            img = Image.open(full_path)
            img.thumbnail((max_size, max_size), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        tk_img = tk.PhotoImage(file=str(full_path))
        width, height = tk_img.width(), tk_img.height()
        largest = max(width, height)
        if largest > max_size:
            scale = max(1, int(largest / max_size))
            tk_img = tk_img.subsample(scale, scale)
        return tk_img
    except Exception as exc:
        print(f"Advertencia: no se pudo cargar el logo: {exc}")
        return None


def _draw_default_logo(parent_frame, color):
    canvas = tk.Canvas(parent_frame, bg=color, highlightthickness=0, width=200, height=200)
    canvas.pack(expand=True, padx=20, pady=20)
    cx, cy, r = 100, 100, 60
    canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline="white", width=3)
    canvas.create_line(cx, cy-r, cx, cy+r, fill="white", width=3)
    canvas.create_arc(cx-44, cy-44, cx, cy+44, start=90, extent=180, style="arc", outline="white", width=3)
    canvas.create_arc(cx, cy-44, cx+44, cy+44, start=-90, extent=180, style="arc", outline="white", width=3)
    canvas.create_oval(cx-26, cy-6, cx-8, cy+12, fill="white", outline="")
    canvas.create_oval(cx+8, cy-6, cx+26, cy+12, fill="white", outline="")
    canvas.create_rectangle(0, 0, 240, 40, fill=color, outline="")


def _read_saved_theme_key() -> str:
    try:
        data_db = obtener_configuracion_app()
        if isinstance(data_db, dict):
            return str(data_db.get("tema", "sistema")).lower()
    except Exception:
        pass
    try:
        if CONFIG_FILE_PATH.exists():
            with CONFIG_FILE_PATH.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                return str(data.get("tema", "sistema")).lower()
    except Exception:
        pass
    return "sistema"


class LoginDialog(tk.Toplevel):
    """Diálogo modal de login. Retorna en self.result un dict con 'exito' y 'usuario'."""
    def __init__(self, master):
        super().__init__(master)
        self.empresa_info = self._load_empresa_info()
        self.title(f"Bienvenido a {self.empresa_info.get('nombre', 'PyColmado')}")
        self.resizable(False, False)
        try:
            if master is not None and str(master.state()) != "withdrawn":
                self.transient(master)
        except Exception:
            pass
        self.grab_set()  # Modal
        self.result = {"exito": False, "usuario": None}
        self.colors = configure_app_styles(self, theme_name=_read_saved_theme_key())
        try:
            self.configure(bg=self.colors.get("panel", "#ffffff"))
        except Exception:
            pass

        main = ttk.Frame(self, padding=0)
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(0, weight=0)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        empresa_info = self.empresa_info
        brand_color = self.colors.get("accent", "#2F66FF")

        # Panel izquierdo
        left = tk.Frame(main, bg=brand_color, width=240)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_propagate(False)
        logo_container = tk.Frame(left, bg=brand_color)
        logo_container.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        self._login_logo_img = _load_logo_image(empresa_info.get("logo_path", ""))
        if self._login_logo_img:
            logo_label = tk.Label(logo_container, image=self._login_logo_img, bg=brand_color)
            logo_label.image = self._login_logo_img
            logo_label.pack(expand=True)
        else:
            _draw_default_logo(logo_container, brand_color)

        # Panel derecho (formulario)
        form = tk.Frame(main, bg=self.colors.get("panel", "#ffffff"), padx=40, pady=30)
        form.grid(row=0, column=1, sticky="nsew")
        for i in range(6):
            form.grid_rowconfigure(i, weight=0)
        form.grid_columnconfigure(0, weight=1)

        ttk.Label(form, text=empresa_info.get("nombre", "Sistema PyColmado"), style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(form, text="Ingresa tus credenciales para continuar.", style="Subheader.TLabel").grid(row=1, column=0, sticky="w", pady=(0, 20))

        ttk.Label(form, text="Usuario").grid(row=2, column=0, sticky="w", pady=(0, 2))
        self.user_var = tk.StringVar()
        entry_user = ttk.Entry(form, textvariable=self.user_var, width=36)
        entry_user.grid(row=3, column=0, sticky="ew", pady=(0, 12))

        ttk.Label(form, text="Contraseña").grid(row=4, column=0, sticky="w", pady=(0, 2))
        self.pass_var = tk.StringVar()
        entry_pass = ttk.Entry(form, textvariable=self.pass_var, width=36, show="•")
        entry_pass.grid(row=5, column=0, sticky="ew", pady=(0, 18))

        login_btn = ttk.Button(form, text="Iniciar sesión", style="Accent.TButton", command=self._on_login)
        login_btn.grid(row=6, column=0, sticky="ew")

        # Facilitar login con Enter
        entry_pass.bind("<Return>", lambda e: self._on_login())
        entry_user.bind("<Return>", lambda e: entry_pass.focus_set())
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.after(100, lambda: entry_user.focus_set())

        # Centrar una vez que el loop principal esté activo
        self.after(10, self._center_dialog)

    def _load_empresa_info(self) -> dict:
        info = DEFAULT_APP_CONFIG["empresa"].copy()
        try:
            cfg = obtener_configuracion_app()
            if isinstance(cfg, dict):
                empresa_cfg = cfg.get("empresa")
                if isinstance(empresa_cfg, dict):
                    info.update({k: v for k, v in empresa_cfg.items() if v not in (None, "")})
        except Exception:
            pass
        return info

    def _on_login(self):
        username = self.user_var.get()
        password = self.pass_var.get()
        res = autenticar_usuario(username, password)
        if res.get("exito"):
            self.result = {"exito": True, "usuario": res.get("usuario")}
            self.destroy()
        else:
            messagebox.showerror("Login", res.get("mensaje", "Credenciales inválidas."), parent=self)

    def _on_cancel(self):
        self.result = {"exito": False, "usuario": None}
        self.destroy()

    def _center_dialog(self):
        """Centra el login en pantalla cuando la ventana ya es visible."""
        try:
            self.update_idletasks()
            w = self.winfo_width() or 320
            h = self.winfo_height() or 150
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = int((sw - w) / 2)
            y = int((sh - h) / 3)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass


MARGEN_GANANCIA_POR_DEFECTO = 0.30 # 30% de margen sobre el precio de compra

class ColmadoApp:
    def __init__(self, root_window, current_user: dict | None = None):
        self.root = root_window
        self.app_config = self._load_app_config()
        if "colores_botones" not in self.app_config or not isinstance(self.app_config["colores_botones"], dict):
            self.app_config["colores_botones"] = {}
        self._update_window_title()
        self.root.geometry("1000x750")
        self.available_theme_options = get_available_themes()
        self._theme_label_by_key = {opt["key"]: opt["label"] for opt in self.available_theme_options}
        self._theme_key_by_label = {opt["label"]: opt["key"] for opt in self.available_theme_options}
        self._active_nav_key: str | None = None
        self.current_theme_key = self.app_config.get("tema", "sistema")
        # Estilos y tema de ttk
        self.colors = self._apply_theme(self.current_theme_key)
        # Usuario actual (dict con keys: username, rol, ...)
        self.current_user = current_user or {"username": "(sin login)", "rol": "cajero"}
        # Normalizar rol y configurar permisos por rol
        self._role = str(self.current_user.get("rol", "cajero")).lower()
        self._role_permissions = {
            'admin': {
                'inicio','listar_productos','agregar_producto','nueva_venta','historial_ventas',
                'registrar_proveedor','historial_proveedor','historial_cliente','gestionar_usuarios','configuracion',
                'registrar_cliente',
                'editar_producto','editar_proveedor'
            },
            'cajero': {'inicio','listar_productos','nueva_venta','historial_ventas','registrar_cliente','configuracion'},
            'almacen': {'inicio','agregar_producto','registrar_proveedor','historial_proveedor','editar_proveedor','configuracion'}
        }

        # --- Variables para el formulario de agregar producto ---
        self.nombre_prod_var = tk.StringVar()
        self.precio_compra_prod_var = tk.StringVar()
        self.precio_venta_sin_itbis_prod_var = tk.StringVar()
        self.tasa_itbis_seleccionada_var = tk.DoubleVar(value=0.18) 
        self.itbis_calculado_prod_var = tk.StringVar(value="ITBIS: RD$ 0.00") 
        self.precio_final_calculado_prod_var = tk.StringVar(value="Precio Final: RD$ 0.00")
        self.stock_prod_var = tk.StringVar()
        self.categoria_prod_var = tk.StringVar()
        self.proveedor_nombre_var = tk.StringVar()
        self.proveedores_map = {}
        self.lista_display_proveedores = ["Ninguno"]
        self.lista_categorias = []

        self.nombre_cliente_reg_var = tk.StringVar()
        self.telefono_cliente_reg_var = tk.StringVar()
        self.direccion_cliente_reg_var = tk.StringVar()
        self.cliente_venta_var = tk.StringVar()
        self.producto_venta_seleccionado_var = tk.StringVar()
        self.cantidad_venta_var = tk.StringVar(value="1")
        self.descuento_venta_var = tk.StringVar(value="0")
        self.dinero_recibido_var = tk.StringVar()
        self.cambio_devuelto_var = tk.StringVar()
        self.clientes_venta_map = {}
        self.lista_display_clientes_venta = ["Ninguno"]
        self.productos_para_venta_datos = []
        self.lista_display_productos_venta_original = []
        self.lista_display_productos_venta_filtrada = []
        self.items_en_venta_actual = []
        self.subtotal_bruto_venta_var = tk.DoubleVar(value=0.0)
        self.itbis_total_venta_var = tk.DoubleVar(value=0.0) 
        self.total_neto_venta_var = tk.DoubleVar(value=0.0)
        self.descuento_aplicado_monto_var = tk.DoubleVar(value=0.0)
        self.fecha_inicio_hist_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        self.fecha_fin_hist_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        self.ventas_cargadas_actualmente = []
        self.cliente_hist_seleccionado_var = tk.StringVar()
        self.cliente_hist_info_nombre_var = tk.StringVar()
        self.cliente_hist_info_telefono_var = tk.StringVar()
        self.cliente_hist_info_direccion_var = tk.StringVar()
        self.cliente_hist_total_gastado_var = tk.StringVar()
        self.historial_compras_cliente_actual = [] 
        self.mapa_clientes_historial = {}

        # --- Variables para el formulario de registrar proveedor ---
        self.nombre_proveedor_reg_var = tk.StringVar()
        self.telefono_proveedor_reg_var = tk.StringVar()
        self.direccion_proveedor_reg_var = tk.StringVar()
        # Variables para historial de proveedores (faltaban, se usan en historial_proveedor_action)
        self.proveedor_hist_seleccionado_var = tk.StringVar()
        self.mapa_proveedores_historial = {}

        content_frame = ttk.Frame(self.root, padding="20 20 20 15", style="Background.TFrame")
        content_frame.pack(expand=True, fill=tk.BOTH)

        header_frame = ttk.Frame(content_frame, style="Content.TFrame", padding="16 18")
        header_frame.pack(fill=tk.X, pady=(0, 18))
        header_frame.columnconfigure(0, weight=1)
        empresa_info = self._get_empresa_info()
        ttk.Label(header_frame, text=empresa_info.get("nombre", "Panel principal"), style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header_frame,
            text=empresa_info.get("tagline", "Gestiona inventario, ventas y proveedores desde un solo lugar"),
            style="Subheader.TLabel"
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        ttk.Label(
            header_frame,
            text=f"Sesión: {self.current_user.get('username','')} · Rol: {self.current_user.get('rol','')}",
            style="Badge.TLabel",
            padding=(14, 6)
        ).grid(row=0, column=1, rowspan=2, sticky="e")

        body_frame = ttk.Frame(content_frame, style="Background.TFrame")
        body_frame.pack(fill=tk.BOTH, expand=True)

        actions_frame = self._create_actions_panel(body_frame)

        card_bg = self.colors.get("panel_alt", self.colors.get("panel", self.colors.get("nav_bg", "#ffffff")))
        card_fg = self._get_contrasting_color(card_bg)
        user_card = tk.Frame(actions_frame, bg=card_bg, padx=14, pady=10, highlightthickness=0, bd=0)
        user_card.pack(fill=tk.X, padx=12, pady=(0, 12))
        self.session_card_frame = user_card
        self.session_card_labels = []
        lbl_title = tk.Label(user_card, text="Sesión activa", bg=card_bg, fg=card_fg, font=("Segoe UI", 10, "bold"))
        lbl_title.pack(anchor="w")
        self.session_card_labels.append(lbl_title)
        lbl_user = tk.Label(
            user_card,
            text=f"{self.current_user.get('username','')} · {self.current_user.get('rol','').title()}",
            bg=card_bg,
            fg=card_fg,
            font=("Segoe UI", 10)
        )
        lbl_user.pack(anchor="w", pady=(4, 0))
        self.session_card_labels.append(lbl_user)
        self.nav_clock_label = tk.Label(
            user_card,
            text="",
            bg=card_bg,
            fg=card_fg,
            font=("Segoe UI", 9)
        )
        self.nav_clock_label.pack(anchor="w", pady=(2, 0))
        self.session_card_labels.append(self.nav_clock_label)
        self._start_dashboard_clock(self.nav_clock_label, full_format=False)

        self.nav_buttons = {}
        nav_items = [
            ("Inicio", self.show_welcome_message_in_display, 'inicio'),
            ("Listar Productos", self.listar_productos_action, 'listar_productos'),
            ("Agregar Producto", self.agregar_producto_action, 'agregar_producto'),
            ("Nueva Venta", self.nueva_venta_action, 'nueva_venta'),
            ("Historial de Ventas", self.historial_ventas_action, 'historial_ventas'),
            ("Registrar Proveedor", self.registrar_proveedor_action, 'registrar_proveedor'),
            ("Registrar Cliente", self.registrar_cliente_action, 'registrar_cliente'),
            ("Historial de Proveedor", self.historial_proveedor_action, 'historial_proveedor'),
            ("Historial de Cliente", self.historial_cliente_action, 'historial_cliente'),
            ("Gestionar Usuarios", self.gestionar_usuarios_action, 'gestionar_usuarios'),
            ("Configuración", self.configuracion_action, 'configuracion'),
        ]
        for text, callback, permission in nav_items:
            if self._allowed(permission):
                btn = ttk.Button(actions_frame, text=text, command=callback, style="Nav.TButton")
                btn.pack(fill=tk.X, padx=12, pady=4)
                self.nav_buttons[permission] = btn

        ttk.Separator(actions_frame, orient=tk.HORIZONTAL, style="Nav.TSeparator").pack(fill=tk.X, padx=12, pady=(10, 12))
        btn_salir = ttk.Button(actions_frame, text="Salir", command=self.root.quit, style="Exit.TButton")
        btn_salir.pack(fill=tk.X, padx=12, pady=(6, 0))

        self.display_frame = ttk.Frame(body_frame, padding="20 18", style="Content.TFrame")
        self.display_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self._clear_display_frame()
        self.show_welcome_message_in_display()

    def _clear_display_frame(self):
        for widget in self.display_frame.winfo_children():
            widget.destroy()

    def show_welcome_message_in_display(self):
        self._set_active_nav_action('inicio')
        self._clear_display_frame()
        container = ttk.Frame(self.display_frame, style="Content.TFrame")
        container.pack(expand=True, fill=tk.BOTH)

        ttk.Label(
            container,
            text=f"Bienvenido {self.current_user.get('username','')} ({self.current_user.get('rol','')}).",
            style="Welcome.TLabel"
        ).pack(anchor="w", pady=(0, 4))
        clock_label = ttk.Label(container, text="", style="Subheader.TLabel")
        clock_label.pack(anchor="w", pady=(0, 4))
        self._start_dashboard_clock(clock_label)

        ttk.Label(
            container,
            text="Resumen del sistema",
            style="Subheader.TLabel"
        ).pack(anchor="w", pady=(4, 12))

        stats = self._collect_dashboard_metrics()
        self.dashboard_cards = []
        cards_frame = ttk.Frame(container, style="Content.TFrame")
        cards_frame.pack(fill=tk.X, pady=(0, 14))

        for concepto, valor in stats:
            text = f"{concepto}\n{valor}"
            btn = ttk.Button(
                cards_frame,
                text=text,
                style="Nav.TButton",
                command=(lambda c=concepto: self._on_dashboard_metric_click(c) if c == "Ventas del dia" else None)
            )
            btn.pack(fill=tk.X, pady=4)
            if concepto != "Ventas del dia":
                btn.state(["disabled"])
            self.dashboard_cards.append(btn)

        ttk.Label(
            container,
            text="Seleccione una accion desde el panel izquierdo para continuar.",
            style="Muted.TLabel"
        ).pack(anchor="w", pady=(8, 0))

    def _set_active_nav_action(self, action_key: str | None):
        self._active_nav_key = action_key
        if not hasattr(self, 'nav_buttons'):
            return
        for key, btn in self.nav_buttons.items():
            desired_style = "NavActive.TButton" if action_key == key else "Nav.TButton"
            try:
                btn.configure(style=desired_style)
            except Exception:
                pass

    def _create_actions_panel(self, parent_frame):
        container = ttk.Frame(parent_frame, style="Content.TFrame")
        container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        self.nav_container_frame = container

        canvas_bg = self.colors.get("panel", self.colors.get("nav_bg", "#f0f0f0"))
        self.nav_canvas = tk.Canvas(
            container,
            highlightthickness=0,
            borderwidth=0,
            background=canvas_bg,
            width=240
        )
        self.nav_scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.nav_canvas.yview)
        self.nav_canvas.configure(yscrollcommand=self.nav_scrollbar.set)
        self.nav_canvas.pack(side=tk.LEFT, fill=tk.Y, expand=False)
        if self.nav_canvas.bbox("all"):
            self.nav_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        actions_frame = ttk.Frame(self.nav_canvas, style="Content.TFrame", padding="18 16 18 18")
        ttk.Label(actions_frame, text="Acciones Principales", style="Subheader.TLabel").pack(anchor="w", padx=12, pady=(0, 10))
        self.nav_canvas_window = self.nav_canvas.create_window((0, 0), window=actions_frame, anchor="nw")

        actions_frame.bind(
            "<Configure>",
            lambda e: self._update_nav_scrollregion()
        )
        self.nav_canvas.bind("<Configure>", lambda e: self._update_nav_scrollregion())
        self.nav_canvas.bind("<Enter>", lambda e: self.nav_canvas.bind_all("<MouseWheel>", self._on_nav_mousewheel))
        self.nav_canvas.bind("<Leave>", lambda e: self.nav_canvas.unbind_all("<MouseWheel>"))
        return actions_frame

    def _on_nav_canvas_configure(self, event):
        if hasattr(self, 'nav_canvas_window'):
            self.nav_canvas.itemconfig(self.nav_canvas_window, width=event.width)
        self._update_nav_scrollregion()

    def _update_nav_scrollregion(self):
        if not hasattr(self, 'nav_canvas'):
            return
        self.nav_canvas.configure(scrollregion=self.nav_canvas.bbox("all"))
        bbox = self.nav_canvas.bbox("all")
        if bbox and hasattr(self, 'nav_canvas') and hasattr(self, 'nav_scrollbar'):
            content_height = bbox[3] - bbox[1]
            canvas_height = max(1, self.nav_canvas.winfo_height())
            if content_height > canvas_height:
                self.nav_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            else:
                self.nav_scrollbar.pack_forget()

    def _on_nav_mousewheel(self, event):
        if hasattr(self, 'nav_canvas'):
            try:
                self.nav_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except Exception:
                pass

    def _load_app_config(self) -> dict:
        """Lee la configuracion desde la base de datos, con fallback al JSON legacy."""
        data = json.loads(json.dumps(DEFAULT_APP_CONFIG))  # deep copy defaults
        loaded_from_db = False
        try:
            stored = obtener_configuracion_app()
            if isinstance(stored, dict):
                loaded_from_db = True
                data["tema"] = str(stored.get("tema", data["tema"])).lower()
                stored_empresa = stored.get("empresa") or {}
                empresa_defaults = DEFAULT_APP_CONFIG["empresa"].copy()
                empresa_defaults.update(stored_empresa)
                data["empresa"] = empresa_defaults
                colores = stored.get("colores_botones") or {}
                if isinstance(colores, dict):
                    data["colores_botones"] = colores.copy()
        except Exception as exc:
            print(f"Advertencia: no se pudo leer configuracion desde la base de datos: {exc}")

        if not loaded_from_db:
            try:
                if CONFIG_FILE_PATH.exists():
                    with CONFIG_FILE_PATH.open("r", encoding="utf-8") as fh:
                        stored = json.load(fh)
                    if isinstance(stored, dict):
                        data["tema"] = str(stored.get("tema", data["tema"])).lower()
                        empresa_defaults = DEFAULT_APP_CONFIG["empresa"].copy()
                        empresa_defaults.update(stored.get("empresa") or {})
                        data["empresa"] = empresa_defaults
                        colores = stored.get("colores_botones") or {}
                        if isinstance(colores, dict):
                            data["colores_botones"] = colores.copy()
            except Exception as exc:
                print(f"Advertencia: no se pudo cargar configuracion legacy desde JSON: {exc}")
            # Intentar sembrar la configuracion en la base de datos para futuras lecturas
            try:
                guardar_configuracion_app(data)
            except Exception as exc:
                print(f"Advertencia: no se pudo guardar configuracion inicial en DB: {exc}")

        return data

    def _save_app_config(self):
        try:
            guardar_configuracion_app(self.app_config)
        except Exception as exc:
            print(f"Advertencia: no se pudo guardar configuracion en DB: {exc}")

    def _apply_theme(self, theme_key: str | None):
        self.current_theme_key = (theme_key or "sistema").lower()
        custom_palette = self._compose_custom_palette(self.current_theme_key)
        colors = configure_app_styles(self.root, theme_name=self.current_theme_key, custom_palette=custom_palette)
        self.colors = colors
        self.root.configure(bg=self.colors.get("bg", "#ffffff"))
        # Reaplicar estilo activo en menu
        if hasattr(self, '_active_nav_key'):
            self._set_active_nav_action(self._active_nav_key)
        self._refresh_nav_styles()
        self._refresh_config_styles()
        return colors

    def _compose_custom_palette(self, theme_key: str) -> dict | None:
        overrides = self.app_config.get("colores_botones") or {}
        valid_overrides = {k: v for k, v in overrides.items() if isinstance(v, str) and v.strip()}
        if not valid_overrides:
            return None
        base = get_theme_palette(theme_key)
        base.update(valid_overrides)
        return base

    def _get_empresa_info(self) -> dict:
        return (self.app_config.get("empresa") or DEFAULT_APP_CONFIG["empresa"]).copy()

    def _update_window_title(self):
        empresa_info = self._get_empresa_info()
        empresa_nombre = empresa_info.get("nombre") or DEFAULT_APP_CONFIG["empresa"]["nombre"]
        self.root.title(f"Sistema de Colmado {empresa_nombre}".strip())

    def _aplicar_tema_desde_config(self):
        if not hasattr(self, 'theme_selector_var'):
            return
        selected_label = self.theme_selector_var.get()
        theme_key = self._theme_key_by_label.get(selected_label, "sistema")
        self._apply_theme(theme_key)
        self.app_config["tema"] = theme_key
        self.app_config["colores_botones"] = {}
        self._save_app_config()
        messagebox.showinfo("Tema actualizado", "El tema se aplicó correctamente.", parent=self.display_frame)

    def _guardar_datos_empresa(self):
        if not all(hasattr(self, attr) for attr in [
            'empresa_nombre_var','empresa_rnc_var','empresa_direccion_var',
            'empresa_ciudad_var','empresa_telefono_var','empresa_correo_var'
        ]):
            return
        nombre = self.empresa_nombre_var.get().strip()
        rnc = self.empresa_rnc_var.get().strip()
        direccion = self.empresa_direccion_var.get().strip()
        ciudad = self.empresa_ciudad_var.get().strip()
        telefono = self.empresa_telefono_var.get().strip()
        correo = self.empresa_correo_var.get().strip()
        tagline = self.empresa_tagline_var.get().strip()
        logo_path = self.empresa_logo_var.get().strip()
        if not nombre or not rnc:
            messagebox.showerror("Datos Incompletos", "El nombre y el RNC son obligatorios.", parent=self.display_frame)
            return
        self.app_config["empresa"] = {
            "nombre": nombre,
            "rnc": rnc,
            "direccion": direccion,
            "ciudad": ciudad,
            "telefono": telefono,
            "correo": correo,
            "tagline": tagline or DEFAULT_APP_CONFIG["empresa"]["tagline"],
            "logo_path": logo_path,
        }
        self._save_app_config()
        self._update_window_title()
        messagebox.showinfo("Datos guardados", "La información del negocio se actualizó correctamente.", parent=self.display_frame)

    def _seleccionar_logo_empresa(self):
        if self._role != 'admin':
            return
        path = filedialog.askopenfilename(
            parent=self.display_frame,
            title="Seleccionar logo",
            filetypes=[("PNG", "*.png"), ("GIF", "*.gif"), ("Todos", "*.*")]
        )
        if path:
            self.empresa_logo_var.set(path)

    def _seleccionar_color_boton(self, key: str):
        var = getattr(self, "_color_override_vars", {}).get(key)
        if not var:
            return
        initial = var.get() or self.colors.get(key, "#0f7048")
        color = colorchooser.askcolor(color=initial, parent=self.display_frame)
        if color and color[1]:
            var.set(color[1])

    def _guardar_colores_botones(self):
        if not hasattr(self, "_color_override_vars"):
            return
        overrides = {}
        for key, var in self._color_override_vars.items():
            value = (var.get() or "").strip()
            if value:
                overrides[key] = value
        self.app_config["colores_botones"] = overrides
        self._save_app_config()
        self._apply_theme(self.current_theme_key)
        messagebox.showinfo("Colores actualizados", "Se aplicaron los nuevos colores de botones.", parent=self.display_frame)

    def _restablecer_colores_botones(self):
        if not hasattr(self, "_color_override_vars"):
            return
        for var in self._color_override_vars.values():
            var.set("")
        self.app_config["colores_botones"] = {}
        self._save_app_config()
        self._apply_theme(self.current_theme_key)
        messagebox.showinfo("Colores restablecidos", "Se restauraron los colores por defecto del tema.", parent=self.display_frame)

    def _refresh_nav_styles(self):
        canvas_bg = self.colors.get("panel", self.colors.get("nav_bg", "#f0f0f0"))
        if hasattr(self, 'nav_canvas'):
            self.nav_canvas.configure(background=canvas_bg)
            self._update_nav_scrollregion()
        if hasattr(self, 'nav_container_frame'):
            try:
                self.nav_container_frame.configure(style="Content.TFrame")
            except Exception:
                pass
        self._refresh_session_card_styles()

    def _refresh_session_card_styles(self):
        """Mantiene el card de sesión alineado con la paleta activa."""
        card_frame = getattr(self, 'session_card_frame', None)
        if not card_frame:
            return
        card_bg = self.colors.get("panel_alt", self.colors.get("panel", self.colors.get("nav_bg", "#ffffff")))
        card_fg = self._get_contrasting_color(card_bg)
        try:
            card_frame.configure(bg=card_bg)
        except Exception:
            pass
        for label in getattr(self, 'session_card_labels', []) or []:
            try:
                label.configure(bg=card_bg, fg=card_fg)
            except Exception:
                continue

    def _refresh_config_styles(self):
        panel_color = self.colors.get("panel", "#ffffff")
        if hasattr(self, 'config_wrapper') and self.config_wrapper:
            try:
                self.config_wrapper.configure(bg=panel_color)
            except Exception:
                pass
        if hasattr(self, 'config_canvas') and self.config_canvas:
            try:
                self.config_canvas.configure(bg=panel_color)
            except Exception:
                pass

    @staticmethod
    def _get_contrasting_color(hex_color: str) -> str:
        def _to_rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) if len(h) == 6 else (31, 41, 51)
        try:
            r, g, b = _to_rgb(hex_color)
        except Exception:
            r, g, b = (31, 41, 51)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b)
        return "#1f2933" if luminance > 180 else "#f5f7fa"

    def _collect_dashboard_metrics(self):
        """Genera datos para la tabla de bienvenida."""
        stats = []

        def add_row(label, supplier, formatter=str):
            try:
                value = supplier()
                stats.append((label, formatter(value)))
            except Exception as exc:
                stats.append((label, "N/D"))
                print(f"Advertencia dashboard '{label}': {exc}")

        add_row("Productos activos", lambda: len(obtener_productos_para_gui()))
        add_row("Clientes registrados", lambda: len(obtener_lista_clientes_para_combobox()))
        add_row("Proveedores registrados", lambda: len(obtener_lista_proveedores_para_combobox()))

        def ventas_supplier():
            today = datetime.date.today().strftime("%Y-%m-%d")
            info = obtener_ventas_para_historial_gui(today, today) or {}
            ventas = info.get("ventas_mostradas", [])
            total = float(info.get("total_periodo", 0.0))
            return len(ventas), total

        def ventas_formatter(data):
            cantidad, total = data
            return f"{cantidad} ventas / RD$ {total:,.2f}"

        add_row("Ventas del dia", ventas_supplier, ventas_formatter)

        if not stats:
            stats.append(("Sin datos disponibles", "N/D"))
        return stats

    def _start_dashboard_clock(self, label, full_format: bool = True):
        def _update():
            now = datetime.datetime.now()
            if full_format:
                text = now.strftime("Fecha: %d %b %Y · Hora: %H:%M:%S")
            else:
                text = now.strftime("%d %b %Y · %H:%M:%S")
            try:
                label.config(text=text)
                label.after(1000, _update)
            except Exception:
                pass
        _update()

    def _on_dashboard_metric_click(self, label: str = None):
        if label != "Ventas del dia":
            return
        today = datetime.date.today().strftime("%Y-%m-%d")
        data = obtener_ventas_para_historial_gui(today, today) or {}
        ventas = data.get("ventas_mostradas", [])
        total = float(data.get("total_periodo", 0.0))
        self._mostrar_modal_ventas_dia(ventas, total, today)

    def _mostrar_modal_ventas_dia(self, ventas, total, fecha_str):
        dlg = tk.Toplevel(self.root)
        self._style_toplevel(dlg)
        dlg.title(f"Ventas del {fecha_str}")
        dlg.geometry("760x520")
        dlg.minsize(640, 460)
        dlg.transient(self.root); dlg.grab_set()
        frame = ttk.Frame(dlg, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text=f"Resumen de ventas", style="Header.TLabel").pack(anchor="w", pady=(0, 4))

        filtros = ttk.Frame(frame)
        filtros.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(filtros, text="Desde:").pack(side=tk.LEFT)
        desde_var = tk.StringVar(value=fecha_str)
        hasta_var = tk.StringVar(value=fecha_str)
        entry_desde = ttk.Entry(filtros, textvariable=desde_var, width=12)
        entry_desde.pack(side=tk.LEFT, padx=(4, 12))
        ttk.Label(filtros, text="Hasta:").pack(side=tk.LEFT)
        entry_hasta = ttk.Entry(filtros, textvariable=hasta_var, width=12)
        entry_hasta.pack(side=tk.LEFT, padx=(4, 12))
        ttk.Button(filtros, text="Filtrar", style="Secondary.TButton", command=lambda: cargar_fechas()).pack(side=tk.LEFT)

        total_filtrado = tk.DoubleVar(value=total)
        total_str_var = tk.StringVar(value=f"Total del periodo: RD$ {total:,.2f}")
        info_total = ttk.Label(frame, textvariable=total_str_var, style="Subheader.TLabel")
        info_total.pack(anchor="w", pady=(4, 12))

        cols = ("id", "cliente", "subtotal", "itbis", "descuento", "total")
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=10)
        headers = {
            "id": "ID Venta",
            "cliente": "Cliente",
            "subtotal": "Subtotal s/ITBIS",
            "itbis": "ITBIS",
            "descuento": "Descuento",
            "total": "Total"
        }
        tree.heading("id", text=headers["id"]); tree.column("id", width=80, anchor=tk.CENTER)
        tree.heading("cliente", text=headers["cliente"]); tree.column("cliente", width=150, anchor=tk.W)
        tree.heading("subtotal", text=headers["subtotal"]); tree.column("subtotal", width=120, anchor=tk.E)
        tree.heading("itbis", text=headers["itbis"]); tree.column("itbis", width=100, anchor=tk.E)
        tree.heading("descuento", text=headers["descuento"]); tree.column("descuento", width=110, anchor=tk.E)
        tree.heading("total", text=headers["total"]); tree.column("total", width=110, anchor=tk.E)

        for venta in ventas:
            tree.insert("", tk.END, values=(
                venta.get("id_venta", "N/A"),
                venta.get("nombre_cliente", "N/A"),
                f"RD$ {venta.get('subtotal_bruto_sin_itbis', 0.0):.2f}",
                f"RD$ {venta.get('itbis_total_venta', 0.0):.2f}",
                f"RD$ {venta.get('descuento_aplicado', 0.0):.2f}",
                f"RD$ {venta.get('total_final', 0.0):.2f}"
            ))

        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self._apply_treeview_striping(tree)

        actions = ttk.Frame(dlg, padding=10)
        actions.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(actions, text="Exportar", style="Secondary.TButton", command=lambda: self._exportar_ventas_modal(tree, desde_var.get(), hasta_var.get())).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions, text="Cerrar", style="Secondary.TButton", command=dlg.destroy).pack(side=tk.RIGHT, padx=5)

        def cargar_fechas():
            fecha_ini = desde_var.get().strip()
            fecha_fin = hasta_var.get().strip()
            if not fecha_ini or not fecha_fin:
                messagebox.showerror("Fechas", "Ingrese la fecha inicial y final.", parent=dlg)
                return
            try:
                datetime.datetime.strptime(fecha_ini, "%Y-%m-%d")
                datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Fechas", "Formato inválido (use YYYY-MM-DD).", parent=dlg)
                return
            data = obtener_ventas_para_historial_gui(fecha_ini, fecha_fin) or {}
            ventas_nuevas = data.get("ventas_mostradas", [])
            total_nuevo = float(data.get("total_periodo", 0.0))
            for item in tree.get_children():
                tree.delete(item)
            for venta in ventas_nuevas:
                tree.insert("", tk.END, values=(
                    venta.get("id_venta", "N/A"),
                    venta.get("nombre_cliente", "N/A"),
                    f"RD$ {venta.get('subtotal_bruto_sin_itbis', 0.0):.2f}",
                    f"RD$ {venta.get('itbis_total_venta', 0.0):.2f}",
                    f"RD$ {venta.get('descuento_aplicado', 0.0):.2f}",
                    f"RD$ {venta.get('total_final', 0.0):.2f}"
                ))
            self._apply_treeview_striping(tree)
            total_str_var.set(f"Total del periodo: RD$ {total_nuevo:,.2f}")

    def _exportar_ventas_modal(self, tree: ttk.Treeview, fecha_ini: str, fecha_fin: str):
        ventas = []
        for item in tree.get_children():
            ventas.append(tree.item(item).get("values", []))
        if not ventas:
            messagebox.showwarning("Sin datos", "No hay ventas para exportar.", parent=self.root)
            return
        formato = self._preguntar_formato_exportacion()
        if not formato:
            return

        downloads = Path.home() / "Downloads"
        downloads.mkdir(parents=True, exist_ok=True)
        if formato == "pdf":
            file_path = downloads / f"ventas_{fecha_ini}_{fecha_fin}.pdf"
            try:
                self._exportar_pdf_simple(file_path, ventas, fecha_ini, fecha_fin)
                messagebox.showinfo("Exportación", f"Archivo guardado en:\n{file_path}", parent=self.root)
            except Exception as exc:
                messagebox.showerror("Exportación", f"No se pudo exportar a PDF: {exc}", parent=self.root)
        else:
            file_path = downloads / f"ventas_{fecha_ini}_{fecha_fin}.csv"
            try:
                self._exportar_csv_simple(file_path, ventas)
                messagebox.showinfo("Exportación", f"Archivo guardado en:\n{file_path}", parent=self.root)
            except Exception as exc:
                messagebox.showerror("Exportación", f"No se pudo exportar: {exc}", parent=self.root)

    def _preguntar_formato_exportacion(self):
        opciones = ["Excel (.xlsx)", "PDF (.pdf)"]
        dlg = tk.Toplevel(self.root)
        self._style_toplevel(dlg)
        dlg.title("Exportar ventas")
        dlg.geometry("320x160")
        dlg.transient(self.root); dlg.grab_set()
        ttk.Label(dlg, text="Seleccione formato de exportación:", style="Header.TLabel").pack(pady=(10, 5), padx=12, anchor="w")
        seleccion = tk.StringVar(value=opciones[0])
        combo = ttk.Combobox(dlg, values=opciones, state="readonly", textvariable=seleccion)
        combo.pack(fill=tk.X, padx=12)
        combo.current(0)

        result = {"value": None}
        def confirmar():
            val = seleccion.get()
            result["value"] = "pdf" if "PDF" in val.upper() else "excel"
            dlg.destroy()
        ttk.Button(dlg, text="Exportar", style="Accent.TButton", command=confirmar).pack(pady=(10, 5))
        ttk.Button(dlg, text="Cancelar", style="Secondary.TButton", command=lambda: dlg.destroy()).pack()
        dlg.wait_window()
        return result["value"]

    def _pdf_escape_text(self, text: str) -> str:
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def _exportar_pdf_simple(self, file_path: Path, ventas, fecha_ini: str, fecha_fin: str):
        lines = [
            f"Ventas del periodo {fecha_ini} al {fecha_fin}",
            "",
            "ID Venta | Cliente | Subtotal | ITBIS | Descuento | Total",
        ]
        for row in ventas:
            lines.append(" | ".join(map(str, row)))

        stream_lines = [
            "BT",
            "/F1 11 Tf",
            "1 0 0 1 50 800 Tm",
            "14 TL",
        ]
        for line in lines:
            stream_lines.append(f"({self._pdf_escape_text(line)}) Tj")
            stream_lines.append("T*")
        stream_lines.append("ET")
        stream = "\n".join(stream_lines)
        stream_bytes = stream.encode("latin-1", "replace")

        objects = []
        objects.append("<< /Type /Catalog /Pages 2 0 R >>")
        objects.append("<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
        objects.append("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>")
        objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        objects.append(f"<< /Length {len(stream_bytes)} >>\nstream\n{stream}\nendstream")

        pdf_parts = ["%PDF-1.4"]
        offsets = [0]
        current_offset = len(pdf_parts[0].encode("latin-1"))
        for idx, obj in enumerate(objects, start=1):
            offsets.append(current_offset)
            obj_text = f"\n{idx} 0 obj\n{obj}\nendobj"
            pdf_parts.append(obj_text)
            current_offset += len(obj_text.encode("latin-1"))

        xref_offset = current_offset
        pdf_parts.append("\nxref")
        pdf_parts.append(f"0 {len(objects)+1}")
        pdf_parts.append("0000000000 65535 f ")
        for off in offsets[1:]:
            pdf_parts.append(f"{off:010} 00000 n ")

        pdf_parts.append("trailer")
        pdf_parts.append(f"<< /Size {len(objects)+1} /Root 1 0 R >>")
        pdf_parts.append("startxref")
        pdf_parts.append(str(xref_offset))
        pdf_parts.append("%%EOF")

        with file_path.open("wb") as fh:
            fh.write("".join(pdf_parts).encode("latin-1"))

    def _exportar_csv_simple(self, file_path: Path, ventas):
        with file_path.open("w", encoding="utf-8", newline="") as f:
            f.write("ID Venta;Cliente;Subtotal;ITBIS;Descuento;Total\n")
            for row in ventas:
                f.write(";".join(map(str, row)) + "\n")
    def _allowed(self, action_key: str) -> bool:
        return action_key in self._role_permissions.get(self._role, set()) or self._role == 'admin'

    def _guard(self, action_key: str) -> bool:
        if not self._allowed(action_key):
            messagebox.showerror("Acceso denegado", "No tienes permisos para esta acción.", parent=self.display_frame)
            return False
        return True

    # ------------- Gestión de Usuarios (solo admin) -------------
    def gestionar_usuarios_action(self):
        if self.current_user.get("rol") != "admin":
            messagebox.showerror("Acceso denegado", "Solo un administrador puede gestionar usuarios.", parent=self.display_frame)
            return
        self._set_active_nav_action('gestionar_usuarios')
        self._clear_display_frame()
        frame = ttk.LabelFrame(self.display_frame, text="Gestionar Usuarios (Admin)", padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Formulario alta de usuario
        ttk.Label(frame, text="Usuario:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.nuevo_user_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.nuevo_user_var, width=25).grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(frame, text="Contraseña:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.nuevo_pass_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.nuevo_pass_var, width=25, show="*").grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(frame, text="Rol:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.nuevo_rol_var = tk.StringVar(value="cajero")
        ttk.Combobox(frame, textvariable=self.nuevo_rol_var, values=["admin", "cajero", "almacen"], state="readonly", width=22).grid(row=2, column=1, sticky="w", padx=5, pady=5)

        btns = ttk.Frame(frame)
        btns.grid(row=3, column=0, columnspan=2, pady=8)
        ttk.Button(btns, text="Crear Usuario", command=self._crear_usuario_submit, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text="Eliminar Seleccionado", command=self._eliminar_usuario_submit, style="Exit.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text="Cambiar Contraseña", command=self._abrir_cambiar_contrasena_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text="Refrescar Lista", command=self._refrescar_lista_usuarios).pack(side=tk.LEFT, padx=5)

        # Listado de usuarios actuales
        ttk.Label(frame, text="Usuarios existentes:").grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=(10, 5))
        cols = ("id_u", "username_u", "rol_u")
        self.tree_usuarios = ttk.Treeview(frame, columns=cols, show="headings", height=7)
        self.tree_usuarios.heading("id_u", text="ID"); self.tree_usuarios.column("id_u", width=40, anchor=tk.CENTER, stretch=tk.NO)
        self.tree_usuarios.heading("username_u", text="Usuario"); self.tree_usuarios.column("username_u", width=160, stretch=tk.YES)
        self.tree_usuarios.heading("rol_u", text="Rol"); self.tree_usuarios.column("rol_u", width=100, stretch=tk.NO)
        sb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree_usuarios.yview)
        self.tree_usuarios.configure(yscrollcommand=sb.set)
        sb.grid(row=5, column=2, sticky="ns")
        self.tree_usuarios.grid(row=5, column=0, columnspan=2, sticky="nsew")
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(5, weight=1)
        self._refrescar_lista_usuarios()
        # Ordenamiento en listado de usuarios
        self._enable_treeview_sorting(
            self.tree_usuarios,
            original_headers={"id_u": "ID", "username_u": "Usuario", "rol_u": "Rol"},
            numeric_cols={"id_u"}, money_cols=set()
        )

    def _crear_usuario_submit(self):
        username = self.nuevo_user_var.get()
        password = self.nuevo_pass_var.get()
        rol = self.nuevo_rol_var.get()
        res = crear_usuario(username, password, rol)
        if res.get("exito"):
            messagebox.showinfo("Éxito", res.get("mensaje", "Usuario creado."), parent=self.display_frame)
            self._refrescar_lista_usuarios()
            self.nuevo_user_var.set(""); self.nuevo_pass_var.set(""); self.nuevo_rol_var.set("usuario")
        else:
            messagebox.showerror("Error", res.get("mensaje", "No se pudo crear el usuario."), parent=self.display_frame)

    def _refrescar_lista_usuarios(self):
        if not hasattr(self, 'tree_usuarios'):
            return
        for i in self.tree_usuarios.get_children():
            self.tree_usuarios.delete(i)
        for u in obtener_usuarios_para_gui():
            self.tree_usuarios.insert("", tk.END, values=(u.get("id"), u.get("username"), u.get("rol")))
        self._apply_treeview_striping(self.tree_usuarios)

    def _abrir_cambiar_contrasena_dialog(self):
        if not hasattr(self, 'tree_usuarios'):
            return
        sel = self.tree_usuarios.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Seleccione un usuario de la lista.", parent=self.display_frame)
            return
        vals = self.tree_usuarios.item(sel[0]).get('values', [])
        if not vals:
            return
        try:
            user_id = int(vals[0])
            username = str(vals[1]) if len(vals) > 1 else ''
        except Exception:
            messagebox.showerror("Error", "No se pudo determinar el usuario seleccionado.", parent=self.display_frame)
            return

        dlg = tk.Toplevel(self.root)
        self._style_toplevel(dlg)
        dlg.title(f"Cambiar contraseña de {username}")
        dlg.geometry("360x200")
        dlg.transient(self.root); dlg.grab_set()

        frame = ttk.Frame(dlg, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text=f"Usuario: {username}", style="Subheader.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        ttk.Label(frame, text="Contraseña actual:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        pass_actual_var = tk.StringVar()
        entry_pass_actual = ttk.Entry(frame, textvariable=pass_actual_var, show="*")
        entry_pass_actual.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        ttk.Label(frame, text="Nueva contraseña:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        nueva_pass_var = tk.StringVar()
        entry_pass_nueva = ttk.Entry(frame, textvariable=nueva_pass_var, show="*")
        entry_pass_nueva.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        frame.columnconfigure(1, weight=1)

        def guardar():
            actual = pass_actual_var.get().strip()
            nueva = nueva_pass_var.get().strip()
            if not actual or not nueva:
                messagebox.showerror("Datos incompletos", "Ingrese la nueva contraseña.", parent=dlg); return
            res = actualizar_password_usuario(user_id, actual, nueva)
            if res.get("exito"):
                messagebox.showinfo("Éxito", res.get("mensaje", "Contraseña actualizada."), parent=dlg)
                dlg.destroy()
            else:
                messagebox.showerror("Error", res.get("mensaje", "No se pudo actualizar la contraseña."), parent=dlg)

        btns = ttk.Frame(frame)
        btns.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btns, text="Guardar", command=guardar, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text="Cancelar", command=dlg.destroy, style="Secondary.TButton").pack(side=tk.LEFT, padx=5)

    def _refrescar_tabla_clientes_registrados(self):
        if not hasattr(self, 'tree_clientes_registrados'):
            return
        for item in self.tree_clientes_registrados.get_children():
            self.tree_clientes_registrados.delete(item)
        for cliente in obtener_clientes_para_tabla_gui():
            self.tree_clientes_registrados.insert(
                "",
                tk.END,
                values=(
                    cliente.get("id", ""),
                    cliente.get("nombre", ""),
                    cliente.get("telefono", "") or "N/D",
                    cliente.get("direccion", "") or "",
                ),
            )
        self._apply_treeview_striping(self.tree_clientes_registrados)

    def _refrescar_tabla_proveedores_registrados(self):
        if not hasattr(self, 'tree_proveedores_registrados'):
            return
        for item in self.tree_proveedores_registrados.get_children():
            self.tree_proveedores_registrados.delete(item)
        for proveedor in obtener_proveedores_para_tabla_gui():
            self.tree_proveedores_registrados.insert(
                "",
                tk.END,
                values=(
                    proveedor.get("id", ""),
                    proveedor.get("nombre", ""),
                    proveedor.get("telefono", "") or "N/D",
                    proveedor.get("direccion", "") or "",
                ),
            )
        self._apply_treeview_striping(self.tree_proveedores_registrados)

    def _eliminar_usuario_submit(self):
        if not hasattr(self, 'tree_usuarios'):
            return
        sel = self.tree_usuarios.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Seleccione un usuario para eliminar.", parent=self.display_frame)
            return
        vals = self.tree_usuarios.item(sel[0]).get('values', [])
        if not vals:
            return
        try:
            user_id = int(vals[0])
            username = str(vals[1]) if len(vals) > 1 else ''
        except Exception:
            messagebox.showerror("Error", "No se pudo determinar el usuario seleccionado.", parent=self.display_frame)
            return
        if messagebox.askyesno("Confirmar", f"¿Eliminar el usuario '{username}' (ID {user_id})?", parent=self.display_frame):
            res = eliminar_usuario_por_id(user_id, usuario_actual=self.current_user.get('username'))
            if res.get('exito'):
                messagebox.showinfo("Éxito", res.get('mensaje', 'Usuario eliminado.'), parent=self.display_frame)
                self._refrescar_lista_usuarios()
            else:
                messagebox.showerror("Error", res.get('mensaje', 'No se pudo eliminar el usuario.'), parent=self.display_frame)


    def _abrir_editar_producto_dialog(self, tree_widget):
        """Abre un diálogo para editar el producto seleccionado (solo admin)."""
        if not self._allowed('editar_producto'):
            messagebox.showerror("Acceso denegado", "Solo un administrador puede editar productos.", parent=self.display_frame); return
        sel = tree_widget.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Seleccione un producto de la lista.", parent=self.display_frame); return
        vals = tree_widget.item(sel[0]).get('values', [])
        if not vals:
            return
        try:
            prod_id = int(vals[0])
        except Exception:
            messagebox.showerror("Error", "No se pudo obtener el ID del producto seleccionado.", parent=self.display_frame); return

        prod = obtener_producto_por_id(prod_id)
        if not prod:
            messagebox.showerror("Error", "No se encontró el producto en la base de datos.", parent=self.display_frame); return

        dlg = tk.Toplevel(self.root)
        self._style_toplevel(dlg)
        dlg.title(f"Editar Producto #{prod_id}")
        dlg.geometry("720x520")
        dlg.transient(self.root); dlg.grab_set()
        f = ttk.Frame(dlg, padding=10); f.pack(fill=tk.BOTH, expand=True)

        # Variables
        v_nombre = tk.StringVar(value=prod.get('nombre',''))
        v_desc = tk.StringVar(value=prod.get('descripcion','') or '')
        v_precio_compra = tk.StringVar(value=f"{float(prod.get('precio_compra',0.0)):.2f}")
        v_precio_sin_itbis = tk.StringVar(value=f"{float(prod.get('precio_venta_sin_itbis',0.0)):.2f}")
        v_tasa = tk.DoubleVar(value=float(prod.get('tasa_itbis',0.0)))
        v_aplica = tk.BooleanVar(value=bool(prod.get('aplica_itbis')))
        v_stock = tk.StringVar(value=str(float(prod.get('stock',0.0))))
        v_categoria = tk.StringVar(value=prod.get('categoria','') or '')
        # Proveedor
        provs = obtener_lista_proveedores_para_combobox()
        prov_map = {p['nombre']: p['id'] for p in provs}
        prov_nombre_init = prod.get('proveedor_nombre') or ''
        v_proveedor = tk.StringVar(value=prov_nombre_init if prov_nombre_init in prov_map else '')

        # Diseño simple
        r=0
        ttk.Label(f, text="Nombre:").grid(row=r, column=0, sticky='w'); e_nombre = ttk.Entry(f, textvariable=v_nombre, width=50); e_nombre.grid(row=r, column=1, columnspan=3, sticky='ew', padx=5, pady=5); r+=1
        ttk.Label(f, text="Descripción:").grid(row=r, column=0, sticky='w'); e_desc = ttk.Entry(f, textvariable=v_desc, width=50); e_desc.grid(row=r, column=1, columnspan=3, sticky='ew', padx=5, pady=5); r+=1
        ttk.Label(f, text="Precio Compra:").grid(row=r, column=0, sticky='w'); e_pc = ttk.Entry(f, textvariable=v_precio_compra, width=16); e_pc.grid(row=r, column=1, sticky='w', padx=5, pady=5)
        ttk.Label(f, text="Precio s/ITBIS:").grid(row=r, column=2, sticky='e'); e_ps = ttk.Entry(f, textvariable=v_precio_sin_itbis, width=16); e_ps.grid(row=r, column=3, sticky='w', padx=5, pady=5); r+=1
        ttk.Checkbutton(f, text="Aplica ITBIS", variable=v_aplica).grid(row=r, column=0, sticky='w', padx=5)
        ttk.Label(f, text="Tasa ITBIS:").grid(row=r, column=1, sticky='w');
        tasa_frame = ttk.Frame(f); tasa_frame.grid(row=r, column=2, columnspan=2, sticky='w')
        for tasa in (0.0, 0.10, 0.18, 0.28):
            ttk.Radiobutton(tasa_frame, text=f"{int(tasa*100)}%", variable=v_tasa, value=tasa).pack(side=tk.LEFT, padx=2)
        r+=1
        ttk.Label(f, text="Stock:").grid(row=r, column=0, sticky='w'); e_st = ttk.Entry(f, textvariable=v_stock, width=16); e_st.grid(row=r, column=1, sticky='w', padx=5, pady=5)
        ttk.Label(f, text="Categoría:").grid(row=r, column=2, sticky='e'); e_cat = ttk.Entry(f, textvariable=v_categoria, width=20); e_cat.grid(row=r, column=3, sticky='w', padx=5, pady=5); r+=1
        ttk.Label(f, text="Proveedor:").grid(row=r, column=0, sticky='w'); cb_prov = ttk.Combobox(f, textvariable=v_proveedor, values=list(prov_map.keys()), width=40, state='readonly'); cb_prov.grid(row=r, column=1, columnspan=3, sticky='ew', padx=5, pady=5); r+=1

        btns = ttk.Frame(f); btns.grid(row=r, column=0, columnspan=4, pady=10)
        def guardar():
            try:
                pc = float(v_precio_compra.get().replace(',','.') or 0)
                pv_sin = float(v_precio_sin_itbis.get().replace(',','.') or 0)
                tasa = float(v_tasa.get())
                aplica = bool(v_aplica.get()) and (tasa>0)
                itbis_monto = pv_sin * (tasa if aplica else 0.0)
                precio_final = pv_sin + itbis_monto
                stock = float(v_stock.get().replace(',','.') or 0)
            except ValueError:
                messagebox.showerror("Error", "Valores numéricos inválidos.", parent=dlg); return
            prov_id = prov_map.get(v_proveedor.get()) if v_proveedor.get() in prov_map else None
            datos = {
                'nombre': v_nombre.get(), 'descripcion': v_desc.get(), 'precio_compra': pc,
                'precio_venta_sin_itbis': pv_sin, 'aplica_itbis': aplica, 'tasa_itbis': tasa,
                'itbis_monto_producto': round(itbis_monto,2), 'precio_final_venta': round(precio_final,2),
                'stock': stock, 'categoria': v_categoria.get(), 'proveedor_id': prov_id
            }
            res = actualizar_producto(prod_id, datos)
            if res.get('exito'):
                messagebox.showinfo("Éxito", res.get('mensaje','Actualizado.'), parent=dlg)
                dlg.destroy()
                self.listar_productos_action()
            else:
                messagebox.showerror("Error", res.get('mensaje','No se pudo actualizar.'), parent=dlg)
        ttk.Button(btns, text="Guardar Cambios", command=guardar, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text="Cancelar", command=dlg.destroy).pack(side=tk.LEFT, padx=5)

    # -------- Validadores de entrada --------
    def _validate_numeric(self, proposed: str) -> bool:
        """Valida números decimales; permite vacío (para edición). Admite coma o punto."""
        if proposed == "":
            return True
        try:
            float(proposed.replace(',', '.'))
            return True
        except ValueError:
            return False

    def _validate_numeric_or_percent(self, proposed: str) -> bool: 
        """Valida números decimales o un porcentaje (terminado en %)."""
        if proposed == "":
            return True
        if proposed.endswith('%'):
            core = proposed[:-1]
            if core == "":
                return True
            try:
                float(core.replace(',', '.'))
                return True
            except ValueError:
                return False
        return self._validate_numeric(proposed)

    # -------- Utilidades de ordenamiento en Treeview --------
    def _enable_treeview_sorting(self, tree: ttk.Treeview, original_headers: dict, numeric_cols=None, money_cols=None):
        """Activa ordenamiento clicando encabezados.
        - original_headers: dict col -> texto base del encabezado
        - numeric_cols: set de columnas tratadas como números
        - money_cols: set de columnas con formato monetario 'RD$ ...'
        """
        numeric_cols = numeric_cols or set()
        money_cols = money_cols or set()
        tree_id = id(tree)
        # Guardar textos originales y estado por árbol
        if not hasattr(self, '_tree_headers'):
            self._tree_headers = {}
        if not hasattr(self, '_tree_sort_state'):
            self._tree_sort_state = {}
        self._tree_headers[tree_id] = dict(original_headers)
        self._tree_sort_state[tree_id] = {col: False for col in original_headers.keys()}  # False = asc

        for col in original_headers.keys():
            is_money = col in money_cols
            is_numeric = col in numeric_cols
            tree.heading(col, command=lambda c=col, m=is_money, n=is_numeric: self._on_treeview_heading_click(tree, c, n, m))
        self._apply_treeview_striping(tree)

    def _on_treeview_heading_click(self, tree: ttk.Treeview, col: str, numeric: bool, money: bool):
        tree_id = id(tree)
        reverse = self._tree_sort_state.get(tree_id, {}).get(col, False)
        # Ejecutar ordenamiento
        self._sort_treeview(tree, col, numeric=numeric, money=money, reverse=reverse)
        # Alternar estado para próximo click
        self._tree_sort_state[tree_id][col] = not reverse
        # Actualizar textos de encabezado con flecha
        base_map = self._tree_headers.get(tree_id, {})
        for c, base_text in base_map.items():
            arrow = ''
            if c == col:
                arrow = ' â–²' if not reverse else ' â–¼'
            tree.heading(c, text=f"{base_text}{arrow}")

    def _sort_treeview(self, tree: ttk.Treeview, col: str, numeric: bool, money: bool, reverse: bool = False):
        def parse_value(v):
            s = str(v)
            if money:
                s = s.replace('RD$', '').replace('$', '').replace(',', '.').strip()
                try:
                    return float(s)
                except ValueError:
                    return 0.0
            if numeric:
                try:
                    return float(s.replace(',', '.'))
                except ValueError:
                    return 0.0
            return s.lower()

        items = [(parse_value(tree.set(k, col)), k) for k in tree.get_children('')]
        items.sort(reverse=reverse)
        for index, (_, k) in enumerate(items):
            tree.move(k, '', index)
        self._apply_treeview_striping(tree)

    def _apply_treeview_striping(self, tree: ttk.Treeview | None):
        """Aplica filas alternas para dar contraste a los Treeview."""
        if not tree:
            return
        try:
            if not hasattr(tree, "_striping_configured"):
                tree.tag_configure('evenrow', background=self.colors.get('panel', '#ffffff'), foreground=self.colors.get('text', '#000000'))
                tree.tag_configure('oddrow', background=self.colors.get('panel_alt', '#f4f6fb'), foreground=self.colors.get('text', '#000000'))
                tree._striping_configured = True  # type: ignore[attr-defined]
            for idx, item in enumerate(tree.get_children('')):
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                tree.item(item, tags=(tag,))
        except Exception as exc:
            print(f"Advertencia: no se pudo aplicar striping en Treeview: {exc}")

    def _refrescar_treeview_productos(self, productos):
        tree = getattr(self, 'tree_productos_listado', None)
        if not tree:
            return
        for item in tree.get_children():
            tree.delete(item)
        for producto in productos:
            tree.insert("", tk.END, values=(
                producto.get("id"),
                producto.get("nombre"),
                f"{producto.get('precio', 0.0):.2f}",
                producto.get("stock"),
                producto.get("categoria"),
                producto.get("proveedor")
            ))
        self._apply_treeview_striping(tree)

    def _filtrar_listado_productos(self, event=None):
        if not hasattr(self, 'productos_listados_cache'):
            return
        texto = (self.producto_busqueda_var.get() or "").lower()
        if not texto:
            filtrados = self.productos_listados_cache
        else:
            filtrados = []
            for prod in self.productos_listados_cache:
                cadena = " ".join([
                    str(prod.get("nombre", "")),
                    str(prod.get("categoria", "")),
                    str(prod.get("proveedor", "")),
                    str(prod.get("id", "")),
                ]).lower()
                if texto in cadena:
                    filtrados.append(prod)
        self._refrescar_treeview_productos(filtrados)

    def _style_scrolled_text(self, widget):
        if not widget:
            return
        try:
            widget.configure(
                background=self.colors.get('panel', '#ffffff'),
                foreground=self.colors.get('text', '#000000'),
                insertbackground=self.colors.get('text', '#000000'),
                highlightbackground=self.colors.get('border', '#cccccc'),
                highlightcolor=self.colors.get('accent', '#2b8a8e'),
                highlightthickness=1,
                borderwidth=1,
                relief='solid'
            )
        except Exception as exc:
            print(f"Advertencia: no se pudo aplicar estilo a Text: {exc}")

    def _style_toplevel(self, window):
        if not window:
            return
        try:
            window.configure(bg=self.colors.get("panel", "#ffffff"))
        except Exception:
            pass

    def listar_productos_action(self):
        if not self._guard('listar_productos'):
            return
        self._set_active_nav_action('listar_productos')
        self._clear_display_frame()
        productos = obtener_productos_para_gui()
        self.productos_listados_cache = productos or []
        self.producto_busqueda_var = tk.StringVar()

        search_frame = ttk.Frame(self.display_frame, padding=(0, 0, 0, 4))
        search_frame.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(search_frame, text="Buscar producto:").pack(side=tk.LEFT, padx=(0, 6))
        entry_buscar = ttk.Entry(search_frame, textvariable=self.producto_busqueda_var, width=30)
        entry_buscar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry_buscar.bind("<KeyRelease>", self._filtrar_listado_productos)
        entry_buscar.bind("<Return>", lambda e: (self.tree_productos_listado.focus_set(), "break"))

        if not productos:
            no_data_label = ttk.Label(self.display_frame, text="No hay productos para mostrar.", font=("Arial", 12))
            no_data_label.pack(padx=10, pady=10, anchor="center", expand=True)
            return

        columnas = ("id", "nombre", "precio_final", "stock", "categoria", "proveedor")
        self.tree_productos_listado = ttk.Treeview(self.display_frame, columns=columnas, show="headings", height=15)
        tree = self.tree_productos_listado
        tree.heading("id", text="ID")
        tree.column("id", minwidth=0, width=50, stretch=tk.NO, anchor=tk.CENTER)
        tree.heading("nombre", text="Nombre")
        tree.column("nombre", minwidth=0, width=200, stretch=tk.YES)
        tree.heading("precio_final", text="Precio Venta Final (RD$)")
        tree.column("precio_final", minwidth=0, width=140, stretch=tk.NO, anchor=tk.E)
        tree.heading("stock", text="Stock")
        tree.column("stock", minwidth=0, width=70, stretch=tk.NO, anchor=tk.CENTER)
        tree.heading("categoria", text="Categoria")
        tree.column("categoria", minwidth=0, width=120, stretch=tk.YES)
        tree.heading("proveedor", text="Proveedor")
        tree.column("proveedor", minwidth=0, width=150, stretch=tk.YES)

        scrollbar = ttk.Scrollbar(self.display_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._refrescar_treeview_productos(self.productos_listados_cache)
        # Habilitar ordenamiento por columnas (ID, Precio y Stock numéricos)
        self._enable_treeview_sorting(
            tree,
            original_headers={
                'id': 'ID', 'nombre': 'Nombre', 'precio_final': 'Precio Venta Final (RD$)',
                'stock': 'Stock', 'categoria': 'Categoria', 'proveedor': 'Proveedor'
            },
            numeric_cols={'id', 'stock'}, money_cols={'precio_final'}
        )

        # Acciones para administradores: Editar producto seleccionado
        actions_frame = ttk.Frame(self.display_frame)
        actions_frame.pack(fill=tk.X, pady=6)
        if self._allowed('editar_producto'):
            ttk.Button(actions_frame, text="Editar Producto Seleccionado", command=lambda: self._abrir_editar_producto_dialog(tree), style="Accent.TButton").pack(side=tk.LEFT, padx=5)

    def _cargar_datos_combobox_agregar_prod(self):
        self.lista_categorias = obtener_categorias_existentes()
        # Cargar proveedores reales (no clientes) para el combobox de proveedor en productos
        proveedores_data = obtener_lista_proveedores_para_combobox()
        # Construir mapa Nombre -> ID de proveedor para guardar correctamente proveedor_id en el producto
        self.proveedores_map = {prov["nombre"]: prov["id"] for prov in proveedores_data}
        self.lista_display_proveedores = ["Ninguno"] + sorted(list(self.proveedores_map.keys()))

    def _clear_agregar_producto_form(self):
        self.nombre_prod_var.set("")
        self.precio_compra_prod_var.set("")
        self.precio_venta_sin_itbis_prod_var.set("") 
        self.tasa_itbis_seleccionada_var.set(0.18) 
        if hasattr(self, 'descripcion_prod_text'):
             self.descripcion_prod_text.delete('1.0', tk.END)
        self.stock_prod_var.set("")
        self.categoria_prod_var.set("") 
        self.proveedor_nombre_var.set("Ninguno")
        self._calcular_precio_final_producto() 
        if hasattr(self, 'nombre_entry_prod'):
             self.nombre_entry_prod.focus()

    def _calcular_precio_final_producto(self, event=None, es_por_precio_compra=False, aplica_itbis_actual=None):
        precio_compra = 0.0
        try:
            precio_compra = float(self.precio_compra_prod_var.get().replace(',', '.') or 0)
        except ValueError:
            pass 

        precio_venta_sin_itbis = 0.0
        if es_por_precio_compra and precio_compra > 0: # Solo calcular si precio_compra es válido y mayor a 0
            precio_venta_sin_itbis = precio_compra * (1 + MARGEN_GANANCIA_POR_DEFECTO)
            self.precio_venta_sin_itbis_prod_var.set(f"{precio_venta_sin_itbis:.2f}")
        else: 
            try:
                precio_venta_sin_itbis = float(self.precio_venta_sin_itbis_prod_var.get().replace(',', '.') or 0)
            except ValueError:
                precio_venta_sin_itbis = 0.0
        
        tasa_itbis_seleccionada = self.tasa_itbis_seleccionada_var.get()
        itbis_monto = 0.0
        
        if tasa_itbis_seleccionada > 0:
            itbis_monto = precio_venta_sin_itbis * tasa_itbis_seleccionada
        
        precio_final = precio_venta_sin_itbis + itbis_monto

        self.itbis_calculado_prod_var.set(f"ITBIS ({tasa_itbis_seleccionada*100:.0f}%): RD$ {itbis_monto:.2f}")
        self.precio_final_calculado_prod_var.set(f"Precio Final Venta: RD$ {precio_final:.2f}")
        
        # Estas variables internas no son estrictamente necesarias si _submit_nuevo_producto recalcula
        self._tasa_itbis_para_guardar = tasa_itbis_seleccionada
        self._aplica_itbis_para_guardar = aplica_itbis_actual


    def agregar_producto_action(self):
        if not self._guard('agregar_producto'):
            return
        self._set_active_nav_action('agregar_producto')
        self._clear_display_frame()
        self._cargar_datos_combobox_agregar_prod()
        
        form_frame = ttk.LabelFrame(self.display_frame, text="Agregar Nuevo Producto", padding="15")
        form_frame.pack(padx=10, pady=10, fill=tk.X, anchor="n")

        current_row = 0
        ttk.Label(form_frame, text="Nombre:").grid(row=current_row, column=0, padx=5, pady=5, sticky="w")
        self.nombre_entry_prod = ttk.Entry(form_frame, textvariable=self.nombre_prod_var, width=50)
        self.nombre_entry_prod.grid(row=current_row, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        current_row += 1

        ttk.Label(form_frame, text="Precio Compra (RD$):").grid(row=current_row, column=0, padx=5, pady=5, sticky="w")
        # Validación numérica para precio de compra
        vcmd_num = (self.root.register(self._validate_numeric), '%P')
        self.precio_compra_entry_prod = ttk.Entry(
            form_frame, textvariable=self.precio_compra_prod_var, width=20,
            validate='key', validatecommand=vcmd_num
        )
        self.precio_compra_entry_prod.grid(row=current_row, column=1, padx=5, pady=5, sticky="ew")
        self.precio_compra_entry_prod.bind("<KeyRelease>", lambda event: self._calcular_precio_final_producto(event, es_por_precio_compra=True))
        self.precio_compra_entry_prod.bind("<FocusOut>", lambda event: self._calcular_precio_final_producto(event, es_por_precio_compra=True))
        
        ttk.Label(form_frame, text="Precio Venta s/ITBIS (RD$):").grid(row=current_row, column=2, padx=5, pady=5, sticky="w")
        # Validación numérica para precio de venta sin ITBIS
        self.precio_venta_sin_itbis_entry_prod = ttk.Entry(
            form_frame, textvariable=self.precio_venta_sin_itbis_prod_var, width=20,
            validate='key', validatecommand=vcmd_num
        )
        self.precio_venta_sin_itbis_entry_prod.grid(row=current_row, column=3, padx=5, pady=5, sticky="ew")
        self.precio_venta_sin_itbis_entry_prod.bind("<KeyRelease>", self._calcular_precio_final_producto)
        self.precio_venta_sin_itbis_entry_prod.bind("<FocusOut>", self._calcular_precio_final_producto)
        current_row += 1
        
        ttk.Label(form_frame, text="Tasa ITBIS:").grid(row=current_row, column=0, padx=5, pady=5, sticky="w")
        itbis_frame = ttk.Frame(form_frame)
        itbis_frame.grid(row=current_row, column=1, columnspan=3, padx=5, pady=0, sticky="w")

        ttk.Radiobutton(itbis_frame, text="No ITBIS (0%)", variable=self.tasa_itbis_seleccionada_var, value=0.0, command=self._calcular_precio_final_producto).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(itbis_frame, text="10%", variable=self.tasa_itbis_seleccionada_var, value=0.10, command=self._calcular_precio_final_producto).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(itbis_frame, text="18%", variable=self.tasa_itbis_seleccionada_var, value=0.18, command=self._calcular_precio_final_producto).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(itbis_frame, text="28%", variable=self.tasa_itbis_seleccionada_var, value=0.28, command=self._calcular_precio_final_producto).pack(side=tk.LEFT, padx=2)
        current_row += 1
        
        ttk.Label(form_frame, textvariable=self.itbis_calculado_prod_var, font=("Arial", 9, "italic")).grid(row=current_row, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(form_frame, textvariable=self.precio_final_calculado_prod_var, font=("Arial", 10, "bold")).grid(row=current_row, column=2, columnspan=2, padx=5, pady=2, sticky="ew")
        current_row += 1

        ttk.Label(form_frame, text="Descripcion (Opcional):").grid(row=current_row, column=0, padx=5, pady=5, sticky="nw")
        self.descripcion_prod_text = scrolledtext.ScrolledText(form_frame, width=48, height=3, wrap=tk.WORD, font=("Arial",9))
        self.descripcion_prod_text.grid(row=current_row, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        self._style_scrolled_text(self.descripcion_prod_text)
        current_row += 1
        
        ttk.Label(form_frame, text="Stock Inicial:").grid(row=current_row, column=0, padx=5, pady=5, sticky="w")
        # Validación numérica para stock inicial
        self.stock_entry_prod = ttk.Entry(
            form_frame, textvariable=self.stock_prod_var, width=20,
            validate='key', validatecommand=vcmd_num
        )
        self.stock_entry_prod.grid(row=current_row, column=1, padx=5, pady=5, sticky="ew")
        current_row += 1
        
        ttk.Label(form_frame, text="Categoria:").grid(row=current_row, column=0, padx=5, pady=5, sticky="w")
        self.categoria_combo_prod = ttk.Combobox(form_frame, textvariable=self.categoria_prod_var, values=self.lista_categorias, width=48)
        self.categoria_combo_prod.grid(row=current_row, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        current_row += 1
        
        ttk.Label(form_frame, text="Proveedor:").grid(row=current_row, column=0, padx=5, pady=5, sticky="w")
        self.proveedor_combo_prod = ttk.Combobox(form_frame, textvariable=self.proveedor_nombre_var,
                                       values=self.lista_display_proveedores, width=48, state="readonly")
        self.proveedor_combo_prod.grid(row=current_row, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        current_row += 1

        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=current_row, column=0, columnspan=4, pady=15)
        ttk.Button(buttons_frame, text="Guardar Producto", command=self._submit_nuevo_producto, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Limpiar Formulario", command=self._clear_agregar_producto_form, style="Secondary.TButton").pack(side=tk.LEFT, padx=5)
        
        for i in range(4): 
            form_frame.columnconfigure(i, weight=1 if i > 0 else 0)

        self._clear_agregar_producto_form()
        self._calcular_precio_final_producto() 

    def _submit_nuevo_producto(self):
        nombre = self.nombre_prod_var.get()
        try:
            precio_compra_str = self.precio_compra_prod_var.get().replace(',', '.')
            precio_compra = float(precio_compra_str) if precio_compra_str else 0.0
        except ValueError:
            messagebox.showerror("Error de Validacion", "Precio de compra debe ser un numero valido.", parent=self.display_frame)
            return

        try:
            precio_venta_sin_itbis_str = self.precio_venta_sin_itbis_prod_var.get().replace(',', '.')
            precio_venta_sin_itbis = float(precio_venta_sin_itbis_str) if precio_venta_sin_itbis_str else 0.0
        except ValueError:
            messagebox.showerror("Error de Validacion", "Precio de venta sin ITBIS debe ser un numero valido.", parent=self.display_frame)
            return
        
        descripcion = self.descripcion_prod_text.get("1.0", tk.END).strip()
        stock_str = self.stock_prod_var.get()
        categoria = self.categoria_prod_var.get()
        proveedor_nombre_seleccionado = self.proveedor_nombre_var.get()

        if not nombre.strip(): 
            messagebox.showerror("Error de Validacion", "El nombre del producto no puede estar vacio.", parent=self.display_frame)
            return
        if not stock_str.strip():
             messagebox.showerror("Error de Validacion", "El stock inicial no puede estar vacio.", parent=self.display_frame)
             return
        try:
            stock = float(stock_str.replace(',', '.')) 
        except ValueError:
            messagebox.showerror("Error de Validacion", "Stock debe ser un numero valido.", parent=self.display_frame)
            return

        tasa_itbis_final = self.tasa_itbis_seleccionada_var.get()
        aplica_itbis_final = True if tasa_itbis_final > 0 else False
        itbis_monto_final = precio_venta_sin_itbis * tasa_itbis_final
        precio_final_calculado = precio_venta_sin_itbis + itbis_monto_final
            
        proveedor_id_para_guardar = None 
        if proveedor_nombre_seleccionado != "Ninguno" and proveedor_nombre_seleccionado in self.proveedores_map:
            proveedor_id_para_guardar = self.proveedores_map[proveedor_nombre_seleccionado]
        
        datos_producto_nuevo = {
            "nombre": nombre,
            "precio_compra": precio_compra,
            "precio_venta_sin_itbis": precio_venta_sin_itbis,
            "aplica_itbis": aplica_itbis_final, 
            "tasa_itbis": tasa_itbis_final,     
            "itbis_monto_producto": round(itbis_monto_final, 2),
            "precio_final_venta": round(precio_final_calculado, 2),
            "descripcion": descripcion,
            "stock": stock,
            "categoria": categoria,
            "proveedor_id": proveedor_id_para_guardar
        }
        
        resultado = guardar_nuevo_producto(datos_producto_nuevo) 

        if resultado["exito"]:
            messagebox.showinfo("Exito", resultado["mensaje"], parent=self.display_frame)
            self._clear_agregar_producto_form()
            self._cargar_datos_para_nueva_venta() 
            if hasattr(self, 'producto_venta_combo'):
                self.producto_venta_combo['values'] = self.lista_display_productos_venta_filtrada
        else:
            messagebox.showerror("Error al Guardar", resultado["mensaje"], parent=self.display_frame)

    def _clear_registrar_cliente_form(self):
        self.nombre_cliente_reg_var.set("")
        self.telefono_cliente_reg_var.set("")
        self.direccion_cliente_reg_var.set("")
        if hasattr(self, 'nombre_cliente_entry_reg'):
            self.nombre_cliente_entry_reg.focus()

    def _submit_nuevo_cliente(self):
        nombre = self.nombre_cliente_reg_var.get()
        telefono = self.telefono_cliente_reg_var.get()
        direccion = self.direccion_cliente_reg_var.get()
        if not nombre.strip() or not telefono.strip():
            messagebox.showerror("Error de Validacion", "El nombre y el telefono del cliente no pueden estar vacios.", parent=self.display_frame)
            return
        resultado = guardar_nuevo_cliente_desde_gui(nombre, telefono, direccion)
        if resultado["exito"]:
            messagebox.showinfo("Exito", resultado["mensaje"], parent=self.display_frame)
            self._clear_registrar_cliente_form()
            self._cargar_datos_para_nueva_venta()
            if hasattr(self, 'cliente_venta_combo'): self.cliente_venta_combo['values'] = self.lista_display_clientes_venta
            self._cargar_datos_combobox_agregar_prod()
            if hasattr(self, 'proveedor_combo_prod'): self.proveedor_combo_prod['values'] = self.lista_display_proveedores
            self._refrescar_tabla_clientes_registrados()
        else: messagebox.showerror("Error al Guardar", resultado["mensaje"], parent=self.display_frame)

    def registrar_cliente_action(self):
        if not self._guard('registrar_cliente'):
            return
        self._set_active_nav_action('registrar_cliente')
        self._clear_display_frame()
        form_frame = ttk.LabelFrame(self.display_frame, text="Registrar Nuevo Cliente", padding="15")
        form_frame.pack(padx=10, pady=10, fill=tk.X, anchor="n")
        ttk.Label(form_frame, text="Nombre Completo:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.nombre_cliente_entry_reg = ttk.Entry(form_frame, textvariable=self.nombre_cliente_reg_var, width=40)
        self.nombre_cliente_entry_reg.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(form_frame, text="Telefono:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(form_frame, textvariable=self.telefono_cliente_reg_var, width=40).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(form_frame, text="Direccion (Opcional):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(form_frame, textvariable=self.direccion_cliente_reg_var, width=40).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=15)
        ttk.Button(buttons_frame, text="Guardar Cliente", command=self._submit_nuevo_cliente, style='Accent.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(buttons_frame, text="Limpiar Formulario", command=self._clear_registrar_cliente_form, style="Secondary.TButton").pack(side=tk.LEFT, padx=10)
        form_frame.columnconfigure(1, weight=1)
        self._clear_registrar_cliente_form()

        tabla_frame = ttk.LabelFrame(self.display_frame, text="Clientes Registrados", padding="10")
        tabla_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        columnas = ("id_c", "nombre_c", "telefono_c", "direccion_c")
        self.tree_clientes_registrados = ttk.Treeview(tabla_frame, columns=columnas, show="headings", height=8)
        self.tree_clientes_registrados.heading("id_c", text="ID")
        self.tree_clientes_registrados.heading("nombre_c", text="Nombre")
        self.tree_clientes_registrados.heading("telefono_c", text="Teléfono")
        self.tree_clientes_registrados.heading("direccion_c", text="Dirección")
        self.tree_clientes_registrados.column("id_c", width=60, anchor=tk.CENTER, stretch=tk.NO)
        self.tree_clientes_registrados.column("nombre_c", width=200, anchor=tk.W, stretch=tk.YES)
        self.tree_clientes_registrados.column("telefono_c", width=120, anchor=tk.CENTER, stretch=tk.NO)
        self.tree_clientes_registrados.column("direccion_c", width=260, anchor=tk.W, stretch=tk.YES)
        sb_clientes = ttk.Scrollbar(tabla_frame, orient=tk.VERTICAL, command=self.tree_clientes_registrados.yview)
        self.tree_clientes_registrados.configure(yscrollcommand=sb_clientes.set)
        self.tree_clientes_registrados.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_clientes.pack(side=tk.RIGHT, fill=tk.Y)
        self._refrescar_tabla_clientes_registrados()
        self._enable_treeview_sorting(
            self.tree_clientes_registrados,
            original_headers={
                "id_c": "ID",
                "nombre_c": "Nombre",
                "telefono_c": "Teléfono",
                "direccion_c": "Dirección",
            },
            numeric_cols={"id_c"},
            money_cols=set(),
        )


    def registrar_proveedor_action(self):
        if not self._guard('registrar_proveedor'):
            return
        self._set_active_nav_action('registrar_proveedor')
        self._clear_display_frame()
        form_frame = ttk.LabelFrame(self.display_frame, text="Registrar Nuevo Proveedor", padding="15")
        form_frame.pack(padx=10, pady=10, fill=tk.X, anchor="n")
        ttk.Label(form_frame, text="Nombre Completo:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.nombre_proveedor_entry_reg = ttk.Entry(form_frame, textvariable=self.nombre_proveedor_reg_var, width=40)
        self.nombre_proveedor_entry_reg.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(form_frame, text="Telefono:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(form_frame, textvariable=self.telefono_proveedor_reg_var, width=40).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(form_frame, text="Direccion (Opcional):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(form_frame, textvariable=self.direccion_proveedor_reg_var, width=40).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=15)
        # Guardar nuevo proveedor (método implementado abajo)
        ttk.Button(buttons_frame, text="Guardar Proveedor", command=self._submit_nuevo_proveedor, style="Accent.TButton").pack(side=tk.LEFT, padx=10)
        # Limpiar solo campos de proveedor
        ttk.Button(buttons_frame, text="Limpiar Formulario", command=self._clear_registrar_proveedor_form, style="Secondary.TButton").pack(side=tk.LEFT, padx=10)
        form_frame.columnconfigure(1, weight=1)
        self._clear_registrar_proveedor_form()

        tabla_frame = ttk.LabelFrame(self.display_frame, text="Proveedores Registrados", padding="10")
        tabla_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        columnas = ("id_p", "nombre_p", "telefono_p", "direccion_p")
        self.tree_proveedores_registrados = ttk.Treeview(tabla_frame, columns=columnas, show="headings", height=8)
        self.tree_proveedores_registrados.heading("id_p", text="ID")
        self.tree_proveedores_registrados.heading("nombre_p", text="Nombre")
        self.tree_proveedores_registrados.heading("telefono_p", text="Teléfono")
        self.tree_proveedores_registrados.heading("direccion_p", text="Dirección")
        self.tree_proveedores_registrados.column("id_p", width=60, anchor=tk.CENTER, stretch=tk.NO)
        self.tree_proveedores_registrados.column("nombre_p", width=220, anchor=tk.W, stretch=tk.YES)
        self.tree_proveedores_registrados.column("telefono_p", width=130, anchor=tk.CENTER, stretch=tk.NO)
        self.tree_proveedores_registrados.column("direccion_p", width=260, anchor=tk.W, stretch=tk.YES)
        sb_proveedores = ttk.Scrollbar(tabla_frame, orient=tk.VERTICAL, command=self.tree_proveedores_registrados.yview)
        self.tree_proveedores_registrados.configure(yscrollcommand=sb_proveedores.set)
        self.tree_proveedores_registrados.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_proveedores.pack(side=tk.RIGHT, fill=tk.Y)
        self._refrescar_tabla_proveedores_registrados()
        self._enable_treeview_sorting(
            self.tree_proveedores_registrados,
            original_headers={
                "id_p": "ID",
                "nombre_p": "Nombre",
                "telefono_p": "Teléfono",
                "direccion_p": "Dirección",
            },
            numeric_cols={"id_p"},
            money_cols=set(),
        )

    def _clear_registrar_proveedor_form(self):
        """Limpia el formulario de registro de proveedores."""
        self.nombre_proveedor_reg_var.set("")
        self.telefono_proveedor_reg_var.set("")
        self.direccion_proveedor_reg_var.set("")
        if hasattr(self, 'nombre_proveedor_entry_reg'):
            self.nombre_proveedor_entry_reg.focus()

    def _submit_nuevo_proveedor(self):
        """Guarda un nuevo proveedor usando el módulo Proveedores y refresca combos relacionados."""
        nombre = self.nombre_proveedor_reg_var.get()
        telefono = self.telefono_proveedor_reg_var.get()
        direccion = self.direccion_proveedor_reg_var.get()
        if not nombre.strip() or not telefono.strip():
            messagebox.showerror(
                "Error de Validacion",
                "El nombre y el telefono del proveedor no pueden estar vacios.",
                parent=self.display_frame,
            )
            return
        resultado = guardar_nuevo_proveedor_desde_gui(nombre, telefono, direccion)
        if resultado.get("exito"):
            messagebox.showinfo("Exito", resultado.get("mensaje", "Proveedor guardado."), parent=self.display_frame)
            # Limpiar formulario y refrescar combos que dependan de proveedores
            self._clear_registrar_proveedor_form()
            self._cargar_datos_combobox_agregar_prod()
            if hasattr(self, 'proveedor_combo_prod'):
                self.proveedor_combo_prod['values'] = self.lista_display_proveedores
            # Si la vista de historial de proveedores está abierta, recargar su combobox
            if hasattr(self, 'proveedor_hist_combo'):
                self._cargar_proveedores_para_historial_combo()
            self._refrescar_tabla_proveedores_registrados()
        else:
            messagebox.showerror("Error al Guardar", resultado.get("mensaje", "No se pudo guardar el proveedor."), parent=self.display_frame)

    def _on_producto_venta_keyup(self, event=None):
        texto_busqueda = self.producto_venta_seleccionado_var.get().lower()
        if not texto_busqueda:
            self.lista_display_productos_venta_filtrada = self.lista_display_productos_venta_original[:]
        else:
            self.lista_display_productos_venta_filtrada = [
                item_display for item_display in self.lista_display_productos_venta_original
                if texto_busqueda in item_display.lower()
            ]
        current_text_in_box = self.producto_venta_combo.get()
        self.producto_venta_combo['values'] = self.lista_display_productos_venta_filtrada
        self.producto_venta_combo.delete(0, tk.END)
        self.producto_venta_combo.insert(0, current_text_in_box)
        self.producto_venta_combo.icursor(tk.END)
        if self.lista_display_productos_venta_filtrada and self.root.focus_get() == self.producto_venta_combo:
            try:
                self.producto_venta_combo.event_generate("<Down>")
                # Restaurar texto después de abrir el dropdown
                self.producto_venta_combo.delete(0, tk.END)
                self.producto_venta_combo.insert(0, current_text_in_box)
                self.producto_venta_combo.icursor(tk.END)
            except Exception:
                pass

    def _agregar_item_a_venta_actual_event(self, event=None):
        self._agregar_item_a_venta_actual()
        return "break"

    def _confirmar_venta_action_event(self, event=None):
        self._confirmar_venta_action()
        return "break"

    def _cargar_datos_para_nueva_venta(self):
        clientes_data = obtener_lista_clientes_para_combobox()
        self.clientes_venta_map = {cliente["nombre"]: cliente["id"] for cliente in clientes_data}
        self.lista_display_clientes_venta = ["Ninguno"] + sorted(list(self.clientes_venta_map.keys()))

        self.productos_para_venta_datos = obtener_productos_para_venta_gui() 
        self.lista_display_productos_venta_original = []
        for p in self.productos_para_venta_datos:
            precio_a_mostrar = p.get('precio_final_venta', p.get('precio', 0.0))
            display_text = f"{p.get('id','N/A')} - {p.get('nombre','N/A')} (Precio: RD$ {precio_a_mostrar:.2f} - Stock: {p.get('stock',0)})"
            self.lista_display_productos_venta_original.append(display_text)
        self.lista_display_productos_venta_filtrada = self.lista_display_productos_venta_original[:]
    
    def _actualizar_info_producto_seleccionado_venta(self, event=None):
        seleccion_actual_str = self.producto_venta_seleccionado_var.get()
        if not seleccion_actual_str or not self.productos_para_venta_datos:
            if hasattr(self, 'stock_disponible_venta_label'): self.stock_disponible_venta_label.config(text="Stock Disp: -")
            if hasattr(self, 'precio_unitario_venta_label'): self.precio_unitario_venta_label.config(text="Precio U: -")
            return

        try:
            producto_id_seleccionado = int(seleccion_actual_str.split(" - ")[0])
            producto_info = next((p for p in self.productos_para_venta_datos if p.get("id") == producto_id_seleccionado), None)

            if producto_info:
                stock_ya_en_cesta = 0.0
                item_en_cesta = next((item for item in self.items_en_venta_actual if item.get("id") == producto_id_seleccionado), None)
                if item_en_cesta: stock_ya_en_cesta = float(item_en_cesta.get("cantidad",0))
                
                stock_visual_disponible = float(producto_info.get('stock', 0)) - stock_ya_en_cesta
                self.stock_disponible_venta_label.config(text=f"Stock Disp: {stock_visual_disponible:.2f}")
                precio_unit_venta_final = float(producto_info.get('precio_final_venta', producto_info.get('precio',0.0)))
                self.precio_unitario_venta_label.config(text=f"Precio U: RD$ {precio_unit_venta_final:.2f}")
            else:
                self.stock_disponible_venta_label.config(text="Stock Disp: -")
                self.precio_unitario_venta_label.config(text="Precio U: -")
        except (ValueError, IndexError): 
            self.stock_disponible_venta_label.config(text="Stock Disp: -")
            self.precio_unitario_venta_label.config(text="Precio U: -")
        except Exception as e:
            print(f"Error actualizando info producto (GUI): {e}")
            self.stock_disponible_venta_label.config(text="Stock Disp: Error")
            self.precio_unitario_venta_label.config(text="Precio U: Error")

    def _agregar_item_a_venta_actual(self):
        producto_seleccionado_str = self.producto_venta_seleccionado_var.get()
        cantidad_str = self.cantidad_venta_var.get()

        if not producto_seleccionado_str:
            messagebox.showwarning("Producto no seleccionado", "Por favor, seleccione un producto de la lista.", parent=self.display_frame)
            return

        try:
            cantidad_a_agregar = float(cantidad_str.replace(',', '.')) 
            if cantidad_a_agregar <= 0:
                messagebox.showwarning("Cantidad Invalida", "La cantidad debe ser mayor a cero.", parent=self.display_frame)
                return
        except ValueError:
            messagebox.showwarning("Cantidad Invalida", "La cantidad debe ser un numero valido (ej: 1 o 0.5).", parent=self.display_frame)
            return

        try:
            producto_id = int(producto_seleccionado_str.split(" - ")[0])
            producto_info_original = next((p for p in self.productos_para_venta_datos if p.get("id") == producto_id), None)

            if not producto_info_original:
                messagebox.showerror("Error de Producto", "El producto seleccionado no es valido.", parent=self.display_frame)
                return

            item_existente_en_cesta = next((item for item in self.items_en_venta_actual if item.get("id") == producto_id), None)
            cantidad_ya_en_cesta = float(item_existente_en_cesta.get("cantidad",0.0)) if item_existente_en_cesta else 0.0
            stock_original_producto = float(producto_info_original.get('stock', 0))

            if stock_original_producto != 0 and (cantidad_ya_en_cesta + cantidad_a_agregar) > stock_original_producto:
                messagebox.showwarning("Stock Insuficiente",
                                       f"No hay suficiente stock para '{producto_info_original.get('nombre','N/A')}'.\n"
                                       f"Stock actual: {stock_original_producto}\n"
                                       f"Ya en carrito: {cantidad_ya_en_cesta}\n"
                                       f"Intentando agregar: {cantidad_a_agregar}\n"
                                       f"Maximo adicional posible: {stock_original_producto - cantidad_ya_en_cesta:.2f}",
                                       parent=self.display_frame)
                return
            
            precio_unitario_item_venta = float(producto_info_original.get('precio_final_venta', producto_info_original.get('precio',0.0)))
            precio_sin_itbis_item = float(producto_info_original.get('precio_venta_sin_itbis', precio_unitario_item_venta))
            itbis_del_item_unitario = 0.0
            if producto_info_original.get('aplica_itbis'): 
                itbis_del_item_unitario = precio_unitario_item_venta - precio_sin_itbis_item

            if item_existente_en_cesta:
                item_existente_en_cesta["cantidad"] += cantidad_a_agregar
                item_existente_en_cesta["subtotal"] = item_existente_en_cesta["cantidad"] * item_existente_en_cesta["precio_unitario"]
                item_existente_en_cesta["itbis_item_total"] = item_existente_en_cesta["cantidad"] * itbis_del_item_unitario 
            else:
                self.items_en_venta_actual.append({
                    "id": producto_info_original.get("id"), 
                    "nombre": producto_info_original.get("nombre"),
                    "cantidad": cantidad_a_agregar,
                    "precio_unitario": precio_unitario_item_venta, 
                    "subtotal": cantidad_a_agregar * precio_unitario_item_venta,
                    "itbis_item_total": cantidad_a_agregar * itbis_del_item_unitario 
                })

            self._actualizar_treeview_items_venta()
            self._actualizar_sumario_venta() 
            self._actualizar_info_producto_seleccionado_venta()
            self.cantidad_venta_var.set("1") 
            if hasattr(self, 'cantidad_venta_entry'): self.cantidad_venta_entry.focus()

        except (ValueError, IndexError) as e:
            print(f"Error de seleccion o valor al agregar item: {e}, string: '{producto_seleccionado_str}'")
            messagebox.showerror("Error de Seleccion/Valor", "Producto o valor no valido al agregar item.", parent=self.display_frame)
        except Exception as e:
            print(f"Error general al agregar item: {e}")
            messagebox.showerror("Error al agregar", f"Ocurrio un error inesperado: {e}", parent=self.display_frame)
    
    def _actualizar_treeview_items_venta(self):
        if hasattr(self, 'tree_items_venta'):
            for i in self.tree_items_venta.get_children():
                self.tree_items_venta.delete(i)
            for item in self.items_en_venta_actual:
                self.tree_items_venta.insert("", tk.END, values=(
                    item.get("id"),
                    item.get("nombre"),
                    f"{item.get('cantidad'):.2f}" if isinstance(item.get('cantidad'), float) else item.get('cantidad'),
                    f"RD$ {item.get('precio_unitario', 0.0):.2f}",
                    f"RD$ {item.get('subtotal', 0.0):.2f}"
                ))
            self._apply_treeview_striping(self.tree_items_venta)
    
    def _eliminar_item_de_venta_actual(self):
        if not hasattr(self, 'tree_items_venta'): return
        seleccion = self.tree_items_venta.selection()
        if not seleccion: 
            messagebox.showwarning("Nada seleccionado", "Seleccione un producto de la lista para eliminar.", parent=self.display_frame)
            return

        item_seleccionado_values = self.tree_items_venta.item(seleccion[0])["values"]
        if not item_seleccionado_values: return

        item_seleccionado_id_tree = item_seleccionado_values[0]

        self.items_en_venta_actual = [item for item in self.items_en_venta_actual if str(item.get("id")) != str(item_seleccionado_id_tree)]
        self._actualizar_treeview_items_venta()
        self._actualizar_sumario_venta()
        self._actualizar_info_producto_seleccionado_venta()

    def _actualizar_sumario_venta(self, event=None):
        subtotal_con_itbis_antes_descuento = 0.0
        itbis_total_de_la_venta = 0.0

        for item in self.items_en_venta_actual:
            subtotal_con_itbis_antes_descuento += item.get("subtotal", 0.0) 
            itbis_total_de_la_venta += item.get("itbis_item_total", 0.0) 

        self.subtotal_bruto_venta_var.set(round(subtotal_con_itbis_antes_descuento, 2))
        self.itbis_total_venta_var.set(round(itbis_total_de_la_venta, 2))
        
        descuento_str = self.descuento_venta_var.get().strip()
        monto_descuento = 0.0
        if descuento_str:
            try:
                if "%" in descuento_str:
                    porcentaje = float(descuento_str.replace("%", "").replace(',','.'))
                    if 0 <= porcentaje <= 100:
                        monto_descuento = subtotal_con_itbis_antes_descuento * (porcentaje / 100)
                    else: self.descuento_venta_var.set("0")
                else: 
                    monto_fijo = float(descuento_str.replace(',','.'))
                    if 0 <= monto_fijo <= subtotal_con_itbis_antes_descuento:
                        monto_descuento = monto_fijo
                    else: self.descuento_venta_var.set("0")
            except ValueError:
                if descuento_str : self.descuento_venta_var.set("0") 
                monto_descuento = 0.0

        self.descuento_aplicado_monto_var.set(round(monto_descuento, 2))
        total_neto_a_pagar = subtotal_con_itbis_antes_descuento - monto_descuento
        self.total_neto_venta_var.set(round(total_neto_a_pagar, 2))

        try:
            dinero_recibido_str = self.dinero_recibido_var.get().replace(',', '.')
            dinero_recibido = float(dinero_recibido_str or "0")
            if dinero_recibido > 0 and dinero_recibido >= total_neto_a_pagar:
                cambio = dinero_recibido - total_neto_a_pagar
                self.cambio_devuelto_var.set(f"RD$ {cambio:.2f}")
            elif dinero_recibido > 0 and dinero_recibido < total_neto_a_pagar:
                self.cambio_devuelto_var.set("Pago Insuficiente")
            else: self.cambio_devuelto_var.set("RD$ 0.00")
        except ValueError: 
            self.cambio_devuelto_var.set("Entrada Invalida") if self.dinero_recibido_var.get() else "RD$ 0.00"

    def _confirmar_venta_action(self):
        if not self.items_en_venta_actual:
            messagebox.showwarning("Venta Vacia", "Agregue productos a la venta antes de confirmar.", parent=self.display_frame)
            return
        self._actualizar_sumario_venta() 
        total_a_pagar = self.total_neto_venta_var.get()
        dinero_recibido_str = self.dinero_recibido_var.get()
        if not dinero_recibido_str:
            messagebox.showwarning("Pago Requerido", "Por favor, ingrese el dinero recibido.", parent=self.display_frame)
            if hasattr(self, 'dinero_recibido_entry'): self.dinero_recibido_entry.focus()
            return
        try: dinero_recibido_float = float(dinero_recibido_str.replace(',','.'))
        except ValueError:
            messagebox.showerror("Error en Pago", "El monto de dinero recibido debe ser un numero.", parent=self.display_frame)
            if hasattr(self, 'dinero_recibido_entry'): self.dinero_recibido_entry.focus()
            return
        if dinero_recibido_float < total_a_pagar:
            messagebox.showwarning("Monto Insuficiente", f"El dinero recibido (RD$ {dinero_recibido_float:.2f}) es menor que el total a pagar (RD$ {total_a_pagar:.2f}).", parent=self.display_frame)
            if hasattr(self, 'dinero_recibido_entry'): self.dinero_recibido_entry.focus()
            return
        cambio_calculado = dinero_recibido_float - total_a_pagar
        cliente_nombre_sel = self.cliente_venta_var.get()
        cliente_id_final = self.clientes_venta_map.get(cliente_nombre_sel) if cliente_nombre_sel != "Ninguno" else None
        descuento_monto = self.descuento_aplicado_monto_var.get()
        itbis_total_para_guardar = self.itbis_total_venta_var.get()
        
        subtotal_real_sin_itbis = 0.0
        for item in self.items_en_venta_actual:
            precio_unitario_final_item = item.get("precio_unitario", 0.0)
            itbis_item_total = item.get("itbis_item_total", 0.0)
            cantidad_item = item.get("cantidad", 1)
            if cantidad_item == 0: cantidad_item = 1 # Evitar división por cero si la cantidad es 0
            
            precio_unitario_sin_itbis_item = precio_unitario_final_item - (itbis_item_total / cantidad_item)
            subtotal_real_sin_itbis += precio_unitario_sin_itbis_item * cantidad_item

        confirm_msg = (f"Total a Pagar: RD$ {total_a_pagar:.2f}\nITBIS Incluido: RD$ {itbis_total_para_guardar:.2f}\nDinero Recibido: RD$ {dinero_recibido_float:.2f}\nCambio a Devolver: RD$ {cambio_calculado:.2f}\n\n¿Confirmar y guardar la venta?")
        confirm = messagebox.askyesno("Confirmar Venta Final", confirm_msg, parent=self.display_frame)
        if not confirm: return
        resultado = procesar_nueva_venta_gui( cliente_id_seleccionado=cliente_id_final, items_vendidos=self.items_en_venta_actual, total_bruto_sin_itbis=subtotal_real_sin_itbis, itbis_total_venta=itbis_total_para_guardar, descuento_aplicado=descuento_monto, total_neto=total_a_pagar, dinero_recibido=dinero_recibido_float, cambio_devuelto=cambio_calculado )
        if resultado["exito"]:
            messagebox.showinfo("Venta Exitosa", resultado["mensaje"], parent=self.display_frame)
            if 'venta_registrada' in resultado:
                venta_guardada = resultado['venta_registrada']
                nombre_cliente_factura = cliente_nombre_sel if cliente_nombre_sel != "Ninguno" else "Consumidor Final"
                texto_factura_generada = generar_texto_factura(venta_guardada, nombre_cliente_factura, datos_empresa=self._get_empresa_info())
                nombre_archivo_factura = ""
                try:
                    factura_dir = "Facturas"; os.makedirs(factura_dir, exist_ok=True)
                    id_venta_actual = venta_guardada.get('id', 'desconocida')
                    nombre_archivo_factura = os.path.join(factura_dir, f"factura_{id_venta_actual:05d}.txt")
                    with open(nombre_archivo_factura, "w", encoding="utf-8") as f_out: f_out.write(texto_factura_generada)
                    print(f"Factura guardada en: {nombre_archivo_factura}")
                except Exception as e_file: messagebox.showerror("Error al Guardar Factura", f"No se pudo guardar el archivo de factura:\n{e_file}", parent=self.display_frame)
                self._mostrar_factura_en_ventana(texto_factura_generada, venta_guardada.get('id', 0), nombre_archivo_factura)
            self._limpiar_estado_nueva_venta()
            self._cargar_datos_para_nueva_venta() 
            if hasattr(self, 'producto_venta_combo'): self.producto_venta_combo['values'] = self.lista_display_productos_venta_filtrada
            if hasattr(self, 'cliente_venta_combo'): self.cliente_venta_combo['values'] = self.lista_display_clientes_venta
            self.cliente_venta_var.set("Ninguno") 
            if hasattr(self, 'producto_venta_combo'): self.producto_venta_combo.focus()
        else: messagebox.showerror("Error en Venta", resultado["mensaje"], parent=self.display_frame)

    def _limpiar_estado_nueva_venta(self):
        self.cliente_venta_var.set("Ninguno")
        self.producto_venta_seleccionado_var.set("")
        self.cantidad_venta_var.set("1")
        self.descuento_venta_var.set("0")
        self.dinero_recibido_var.set("")
        self.items_en_venta_actual = []
        if hasattr(self, 'tree_items_venta'): self._actualizar_treeview_items_venta()
        self._actualizar_sumario_venta() 
        if hasattr(self, 'stock_disponible_venta_label'): self.stock_disponible_venta_label.config(text="Stock Disp: -")
        if hasattr(self, 'precio_unitario_venta_label'): self.precio_unitario_venta_label.config(text="Precio U: -")
        if hasattr(self, 'producto_venta_combo'):
            self.lista_display_productos_venta_filtrada = self.lista_display_productos_venta_original[:]
            self.producto_venta_combo['values'] = self.lista_display_productos_venta_filtrada

    def _limpiar_y_mostrar_welcome(self):
        self._limpiar_estado_nueva_venta()
        self.show_welcome_message_in_display()

    def nueva_venta_action(self):
        if not self._guard('nueva_venta'):
            return
        self._set_active_nav_action('nueva_venta')
        self._clear_display_frame()
        self._cargar_datos_para_nueva_venta()
        venta_main_frame = ttk.Frame(self.display_frame)
        venta_main_frame.pack(fill=tk.BOTH, expand=True)
        top_controls_frame = ttk.Frame(venta_main_frame)
        top_controls_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(top_controls_frame, text="Cliente:").pack(side=tk.LEFT, padx=(0, 2))
        self.cliente_venta_combo = ttk.Combobox(top_controls_frame, textvariable=self.cliente_venta_var, values=self.lista_display_clientes_venta, state="readonly", width=18)
        self.cliente_venta_combo.pack(side=tk.LEFT, padx=2)
        ttk.Label(top_controls_frame, text="Producto:").pack(side=tk.LEFT, padx=(5, 2))
        self.producto_venta_combo = ttk.Combobox(top_controls_frame, textvariable=self.producto_venta_seleccionado_var, values=self.lista_display_productos_venta_filtrada, width=35)
        self.producto_venta_combo.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        self.producto_venta_combo.bind("<<ComboboxSelected>>", self._actualizar_info_producto_seleccionado_venta)
        self.producto_venta_combo.bind("<KeyRelease>", self._on_producto_venta_keyup)
        self.producto_venta_combo.bind("<Return>", self._agregar_item_a_venta_actual_event)
        prod_info_qty_frame = ttk.Frame(venta_main_frame)
        prod_info_qty_frame.pack(fill=tk.X, pady=(0, 5))
        self.stock_disponible_venta_label = ttk.Label(prod_info_qty_frame, text="Stock Disp: -", width=18)
        self.stock_disponible_venta_label.pack(side=tk.LEFT, padx=2)
        self.precio_unitario_venta_label = ttk.Label(prod_info_qty_frame, text="Precio U: -", width=18)
        self.precio_unitario_venta_label.pack(side=tk.LEFT, padx=2)
        ttk.Label(prod_info_qty_frame, text="Cantidad:").pack(side=tk.LEFT, padx=(5, 2))
        self.cantidad_venta_entry = ttk.Entry(prod_info_qty_frame, textvariable=self.cantidad_venta_var, width=7)
        self.cantidad_venta_entry.pack(side=tk.LEFT, padx=2)
        self.cantidad_venta_entry.bind("<Return>", self._agregar_item_a_venta_actual_event)
        btn_agregar_item = ttk.Button(
            prod_info_qty_frame,
            text="Agregar a Venta",
            command=self._agregar_item_a_venta_actual,
            style="Secondary.TButton"
        )
        btn_agregar_item.pack(side=tk.LEFT, padx=5)
        items_venta_frame = ttk.LabelFrame(venta_main_frame, text="Items en Venta Actual", padding="5")
        items_venta_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        columnas_venta = ("id", "nombre", "cantidad", "precio_u", "subtotal")
        self.tree_items_venta = ttk.Treeview(items_venta_frame, columns=columnas_venta, show="headings", height=6)
        self.tree_items_venta.heading("id", text="ID"); self.tree_items_venta.column("id", width=40, anchor=tk.CENTER, stretch=tk.NO)
        self.tree_items_venta.heading("nombre", text="Producto"); self.tree_items_venta.column("nombre", width=200, stretch=tk.YES)
        self.tree_items_venta.heading("cantidad", text="Cant."); self.tree_items_venta.column("cantidad", width=60, anchor=tk.CENTER, stretch=tk.NO)
        self.tree_items_venta.heading("precio_u", text="Precio U. (Final)"); self.tree_items_venta.column("precio_u", width=110, anchor=tk.E, stretch=tk.NO)
        self.tree_items_venta.heading("subtotal", text="Subtotal (Final)"); self.tree_items_venta.column("subtotal", width=110, anchor=tk.E, stretch=tk.NO)
        scrollbar_items_venta = ttk.Scrollbar(items_venta_frame, orient=tk.VERTICAL, command=self.tree_items_venta.yview)
        self.tree_items_venta.configure(yscrollcommand=scrollbar_items_venta.set)
        scrollbar_items_venta.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_items_venta.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree_items_venta.bind("<Delete>", lambda e: (self._eliminar_item_de_venta_actual(), "break"))
        
        summary_payment_frame = ttk.LabelFrame(venta_main_frame, text="Resumen y Pago", padding="10")
        summary_payment_frame.pack(fill=tk.X, pady=5)
        
        row_idx = 0
        ttk.Label(summary_payment_frame, text="Subtotal (con ITBIS):").grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(summary_payment_frame, textvariable=self.subtotal_bruto_venta_var, font=("Arial", 10, "bold")).grid(row=row_idx, column=1, sticky="e", padx=5, pady=2)
        ttk.Label(summary_payment_frame, text="Descuento:").grid(row=row_idx, column=2, sticky="w", padx=5, pady=2)
        self.descuento_venta_entry = ttk.Entry(summary_payment_frame, textvariable=self.descuento_venta_var, width=10)
        self.descuento_venta_entry.grid(row=row_idx, column=3, sticky="ew", padx=5, pady=2)
        self.descuento_venta_entry.bind("<KeyRelease>", self._actualizar_sumario_venta)
        row_idx +=1

        ttk.Label(summary_payment_frame, text="Monto Desc:").grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(summary_payment_frame, textvariable=self.descuento_aplicado_monto_var, font=("Arial", 10, "bold")).grid(row=row_idx, column=1, sticky="e", padx=5, pady=2)
        ttk.Label(summary_payment_frame, text="ITBIS Total Venta:").grid(row=row_idx, column=2, sticky="w", padx=5, pady=2) 
        ttk.Label(summary_payment_frame, textvariable=self.itbis_total_venta_var, font=("Arial", 10, "bold")).grid(row=row_idx, column=3, sticky="e", padx=5, pady=2) 
        row_idx +=1
        
        ttk.Label(summary_payment_frame, text="TOTAL A PAGAR:", font=("Arial", 11, "bold")).grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=5, pady=3) 
        ttk.Label(summary_payment_frame, textvariable=self.total_neto_venta_var, font=("Arial", 11, "bold")).grid(row=row_idx, column=2, columnspan=2, sticky="e", padx=5, pady=3) 
        row_idx +=1
        
        ttk.Label(summary_payment_frame, text="Dinero Recibido:", font=("Arial", 10)).grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)
        self.dinero_recibido_entry = ttk.Entry(summary_payment_frame, textvariable=self.dinero_recibido_var, width=12)
        self.dinero_recibido_entry.grid(row=row_idx, column=1, sticky="e", padx=5, pady=2)
        self.dinero_recibido_entry.bind("<KeyRelease>", self._actualizar_sumario_venta)
        self.dinero_recibido_entry.bind("<Return>", self._confirmar_venta_action_event)
        ttk.Label(summary_payment_frame, text="Cambio:", font=("Arial", 10, "bold")).grid(row=row_idx, column=2, sticky="w", padx=5, pady=2)
        ttk.Label(summary_payment_frame, textvariable=self.cambio_devuelto_var, font=("Arial", 10, "bold")).grid(row=row_idx, column=3, sticky="e", padx=5, pady=2)
        
        summary_payment_frame.columnconfigure(0, weight=1)
        summary_payment_frame.columnconfigure(1, weight=1)
        summary_payment_frame.columnconfigure(2, weight=1)
        summary_payment_frame.columnconfigure(3, weight=1)

        venta_actions_frame = ttk.Frame(venta_main_frame)
        venta_actions_frame.pack(fill=tk.X, pady=10, side=tk.BOTTOM)
        btn_eliminar_item_bottom = ttk.Button(
            venta_actions_frame,
            text="Eliminar Item",
            command=self._eliminar_item_de_venta_actual,
            style="Exit.TButton"
        )
        btn_eliminar_item_bottom.pack(side=tk.LEFT, padx=5)
        btn_cancelar_venta = ttk.Button(
            venta_actions_frame,
            text="Cancelar Venta",
            command=self._limpiar_y_mostrar_welcome,
            style="Secondary.TButton"
        )
        btn_cancelar_venta.pack(side=tk.LEFT, padx=5)
        btn_confirmar_venta = ttk.Button(venta_actions_frame, text="Confirmar y Guardar Venta", command=self._confirmar_venta_action, style="Accent.TButton")
        btn_confirmar_venta.pack(side=tk.RIGHT, padx=10)
        
        self._limpiar_estado_nueva_venta() 
        self._actualizar_info_producto_seleccionado_venta()
        if hasattr(self, 'producto_venta_combo'): self.producto_venta_combo.focus()

    def historial_ventas_action(self):
        if not self._guard('historial_ventas'):
            return
        self._set_active_nav_action('historial_ventas')
        self._clear_display_frame()
        filtro_frame = ttk.Frame(self.display_frame)
        filtro_frame.pack(fill=tk.X, pady=5)
        ttk.Label(filtro_frame, text="Fecha Inicio (YYYY-MM-DD):").pack(side=tk.LEFT, padx=5)
        ttk.Entry(filtro_frame, textvariable=self.fecha_inicio_hist_var, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Label(filtro_frame, text="Fecha Fin (YYYY-MM-DD):").pack(side=tk.LEFT, padx=5)
        ttk.Entry(filtro_frame, textvariable=self.fecha_fin_hist_var, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            filtro_frame,
            text="Filtrar",
            command=lambda: self._poblar_historial_ventas_treeview(filtrar_por_fecha=True),
            style="Secondary.TButton"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            filtro_frame,
            text="Mostrar Todas",
            command=lambda: self._poblar_historial_ventas_treeview(filtrar_por_fecha=False),
            style="Secondary.TButton"
        ).pack(side=tk.LEFT, padx=5)
        hist_main_frame = ttk.Frame(self.display_frame)
        hist_main_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        columnas_hist = ("id_v", "fecha_v", "cliente_v", "subtotal_s_itbis_v", "itbis_v", "descuento_v", "total_v")
        self.tree_historial_ventas = ttk.Treeview(hist_main_frame, columns=columnas_hist, show="headings", height=10)
        self.tree_historial_ventas.heading("id_v", text="ID Venta"); self.tree_historial_ventas.column("id_v", width=60, anchor=tk.CENTER, stretch=tk.NO)
        self.tree_historial_ventas.heading("fecha_v", text="Fecha y Hora"); self.tree_historial_ventas.column("fecha_v", width=130, stretch=tk.NO)
        self.tree_historial_ventas.heading("cliente_v", text="Cliente"); self.tree_historial_ventas.column("cliente_v", width=150, stretch=tk.YES)
        self.tree_historial_ventas.heading("subtotal_s_itbis_v", text="Subtotal s/ITBIS"); self.tree_historial_ventas.column("subtotal_s_itbis_v", width=110, anchor=tk.E, stretch=tk.NO)
        self.tree_historial_ventas.heading("itbis_v", text="ITBIS"); self.tree_historial_ventas.column("itbis_v", width=80, anchor=tk.E, stretch=tk.NO)
        self.tree_historial_ventas.heading("descuento_v", text="Descuento"); self.tree_historial_ventas.column("descuento_v", width=80, anchor=tk.E, stretch=tk.NO)
        self.tree_historial_ventas.heading("total_v", text="Total Venta"); self.tree_historial_ventas.column("total_v", width=100, anchor=tk.E, stretch=tk.NO)
        scrollbar_hist_main = ttk.Scrollbar(hist_main_frame, orient=tk.VERTICAL, command=self.tree_historial_ventas.yview)
        self.tree_historial_ventas.configure(yscrollcommand=scrollbar_hist_main.set)
        scrollbar_hist_main.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_historial_ventas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree_historial_ventas.bind("<<TreeviewSelect>>", self._mostrar_detalle_venta_historial)
        self.label_detalle_venta_id_frame = ttk.LabelFrame(self.display_frame, text="Detalles de Venta ID: - (Seleccione una venta de arriba)", padding="10")
        self.label_detalle_venta_id_frame.pack(fill=tk.X, pady=10)
        columnas_detalle = ("prod_d", "cant_d", "pu_d", "sub_d")
        self.tree_detalle_historial_venta = ttk.Treeview(self.label_detalle_venta_id_frame, columns=columnas_detalle, show="headings", height=5)
        self.tree_detalle_historial_venta.heading("prod_d", text="Producto"); self.tree_detalle_historial_venta.column("prod_d", width=250)
        self.tree_detalle_historial_venta.heading("cant_d", text="Cantidad"); self.tree_detalle_historial_venta.column("cant_d", width=80, anchor=tk.CENTER)
        self.tree_detalle_historial_venta.heading("pu_d", text="Precio Unit. (Final)"); self.tree_detalle_historial_venta.column("pu_d", width=120, anchor=tk.E)
        self.tree_detalle_historial_venta.heading("sub_d", text="Subtotal (Final)"); self.tree_detalle_historial_venta.column("sub_d", width=120, anchor=tk.E)
        scrollbar_detalle = ttk.Scrollbar(self.label_detalle_venta_id_frame, orient=tk.VERTICAL, command=self.tree_detalle_historial_venta.yview)
        self.tree_detalle_historial_venta.configure(yscrollcommand=scrollbar_detalle.set)
        scrollbar_detalle.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_detalle_historial_venta.pack(fill=tk.BOTH, expand=True)
        self.label_total_periodo_hist = ttk.Label(self.display_frame, text="Total del Periodo: RD$ 0.00", font=("Arial", 12, "bold"))
        self.label_total_periodo_hist.pack(pady=5, anchor="e")
        self._poblar_historial_ventas_treeview(filtrar_por_fecha=False)
        # Botón para imprimir factura seleccionada (rol: cajero/admin)
        print_btn_frame = ttk.Frame(self.display_frame)
        print_btn_frame.pack(fill=tk.X, pady=(0,5))
        ttk.Button(print_btn_frame, text="Imprimir Factura Seleccionada", command=self._imprimir_factura_desde_historial, style="Accent.TButton").pack(side=tk.LEFT, padx=5)

    def _poblar_historial_ventas_treeview(self, filtrar_por_fecha=False):
        fecha_inicio, fecha_fin = None, None
        if filtrar_por_fecha:
            fecha_inicio = self.fecha_inicio_hist_var.get()
            fecha_fin = self.fecha_fin_hist_var.get()
            try:
                datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
                datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
                if fecha_inicio > fecha_fin:
                    messagebox.showerror("Error de Fechas", "La fecha de inicio no puede ser posterior a la fecha de fin.", parent=self.display_frame); return
            except ValueError: messagebox.showerror("Error de Fechas", "Formato de fecha incorrecto. Use YYYY-MM-DD.", parent=self.display_frame); return
        resultado_ventas = obtener_ventas_para_historial_gui(fecha_inicio, fecha_fin)
        self.ventas_cargadas_actualmente = resultado_ventas.get('ventas_mostradas', [])
        for widget_tree in [getattr(self, 'tree_historial_ventas', None), getattr(self, 'tree_detalle_historial_venta', None)]:
            if widget_tree:
                for i in widget_tree.get_children(): widget_tree.delete(i)
        if hasattr(self, 'label_detalle_venta_id_frame'): self.label_detalle_venta_id_frame.config(text="Detalles de Venta ID: - (Seleccione una venta)")
        if not self.ventas_cargadas_actualmente:
            if hasattr(self, 'tree_historial_ventas'): self.tree_historial_ventas.insert("", tk.END, values=("No hay ventas en este periodo.", "", "", "", "", "", ""))
            if hasattr(self, 'label_total_periodo_hist'): self.label_total_periodo_hist.config(text="Total del Periodo: RD$ 0.00")
            return
        if hasattr(self, 'tree_historial_ventas'):
            for venta in self.ventas_cargadas_actualmente:
                self.tree_historial_ventas.insert("", tk.END, iid=str(venta.get("id_venta")), values=(
                    venta.get("id_venta", "N/A"), venta.get("fecha", "N/A"), venta.get("nombre_cliente", "N/A"),
                    f"RD$ {venta.get('subtotal_bruto_sin_itbis', 0.0):.2f}", f"RD$ {venta.get('itbis_total_venta', 0.0):.2f}",
                    f"RD$ {venta.get('descuento_aplicado', 0.0):.2f}", f"RD$ {venta.get('total_final', 0.0):.2f}" ))
        if hasattr(self, 'label_total_periodo_hist'): self.label_total_periodo_hist.config(text=f"Total del Periodo: RD$ {resultado_ventas.get('total_periodo', 0.0):.2f}")
        self._apply_treeview_striping(getattr(self, 'tree_historial_ventas', None))
        self._apply_treeview_striping(getattr(self, 'tree_detalle_historial_venta', None))

    def _mostrar_detalle_venta_historial(self, event=None):
        if not hasattr(self, 'tree_detalle_historial_venta'): return
        for i in self.tree_detalle_historial_venta.get_children(): self.tree_detalle_historial_venta.delete(i)
        if hasattr(self, 'label_detalle_venta_id_frame'): self.label_detalle_venta_id_frame.config(text="Detalles de Venta ID: -")
        seleccion = self.tree_historial_ventas.selection()
        if not seleccion: return 
        item_id_tree = seleccion[0] 
        venta_seleccionada_completa = next((v for v in self.ventas_cargadas_actualmente if str(v.get("id_venta")) == str(item_id_tree)), None)
        if venta_seleccionada_completa:
            if hasattr(self, 'label_detalle_venta_id_frame'): self.label_detalle_venta_id_frame.config(text=f"Detalles de Venta ID: {venta_seleccionada_completa['id_venta']}")
            for prod in venta_seleccionada_completa.get("productos_detalle", []):
                self.tree_detalle_historial_venta.insert("", tk.END, values=(
                    prod.get("nombre", "N/A"), prod.get("cantidad", 0),
                    f"RD$ {prod.get('precio_unitario', 0.0):.2f}", f"RD$ {prod.get('subtotal', 0.0):.2f}" ))
            self._apply_treeview_striping(self.tree_detalle_historial_venta)
        else:
             if hasattr(self, 'label_detalle_venta_id_frame'): self.label_detalle_venta_id_frame.config(text="Detalle de Venta ID: - (Error al cargar)")
    
    def _cargar_clientes_para_historial_combo(self):
        clientes_data = obtener_lista_clientes_para_combobox()
        self.mapa_clientes_historial = {cliente["nombre"]: cliente["id"] for cliente in clientes_data}
        lista_nombres_clientes = sorted([nombre for nombre in self.mapa_clientes_historial.keys() if nombre])
        if hasattr(self, 'cliente_hist_combo'):
            self.cliente_hist_combo['values'] = lista_nombres_clientes
            if lista_nombres_clientes: self.cliente_hist_seleccionado_var.set(lista_nombres_clientes[0])
            else: self.cliente_hist_seleccionado_var.set("")

    def _limpiar_vista_historial_cliente(self):
        self.cliente_hist_info_nombre_var.set("")
        self.cliente_hist_info_telefono_var.set("")
        self.cliente_hist_info_direccion_var.set("")
        self.cliente_hist_total_gastado_var.set("Total Gastado: RD$0.00")
        if hasattr(self, 'tree_historial_compras_cliente'):
            for i in self.tree_historial_compras_cliente.get_children(): self.tree_historial_compras_cliente.delete(i)
        if hasattr(self, 'tree_detalle_venta_cliente'):
            for i in self.tree_detalle_venta_cliente.get_children(): self.tree_detalle_venta_cliente.delete(i)
        if hasattr(self, 'label_detalle_venta_cliente_frame'): self.label_detalle_venta_cliente_frame.config(text="Detalle de Venta ID: -")

    def _ver_historial_cliente_seleccionado(self):
        self._limpiar_vista_historial_cliente()
        nombre_cliente_seleccionado = self.cliente_hist_seleccionado_var.get()
        if not nombre_cliente_seleccionado:
            messagebox.showwarning("Sin Seleccion", "Por favor, seleccione un cliente.", parent=self.display_frame); return
        cliente_id = self.mapa_clientes_historial.get(nombre_cliente_seleccionado)
        if cliente_id is None:
            messagebox.showerror("Error", "No se pudo encontrar el ID del cliente seleccionado.", parent=self.display_frame); return
        
        # Asegurarse que obtener_historial_compras_cliente_gui está importada
        resultado = obtener_historial_compras_cliente_gui(cliente_id) 

        if resultado and resultado.get("exito"):
            cliente_info = resultado.get("cliente_info", {})
            self.cliente_hist_info_nombre_var.set(f"Nombre: {cliente_info.get('nombre', 'N/A')}")
            self.cliente_hist_info_telefono_var.set(f"Telefono: {cliente_info.get('telefono', 'N/A')}")
            self.cliente_hist_info_direccion_var.set(f"Direccion: {cliente_info.get('direccion', 'N/A')}")
            self.historial_compras_cliente_actual = resultado.get("historial_compras", [])
            if hasattr(self, 'tree_historial_compras_cliente'):
                for compra in self.historial_compras_cliente_actual:
                    self.tree_historial_compras_cliente.insert("", tk.END, iid=str(compra.get("id_venta")), values=(
                        compra.get("id_venta", "N/A"), compra.get("fecha", "N/A"), f"RD$ {compra.get('total_final', 0.0):.2f}" ))
                self._apply_treeview_striping(self.tree_historial_compras_cliente)
            self.cliente_hist_total_gastado_var.set(f"Total Gastado: RD$ {resultado.get('total_gastado', 0.0):.2f}")
        else:
            self.historial_compras_cliente_actual = []
            messagebox.showerror("Error", resultado.get("mensaje", "No se pudo obtener el historial del cliente."), parent=self.display_frame)
            self.cliente_hist_info_nombre_var.set("Nombre: N/A"); self.cliente_hist_info_telefono_var.set("Telefono: N/A")
            self.cliente_hist_info_direccion_var.set("Direccion: N/A"); self.cliente_hist_total_gastado_var.set("Total Gastado: RD$0.00")

    def historial_cliente_action(self):
        if not self._guard('historial_cliente'):
            return
        self._set_active_nav_action('historial_cliente')
        self._clear_display_frame()
        seleccion_frame = ttk.Frame(self.display_frame, padding="5")
        seleccion_frame.pack(fill=tk.X, pady=5)
        ttk.Label(seleccion_frame, text="Seleccionar Cliente:").pack(side=tk.LEFT, padx=(0, 5))
        self.cliente_hist_combo = ttk.Combobox(seleccion_frame, textvariable=self.cliente_hist_seleccionado_var, state="readonly", width=30)
        self.cliente_hist_combo.pack(side=tk.LEFT, padx=5)
        btn_ver_historial = ttk.Button(seleccion_frame, text="Ver Historial", command=self._ver_historial_cliente_seleccionado, style="Accent.TButton")
        btn_ver_historial.pack(side=tk.LEFT, padx=10)
        self._cargar_clientes_para_historial_combo()
        info_cliente_frame = ttk.LabelFrame(self.display_frame, text="Informacion del Cliente", padding="10")
        info_cliente_frame.pack(fill=tk.X, pady=5)
        ttk.Label(info_cliente_frame, textvariable=self.cliente_hist_info_nombre_var).pack(anchor="w")
        ttk.Label(info_cliente_frame, textvariable=self.cliente_hist_info_telefono_var).pack(anchor="w")
        ttk.Label(info_cliente_frame, textvariable=self.cliente_hist_info_direccion_var).pack(anchor="w")
        hist_compras_frame = ttk.LabelFrame(self.display_frame, text="Historial de Compras", padding="10")
        hist_compras_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        columnas_compras_cliente = ("id_venta_c", "fecha_c", "total_c")
        self.tree_historial_compras_cliente = ttk.Treeview(hist_compras_frame, columns=columnas_compras_cliente, show="headings", height=7)
        self.tree_historial_compras_cliente.heading("id_venta_c", text="ID Venta"); self.tree_historial_compras_cliente.column("id_venta_c", width=80, anchor=tk.CENTER, stretch=tk.NO)
        self.tree_historial_compras_cliente.heading("fecha_c", text="Fecha"); self.tree_historial_compras_cliente.column("fecha_c", width=150, stretch=tk.NO)
        self.tree_historial_compras_cliente.heading("total_c", text="Total Venta (RD$)"); self.tree_historial_compras_cliente.column("total_c", width=120, anchor=tk.E, stretch=tk.NO)
        scrollbar_compras_cliente = ttk.Scrollbar(hist_compras_frame, orient=tk.VERTICAL, command=self.tree_historial_compras_cliente.yview)
        self.tree_historial_compras_cliente.configure(yscrollcommand=scrollbar_compras_cliente.set)
        scrollbar_compras_cliente.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_historial_compras_cliente.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree_historial_compras_cliente.bind("<<TreeviewSelect>>", self._mostrar_detalle_venta_seleccionada_cliente)
        self.label_detalle_venta_cliente_frame = ttk.LabelFrame(self.display_frame, text="Detalle de Venta ID: -", padding="10")
        self.label_detalle_venta_cliente_frame.pack(fill=tk.X, pady=10)
        columnas_detalle_c = ("prod_vc", "cant_vc", "pu_vc", "sub_vc")
        self.tree_detalle_venta_cliente = ttk.Treeview(self.label_detalle_venta_cliente_frame, columns=columnas_detalle_c, show="headings", height=4)
        self.tree_detalle_venta_cliente.heading("prod_vc", text="Producto"); self.tree_detalle_venta_cliente.column("prod_vc", width=250, stretch=tk.YES)
        self.tree_detalle_venta_cliente.heading("cant_vc", text="Cantidad"); self.tree_detalle_venta_cliente.column("cant_vc", width=80, anchor=tk.CENTER, stretch=tk.NO)
        self.tree_detalle_venta_cliente.heading("pu_vc", text="Precio Unit. (Final)"); self.tree_detalle_venta_cliente.column("pu_vc", width=120, anchor=tk.E, stretch=tk.NO)
        self.tree_detalle_venta_cliente.heading("sub_vc", text="Subtotal (Final)"); self.tree_detalle_venta_cliente.column("sub_vc", width=120, anchor=tk.E, stretch=tk.NO)
        scrollbar_detalle_c = ttk.Scrollbar(self.label_detalle_venta_cliente_frame, orient=tk.VERTICAL, command=self.tree_detalle_venta_cliente.yview)
        self.tree_detalle_venta_cliente.configure(yscrollcommand=scrollbar_detalle_c.set)
        scrollbar_detalle_c.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_detalle_venta_cliente.pack(fill=tk.BOTH, expand=True)
        label_total_gastado = ttk.Label(self.display_frame, textvariable=self.cliente_hist_total_gastado_var, font=("Arial", 12, "bold"))
        label_total_gastado.pack(pady=5, anchor="e", padx=10)
        self._limpiar_vista_historial_cliente()

    def configuracion_action(self):
        if not self._guard('configuracion'):
            return
        self._set_active_nav_action('configuracion')
        self._clear_display_frame()
        wrapper = tk.Frame(self.display_frame, bg=self.colors.get("panel", "#ffffff"))
        wrapper.pack(fill=tk.BOTH, expand=True)
        self.config_wrapper = wrapper
        config_canvas = tk.Canvas(wrapper, bg=self.colors.get("panel", "#ffffff"), highlightthickness=0)
        config_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.config_canvas = config_canvas
        config_scroll = ttk.Scrollbar(wrapper, orient=tk.VERTICAL, command=config_canvas.yview)
        config_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        config_canvas.configure(yscrollcommand=config_scroll.set)

        cont = ttk.Frame(config_canvas, padding="15", style="Content.TFrame")
        self._config_canvas_window = config_canvas.create_window((0, 0), window=cont, anchor="nw")

        def _update_config_scroll(_event=None):
            config_canvas.configure(scrollregion=config_canvas.bbox("all"))
            config_canvas.itemconfig(self._config_canvas_window, width=config_canvas.winfo_width())
        cont.bind("<Configure>", _update_config_scroll)
        config_canvas.bind("<Configure>", _update_config_scroll)

        # Seccion de tema
        tema_frame = ttk.LabelFrame(cont, text="Preferencias de Tema", padding="12")
        tema_frame.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(tema_frame, text="Selecciona el tema de la aplicación:").grid(row=0, column=0, sticky="w")
        tema_labels = [self._theme_label_by_key.get(opt["key"], opt["key"].title()) for opt in self.available_theme_options]
        current_label = self._theme_label_by_key.get(self.current_theme_key, tema_labels[0])
        self.theme_selector_var = tk.StringVar(value=current_label)
        ttk.Combobox(
            tema_frame,
            values=tema_labels,
            textvariable=self.theme_selector_var,
            state="readonly",
            width=28
        ).grid(row=1, column=0, sticky="w", pady=5)
        ttk.Button(
            tema_frame,
            text="Aplicar Tema",
            style="Accent.TButton",
            command=self._aplicar_tema_desde_config
        ).grid(row=1, column=1, padx=10, sticky="e")
        tema_frame.columnconfigure(0, weight=1)
        tema_frame.columnconfigure(1, weight=0)

        # Seccion de datos del negocio solo para admin
        if self._role == 'admin':
            empresa_info = self._get_empresa_info()
            datos_frame = ttk.LabelFrame(cont, text="Datos del Negocio", padding="12")
            datos_frame.pack(fill=tk.BOTH, expand=True)

            self.empresa_nombre_var = tk.StringVar(value=empresa_info.get("nombre", ""))
            self.empresa_rnc_var = tk.StringVar(value=empresa_info.get("rnc", ""))
            self.empresa_direccion_var = tk.StringVar(value=empresa_info.get("direccion", ""))
            self.empresa_ciudad_var = tk.StringVar(value=empresa_info.get("ciudad", ""))
            self.empresa_telefono_var = tk.StringVar(value=empresa_info.get("telefono", ""))
            self.empresa_correo_var = tk.StringVar(value=empresa_info.get("correo", ""))
            self.empresa_tagline_var = tk.StringVar(value=empresa_info.get("tagline", ""))
            self.empresa_logo_var = tk.StringVar(value=empresa_info.get("logo_path", ""))

            campos = [
                ("Nombre Comercial:", self.empresa_nombre_var),
                ("RNC:", self.empresa_rnc_var),
                ("Dirección:", self.empresa_direccion_var),
                ("Ciudad / Provincia:", self.empresa_ciudad_var),
                ("Teléfono:", self.empresa_telefono_var),
                ("Correo electrónico:", self.empresa_correo_var),
                ("Descripción corta:", self.empresa_tagline_var),
            ]
            for idx, (label, var) in enumerate(campos):
                ttk.Label(datos_frame, text=label).grid(row=idx, column=0, sticky="w", padx=5, pady=5)
                ttk.Entry(datos_frame, textvariable=var, width=50).grid(row=idx, column=1, sticky="ew", padx=5, pady=5)
            datos_frame.columnconfigure(1, weight=1)

            ttk.Label(datos_frame, text="Logo (PNG):").grid(row=len(campos), column=0, sticky="w", padx=5, pady=5)
            ttk.Entry(datos_frame, textvariable=self.empresa_logo_var, width=50, state="readonly").grid(row=len(campos), column=1, sticky="ew", padx=5, pady=5)

            logo_buttons = ttk.Frame(datos_frame)
            logo_buttons.grid(row=len(campos)+1, column=0, columnspan=2, sticky="w", padx=5, pady=(0, 10))
            ttk.Button(logo_buttons, text="Seleccionar Logo", style="Secondary.TButton", command=self._seleccionar_logo_empresa).pack(side=tk.LEFT, padx=(0, 8))
            ttk.Button(logo_buttons, text="Limpiar", command=lambda: self.empresa_logo_var.set("")).pack(side=tk.LEFT)

            ttk.Button(
                datos_frame,
                text="Guardar Información",
                style="Accent.TButton",
                command=self._guardar_datos_empresa
            ).grid(row=len(campos)+2, column=0, columnspan=2, pady=(12, 0))
        else:
            ttk.Label(
                cont,
                text="Solo un administrador puede modificar la información del negocio.",
                style="Muted.TLabel"
            ).pack(fill=tk.X, pady=(10, 0))

    def _mostrar_detalle_venta_seleccionada_cliente(self, event=None):
        """Muestra detalle de la venta seleccionada en el historial del cliente."""
        if not hasattr(self, 'tree_historial_compras_cliente') or not hasattr(self, 'tree_detalle_venta_cliente'):
            return
        seleccion = self.tree_historial_compras_cliente.selection()
        if not seleccion:
            return
        try:
            item_id = seleccion[0]
            valores = self.tree_historial_compras_cliente.item(item_id).get('values', [])
            venta_id_sel = valores[0] if valores else None
            # Encabezado
            if hasattr(self, 'label_detalle_venta_cliente_frame') and venta_id_sel is not None:
                self.label_detalle_venta_cliente_frame.config(text=f"Detalle de Venta ID: {venta_id_sel}")
            # Limpiar detalle
            for i in self.tree_detalle_venta_cliente.get_children():
                self.tree_detalle_venta_cliente.delete(i)
            # Buscar venta en cache actual
            venta = None
            for registro in (self.historial_compras_cliente_actual or []):
                if str(registro.get('id_venta')) == str(venta_id_sel):
                    venta = registro
                    break
            if not venta:
                return
            for prod in venta.get('productos_detalle', []):
                self.tree_detalle_venta_cliente.insert(
                    "", tk.END,
                    values=(
                        prod.get('nombre', 'N/A'),
                        prod.get('cantidad', 0),
                        f"RD$ {float(prod.get('precio_unitario', 0.0)):.2f}",
                        f"RD$ {float(prod.get('subtotal', 0.0)):.2f}"
                    )
                )
            self._apply_treeview_striping(self.tree_detalle_venta_cliente)
        except Exception as e:
            print(f"Error mostrando detalle de venta del cliente: {e}")

    def _mostrar_factura_en_ventana(self, texto_factura, venta_id, nombre_archivo_factura_guardada=None):
        factura_window = tk.Toplevel(self.root)
        self._style_toplevel(factura_window)
        factura_window.title(f"Factura #: {venta_id:05d}")
        factura_window.geometry("480x650") 
        factura_window.transient(self.root)
        factura_window.grab_set(); factura_window.focus_set()
        text_frame = ttk.Frame(factura_window); text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Courier New", 9), padx=10, pady=10, relief=tk.SOLID, borderwidth=1)
        text_widget.insert(tk.END, texto_factura); text_widget.config(state=tk.DISABLED)
        self._style_scrolled_text(text_widget)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y); text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        button_frame = ttk.Frame(factura_window); button_frame.pack(fill=tk.X, pady=(5, 10))
        if nombre_archivo_factura_guardada:
            nombre_visible_archivo = os.path.basename(nombre_archivo_factura_guardada)
            if len(nombre_archivo_factura_guardada) > 50: nombre_visible_archivo = "..." + nombre_visible_archivo[-45:]
            saved_label = ttk.Label(button_frame, text=f"Guardada en: {nombre_visible_archivo}", font=("Arial", 8))
            saved_label.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)
        def guardar_copia_factura_dialogo():
            initial_dir = os.path.join(os.getcwd(), "Facturas"); os.makedirs(initial_dir, exist_ok=True)
            file_path = filedialog.asksaveasfilename(master=factura_window, initialdir=initial_dir, initialfile=f"copia_factura_{venta_id:05d}.txt", defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
            if file_path:
                try:
                    with open(file_path, "w", encoding="utf-8") as f: f.write(texto_factura)
                    messagebox.showinfo("Guardado", f"Factura guardada en:\n{file_path}", parent=factura_window)
                except Exception as e: messagebox.showerror("Error al Guardar", f"No se pudo guardar la factura:\n{e}", parent=factura_window)
        ttk.Button(button_frame, text="Guardar Copia Como...", command=guardar_copia_factura_dialogo).pack(side=tk.LEFT, padx=5)
        # Opción de imprimir directamente desde la vista de factura
        def imprimir_factura():
            try:
                self._print_text_to_system(texto_factura)
            except Exception as e:
                messagebox.showerror("Impresión", f"No fue posible imprimir la factura.\n{e}", parent=factura_window)
        ttk.Button(button_frame, text="Imprimir", command=imprimir_factura).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cerrar Vista", command=factura_window.destroy).pack(side=tk.RIGHT, padx=10)

    def _imprimir_factura_desde_historial(self):
        """Genera y muestra la factura de la venta seleccionada en el historial."""
        if not hasattr(self, 'tree_historial_ventas'):
            return
        sel = self.tree_historial_ventas.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Seleccione una venta para imprimir su factura.", parent=self.display_frame)
            return
        valores = self.tree_historial_ventas.item(sel[0]).get('values', [])
        if not valores:
            return
        try:
            venta_id = int(valores[0])
        except Exception:
            messagebox.showerror("Error", "No se pudo determinar el ID de la venta seleccionada.", parent=self.display_frame)
            return

        # Cargar venta completa desde la base de datos
        venta_obj = obtener_venta_para_factura(venta_id)
        # Determinar nombre del cliente
        nombre_cliente = "Consumidor Final"
        try:
            cid = venta_obj.get('cliente_id')
            if cid:
                # Consultar nombre del cliente vía Repo (consulta directa)
                from Modulos.DBUtil import fetch_one
                c = fetch_one("SELECT nombre FROM clientes WHERE id=%s", (cid,))
                if c and c.get('nombre'):
                    nombre_cliente = c['nombre']
        except Exception:
            pass

        texto_factura = generar_texto_factura(venta_obj, nombre_cliente, datos_empresa=self._get_empresa_info())
        self._mostrar_factura_en_ventana(texto_factura, venta_id)

    def _print_text_to_system(self, texto: str):
        """Intenta imprimir texto usando comandos del sistema.
        - En Linux/Mac usa lpr/lp si están disponibles.
        - En Windows intenta os.startfile(..., 'print').
        """
        # Crear un archivo temporal
        tmp_dir = tempfile.mkdtemp(prefix='pycolmado_')
        tmp_path = os.path.join(tmp_dir, 'factura.txt')
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(texto)

        system = platform.system().lower()
        try:
            if system == 'windows':
                try:
                    os.startfile(tmp_path, 'print')  # type: ignore[attr-defined]
                except Exception as e:
                    raise RuntimeError(f"No se pudo enviar a impresión en Windows: {e}")
            else:
                # Intentar lpr, si no lp
                cmd = None
                if shutil.which('lpr'):
                    cmd = ['lpr', tmp_path]
                elif shutil.which('lp'):
                    cmd = ['lp', tmp_path]
                if not cmd:
                    raise RuntimeError("No se encontró comando de impresión (lpr/lp)")
                subprocess.run(cmd, check=True)
        finally:
            # Limpiar el temporal
            try:
                os.remove(tmp_path)
                os.rmdir(tmp_dir)
            except Exception:
                pass

    # Nueva función para historial de proveedores
    def historial_proveedor_action(self):
        if not self._guard('historial_proveedor'):
            return
        self._set_active_nav_action('historial_proveedor')
        self._clear_display_frame()
        seleccion_frame = ttk.Frame(self.display_frame, padding="5")
        seleccion_frame.pack(fill=tk.X, pady=5)
        ttk.Label(seleccion_frame, text="Seleccionar Proveedor:").pack(side=tk.LEFT, padx=(0, 5))
        self.proveedor_hist_combo = ttk.Combobox(seleccion_frame, textvariable=self.proveedor_hist_seleccionado_var, state="readonly", width=30)
        self.proveedor_hist_combo.pack(side=tk.LEFT, padx=5)
        btn_ver_historial = ttk.Button(seleccion_frame, text="Ver Historial", command=self._ver_historial_proveedor_seleccionado, style="Accent.TButton")
        btn_ver_historial.pack(side=tk.LEFT, padx=10)
        if self._allowed('editar_proveedor'):
            ttk.Button(seleccion_frame, text="Editar Proveedor", command=self._abrir_editar_proveedor_dialog, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        # Aquí deberías cargar los proveedores, no los clientes
        self._cargar_proveedores_para_historial_combo()
        # Contenedor para resultados (se reutiliza y limpia entre búsquedas)
        self.proveedor_hist_result_container = ttk.Frame(self.display_frame)
        self.proveedor_hist_result_container.pack(fill=tk.BOTH, expand=True, pady=5)
        # El resto de la vista debe ser similar a la de clientes, pero usando variables y funciones de proveedores

    # Ejemplo de función para cargar proveedores en el combobox
    def _cargar_proveedores_para_historial_combo(self):
        proveedores_data = obtener_lista_proveedores_para_combobox()
        self.mapa_proveedores_historial = {prov["nombre"]: prov["id"] for prov in proveedores_data}
        lista_nombres_proveedores = sorted([nombre for nombre in self.mapa_proveedores_historial.keys() if nombre])
        if hasattr(self, 'proveedor_hist_combo'):
            self.proveedor_hist_combo['values'] = lista_nombres_proveedores
            if lista_nombres_proveedores:
                self.proveedor_hist_seleccionado_var.set(lista_nombres_proveedores[0])
            else:
                self.proveedor_hist_seleccionado_var.set("")

    # Ejemplo de función para ver historial de proveedor (debes implementarla según tu lógica de proveedores)
    def _ver_historial_proveedor_seleccionado(self):
        nombre_proveedor = self.proveedor_hist_seleccionado_var.get()
        if not nombre_proveedor:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un proveedor.", parent=self.display_frame)
            return
        proveedor_id = self.mapa_proveedores_historial.get(nombre_proveedor)
        if proveedor_id is None:
            messagebox.showerror("Error", "No se pudo encontrar el ID del proveedor seleccionado.", parent=self.display_frame)
            return

        resultado = obtener_historial_proveedor_gui(proveedor_id)
        if resultado.get("exito"):
            productos = resultado.get("productos", [])
            total_productos = resultado.get("total_productos", 0)
            total_stock = resultado.get("total_stock", 0)
            # Limpiar resultados anteriores y mostrar en el contenedor
            try:
                container = getattr(self, 'proveedor_hist_result_container')
            except Exception:
                container = None
            if container is None:
                container = ttk.Frame(self.display_frame)
                container.pack(fill=tk.BOTH, expand=True, pady=5)
                self.proveedor_hist_result_container = container
            else:
                for w in container.winfo_children():
                    try:
                        w.destroy()
                    except Exception:
                        pass

            info_frame = ttk.LabelFrame(container, text="Productos de este Proveedor", padding="10")
            info_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            columnas = ("id", "nombre", "stock", "precio_compra", "categoria")
            tree = ttk.Treeview(info_frame, columns=columnas, show="headings", height=8)
            tree.heading("id", text="ID")
            tree.heading("nombre", text="Nombre")
            tree.heading("stock", text="Stock")
            tree.heading("precio_compra", text="Precio Compra")
            tree.heading("categoria", text="Categoría")
            for prod in productos:
                tree.insert("", tk.END, values=(
                    prod.get("id", ""),
                    prod.get("nombre", ""),
                    prod.get("stock", 0),
                    f"RD$ {prod.get('precio_compra', 0.0):.2f}",
                    prod.get("categoria", "")
                ))
            tree.pack(fill=tk.BOTH, expand=True)
            self._apply_treeview_striping(tree)
            resumen = f"Total productos: {total_productos} | Stock total: {total_stock}"
            ttk.Label(container, text=resumen, font=("Arial", 11, "bold")).pack(pady=5, anchor="e")
        else:
            messagebox.showerror("Error", "No se pudo obtener el historial del proveedor.", parent=self.display_frame)

    def _abrir_editar_proveedor_dialog(self):
        if not self._allowed('editar_proveedor'):
            messagebox.showerror("Acceso denegado", "No tienes permisos para editar proveedores.", parent=self.display_frame); return
        nombre_proveedor = self.proveedor_hist_seleccionado_var.get()
        if not nombre_proveedor:
            messagebox.showwarning("Sin selección", "Seleccione un proveedor para editar.", parent=self.display_frame); return
        proveedor_id = self.mapa_proveedores_historial.get(nombre_proveedor)
        if proveedor_id is None:
            messagebox.showerror("Error", "No se pudo identificar el proveedor seleccionado.", parent=self.display_frame); return
        prov = obtener_proveedor_por_id(proveedor_id)
        if not prov:
            messagebox.showerror("Error", "Proveedor no encontrado.", parent=self.display_frame); return
        dlg = tk.Toplevel(self.root)
        self._style_toplevel(dlg)
        dlg.title(f"Editar Proveedor #{proveedor_id}")
        dlg.geometry("460x220")
        dlg.transient(self.root); dlg.grab_set()
        f = ttk.Frame(dlg, padding=10); f.pack(fill=tk.BOTH, expand=True)
        v_nombre = tk.StringVar(value=prov.get('nombre',''))
        v_tel = tk.StringVar(value=prov.get('telefono','') or '')
        v_dir = tk.StringVar(value=prov.get('direccion','') or '')
        ttk.Label(f, text="Nombre:").grid(row=0, column=0, sticky='w'); ttk.Entry(f, textvariable=v_nombre, width=35).grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        ttk.Label(f, text="Teléfono:").grid(row=1, column=0, sticky='w'); ttk.Entry(f, textvariable=v_tel, width=35).grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        ttk.Label(f, text="Dirección:").grid(row=2, column=0, sticky='w'); ttk.Entry(f, textvariable=v_dir, width=35).grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        btns = ttk.Frame(f); btns.grid(row=3, column=0, columnspan=2, pady=10)
        def guardar():
            res = actualizar_proveedor(proveedor_id, v_nombre.get(), v_tel.get(), v_dir.get())
            if res.get('exito'):
                messagebox.showinfo("Éxito", res.get('mensaje','Proveedor actualizado.'), parent=dlg)
                dlg.destroy(); self._cargar_proveedores_para_historial_combo(); self._ver_historial_proveedor_seleccionado()
            else:
                messagebox.showerror("Error", res.get('mensaje','No se pudo actualizar el proveedor.'), parent=dlg)
        ttk.Button(btns, text='Guardar', command=guardar, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text='Cerrar', command=dlg.destroy).pack(side=tk.LEFT, padx=5)
 
if __name__ == "__main__":
    # Root temporal solo para el login
    login_root = tk.Tk()
    login_root.withdraw()  # evitar parpadeo antes de crear el diálogo

    try:
        login_dialog = LoginDialog(login_root)
        try:
            login_root.update()
        except Exception:
            pass
        login_root.wait_window(login_dialog)

        if not login_dialog.result.get("exito"):
            login_root.destroy()
        else:
            user = login_dialog.result.get("usuario") or {}
            login_root.destroy()

            app_root = tk.Tk()
            app_root.state('zoomed')
            app_root.title(f"Sistema JB solution - Usuario: {user.get('username','')} ({user.get('rol','')})")
            app = ColmadoApp(app_root, current_user=user)
            app_root.mainloop()
    except Exception as e:
        print(f"Error durante el proceso de login: {e}")
        try:
            login_root.destroy()
        except Exception:
            pass


