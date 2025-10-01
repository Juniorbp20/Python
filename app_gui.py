import os 
import platform
import tempfile
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext 
import datetime
from Modulos.Repo import (
    # Productos
    obtener_productos_para_gui, guardar_nuevo_producto,
    obtener_categorias_existentes, obtener_productos_para_venta_gui,
    # Clientes
    obtener_lista_clientes_para_combobox, guardar_nuevo_cliente_desde_gui,
    obtener_historial_compras_cliente_gui,
    # Ventas
    procesar_nueva_venta_gui, obtener_ventas_para_historial_gui, generar_texto_factura, obtener_venta_para_factura,
    # Proveedores
    obtener_lista_proveedores_para_combobox, obtener_historial_proveedor_gui, guardar_nuevo_proveedor_desde_gui,
    actualizar_proveedor, obtener_proveedor_por_id,
    # Usuarios
    autenticar_usuario, crear_usuario, obtener_usuarios_para_gui, eliminar_usuario_por_id,
    # Productos extra
    obtener_producto_por_id, actualizar_producto,
)
 


class LoginDialog(tk.Toplevel):
    """Diálogo modal de login. Retorna en self.result un dict con 'exito' y 'usuario'."""
    def __init__(self, master):
        super().__init__(master)
        self.title("Iniciar Sesión")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()  # Modal
        self.result = {"exito": False, "usuario": None}

        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main, text="Usuario:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.user_var = tk.StringVar(value="Admin")
        ttk.Entry(main, textvariable=self.user_var, width=24).grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(main, text="Contraseña:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.pass_var = tk.StringVar(value="1234")
        entry_pass = ttk.Entry(main, textvariable=self.pass_var, width=24, show="*")
        entry_pass.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        btns = ttk.Frame(main)
        btns.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btns, text="Entrar", command=self._on_login, style="Accent.TButton").pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Cancelar", command=self._on_cancel, style="Exit.TButton").pack(side=tk.LEFT, padx=4)

        main.columnconfigure(1, weight=1)

        # Facilitar login con Enter
        entry_pass.bind("<Return>", lambda e: self._on_login())
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.after(100, lambda: entry_pass.focus_set())

        # Asegurar que el diálogo sea visible y centrado
        try:
            self.update_idletasks()
            self.wait_visibility()  # Forzar que sea visible antes de centrar
            w = self.winfo_width() or 320
            h = self.winfo_height() or 150
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = int((sw - w) / 2)
            y = int((sh - h) / 3)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

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

MARGEN_GANANCIA_POR_DEFECTO = 0.30 # 30% de margen sobre el precio de compra

class ColmadoApp:
    def __init__(self, root_window, current_user: dict | None = None):
        self.root = root_window
        self.root.title("Sistema de Colmado PyColmado")
        self.root.geometry("1000x750") 
        # Estilos y tema de ttk (define estilos usados: Accent.TButton, Exit.TButton)
        self._setup_styles()
        # Usuario actual (dict con keys: username, rol, ...)
        self.current_user = current_user or {"username": "(sin login)", "rol": "cajero"}
        # Normalizar rol y configurar permisos por rol
        self._role = str(self.current_user.get("rol", "cajero")).lower()
        self._role_permissions = {
            'admin': {
                'listar_productos','agregar_producto','nueva_venta','historial_ventas',
                'registrar_proveedor','historial_proveedor','historial_cliente','gestionar_usuarios',
                'registrar_cliente',
                'editar_producto','editar_proveedor'
            },
            'cajero': {'listar_productos','nueva_venta','historial_ventas','registrar_cliente'},
            'almacen': {'agregar_producto','registrar_proveedor','historial_proveedor','editar_proveedor'}
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

        content_frame = ttk.Frame(self.root, padding="10")
        content_frame.pack(expand=True, fill=tk.BOTH)
        actions_frame = ttk.LabelFrame(content_frame, text="Acciones Principales", padding="10")
        actions_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        self.display_frame = ttk.Frame(content_frame, padding="10")
        self.display_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10, pady=10)
        self._clear_display_frame()
        self.show_welcome_message_in_display()
        
        btn_listar_productos = ttk.Button(actions_frame, text="Listar Productos", command=self.listar_productos_action)
        if self._allowed('listar_productos'): btn_listar_productos.pack(fill=tk.X, pady=5)
        btn_agregar_producto = ttk.Button(actions_frame, text="Agregar Producto", command=self.agregar_producto_action)
        if self._allowed('agregar_producto'): btn_agregar_producto.pack(fill=tk.X, pady=5)
        btn_nueva_venta = ttk.Button(actions_frame, text="Nueva Venta", command=self.nueva_venta_action)
        if self._allowed('nueva_venta'): btn_nueva_venta.pack(fill=tk.X, pady=5)
        btn_historial_ventas = ttk.Button(actions_frame, text="Historial de Ventas", command=self.historial_ventas_action)
        if self._allowed('historial_ventas'): btn_historial_ventas.pack(fill=tk.X, pady=5)
        btn_registrar_proveedor = ttk.Button(actions_frame, text="Registrar Proveedor", command=self.registrar_proveedor_action)
        if self._allowed('registrar_proveedor'): btn_registrar_proveedor.pack(fill=tk.X, pady=5)
        # Nuevo: registrar clientes (admin/cajero)
        btn_registrar_cliente = ttk.Button(actions_frame, text="Registrar Cliente", command=self.registrar_cliente_action)
        if self._allowed('registrar_cliente'): btn_registrar_cliente.pack(fill=tk.X, pady=5)
        btn_historial_cliente = ttk.Button(actions_frame, text="Historial de Proveedor", command=self.historial_proveedor_action)
        if self._allowed('historial_proveedor'): btn_historial_cliente.pack(fill=tk.X, pady=5)
        btn_historial_cliente_real = ttk.Button(actions_frame, text="Historial de Cliente", command=self.historial_cliente_action)
        if self._allowed('historial_cliente'): btn_historial_cliente_real.pack(fill=tk.X, pady=5)
        # Botón de gestión de usuarios (solo visible para admin)
        if self._allowed('gestionar_usuarios'):
            btn_users = ttk.Button(actions_frame, text="Gestionar Usuarios", command=self.gestionar_usuarios_action)
            btn_users.pack(fill=tk.X, pady=5)

        btn_salir = ttk.Button(actions_frame, text="Salir", command=self.root.quit, style="Exit.TButton")
        btn_salir.pack(fill=tk.X, pady=20)

    def _clear_display_frame(self):
        for widget in self.display_frame.winfo_children():
            widget.destroy()

    def show_welcome_message_in_display(self):
        self._clear_display_frame()
        welcome_text = f"Bienvenido {self.current_user.get('username','')} ({self.current_user.get('rol','')}).\nSeleccione una accion del menu de la izquierda."
        welcome_label = ttk.Label(self.display_frame, text=welcome_text,
                                  font=("Arial", 12))
        welcome_label.pack(padx=10, pady=10, anchor="center", expand=True)

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


    def _setup_styles(self):
        """Configura el tema ttk y estilos usados por la app.
        Define 'Accent.TButton' y 'Exit.TButton' si no existen.
        """
        try:
            style = ttk.Style(self.root)
            # Intentar usar un tema consistente en Linux/Windows
            try:
                style.theme_use('clam')
            except Exception:
                pass  # Mantener tema por defecto si falla
            # Botón de acción principal (azul)
            style.configure('Accent.TButton', foreground='white')
            style.map('Accent.TButton', background=[('!disabled', '#0078D4'), ('active', '#106EBE')])
            # Botón de salida/destructivo (rojo)
            style.configure('Exit.TButton', foreground='white')
            style.map('Exit.TButton', background=[('!disabled', '#D83B01'), ('active', '#A52600')])
            # Suavizar encabezados de Treeview
            style.configure('Treeview.Heading', font=("Arial", 10, 'bold'))
        except Exception as e:
            print(f"Advertencia: No se pudieron configurar estilos ttk: {e}")

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
                arrow = ' ▲' if not reverse else ' ▼'
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

    def listar_productos_action(self): 
        if not self._guard('listar_productos'):
            return
        self._clear_display_frame()
        productos = obtener_productos_para_gui() 
        if not productos:
            no_data_label = ttk.Label(self.display_frame, text="No hay productos para mostrar.", font=("Arial", 12))
            no_data_label.pack(padx=10, pady=10, anchor="center", expand=True)
            return
        
        columnas = ("id", "nombre", "precio_final", "stock", "categoria", "proveedor") 
        tree = ttk.Treeview(self.display_frame, columns=columnas, show="headings", height=15)
        tree.heading("id", text="ID");
        tree.column("id", minwidth=0, width=50, stretch=tk.NO, anchor=tk.CENTER)
        tree.heading("nombre", text="Nombre");
        tree.column("nombre", minwidth=0, width=200, stretch=tk.YES)
        tree.heading("precio_final", text="Precio Venta Final (RD$)"); 
        tree.column("precio_final", minwidth=0, width=140, stretch=tk.NO, anchor=tk.E)
        tree.heading("stock", text="Stock");
        tree.column("stock", minwidth=0, width=70, stretch=tk.NO, anchor=tk.CENTER)
        tree.heading("categoria", text="Categoria");
        tree.column("categoria", minwidth=0, width=120, stretch=tk.YES)
        tree.heading("proveedor", text="Proveedor");
        tree.column("proveedor", minwidth=0, width=150, stretch=tk.YES)
        
        for producto in productos:
            tree.insert("", tk.END, values=(
            producto.get("id"), 
            producto.get("nombre"), 
            f"{producto.get('precio'):.2f}", # 'precio' en obtener_productos_para_gui es precio_final_venta
            producto.get("stock"), 
            producto.get("categoria"),
            producto.get("proveedor")
            ))
        scrollbar = ttk.Scrollbar(self.display_frame, orient=tk.VERTICAL, command=tree.yview)
        # Corregido: usar yscrollcommand en lugar de 'yscroll'
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
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
        ttk.Button(buttons_frame, text="Guardar Producto", command=self._submit_nuevo_producto).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Limpiar Formulario", command=self._clear_agregar_producto_form).pack(side=tk.LEFT, padx=5)
        
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
        else: messagebox.showerror("Error al Guardar", resultado["mensaje"], parent=self.display_frame)

    def registrar_cliente_action(self):
        if not self._guard('registrar_cliente'):
            return
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
        ttk.Button(buttons_frame, text="Limpiar Formulario", command=self._clear_registrar_cliente_form).pack(side=tk.LEFT, padx=10)
        form_frame.columnconfigure(1, weight=1)
        self._clear_registrar_cliente_form()


    def registrar_proveedor_action(self):
        if not self._guard('registrar_proveedor'):
            return
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
        ttk.Button(buttons_frame, text="Guardar Proveedor", command=self._submit_nuevo_proveedor).pack(side=tk.LEFT, padx=10)
        # Limpiar solo campos de proveedor
        ttk.Button(buttons_frame, text="Limpiar Formulario", command=self._clear_registrar_proveedor_form).pack(side=tk.LEFT, padx=10)
        form_frame.columnconfigure(1, weight=1)
        self._clear_registrar_proveedor_form()

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
        self.producto_venta_combo.set(current_text_in_box)
        if self.lista_display_productos_venta_filtrada and self.root.focus_get() == self.producto_venta_combo:
            if len(current_text_in_box) > 0:
                pass

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
                texto_factura_generada = generar_texto_factura(venta_guardada, nombre_cliente_factura) 
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
        prod_info_qty_frame = ttk.Frame(venta_main_frame)
        prod_info_qty_frame.pack(fill=tk.X, pady=(0, 5))
        self.stock_disponible_venta_label = ttk.Label(prod_info_qty_frame, text="Stock Disp: -", width=18)
        self.stock_disponible_venta_label.pack(side=tk.LEFT, padx=2)
        self.precio_unitario_venta_label = ttk.Label(prod_info_qty_frame, text="Precio U: -", width=18)
        self.precio_unitario_venta_label.pack(side=tk.LEFT, padx=2)
        ttk.Label(prod_info_qty_frame, text="Cantidad:").pack(side=tk.LEFT, padx=(5, 2))
        self.cantidad_venta_entry = ttk.Entry(prod_info_qty_frame, textvariable=self.cantidad_venta_var, width=7)
        self.cantidad_venta_entry.pack(side=tk.LEFT, padx=2)
        btn_agregar_item = ttk.Button(prod_info_qty_frame, text="Agregar a Venta", command=self._agregar_item_a_venta_actual)
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
        ttk.Label(summary_payment_frame, text="Cambio:", font=("Arial", 10, "bold")).grid(row=row_idx, column=2, sticky="w", padx=5, pady=2)
        ttk.Label(summary_payment_frame, textvariable=self.cambio_devuelto_var, font=("Arial", 10, "bold")).grid(row=row_idx, column=3, sticky="e", padx=5, pady=2)
        
        summary_payment_frame.columnconfigure(0, weight=1)
        summary_payment_frame.columnconfigure(1, weight=1)
        summary_payment_frame.columnconfigure(2, weight=1)
        summary_payment_frame.columnconfigure(3, weight=1)

        venta_actions_frame = ttk.Frame(venta_main_frame)
        venta_actions_frame.pack(fill=tk.X, pady=10, side=tk.BOTTOM)
        btn_eliminar_item_bottom = ttk.Button(venta_actions_frame, text="Eliminar Item", command=self._eliminar_item_de_venta_actual)
        btn_eliminar_item_bottom.pack(side=tk.LEFT, padx=5)
        btn_cancelar_venta = ttk.Button(venta_actions_frame, text="Cancelar Venta", command=self._limpiar_y_mostrar_welcome)
        btn_cancelar_venta.pack(side=tk.LEFT, padx=5)
        btn_confirmar_venta = ttk.Button(venta_actions_frame, text="Confirmar y Guardar Venta", command=self._confirmar_venta_action, style="Accent.TButton")
        btn_confirmar_venta.pack(side=tk.RIGHT, padx=10)
        
        self._limpiar_estado_nueva_venta() 
        self._actualizar_info_producto_seleccionado_venta()
        if hasattr(self, 'producto_venta_combo'): self.producto_venta_combo.focus()

    def historial_ventas_action(self):
        if not self._guard('historial_ventas'):
            return
        self._clear_display_frame()
        filtro_frame = ttk.Frame(self.display_frame)
        filtro_frame.pack(fill=tk.X, pady=5)
        ttk.Label(filtro_frame, text="Fecha Inicio (YYYY-MM-DD):").pack(side=tk.LEFT, padx=5)
        ttk.Entry(filtro_frame, textvariable=self.fecha_inicio_hist_var, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Label(filtro_frame, text="Fecha Fin (YYYY-MM-DD):").pack(side=tk.LEFT, padx=5)
        ttk.Entry(filtro_frame, textvariable=self.fecha_fin_hist_var, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(filtro_frame, text="Filtrar", command=lambda: self._poblar_historial_ventas_treeview(filtrar_por_fecha=True)).pack(side=tk.LEFT, padx=5)
        ttk.Button(filtro_frame, text="Mostrar Todas", command=lambda: self._poblar_historial_ventas_treeview(filtrar_por_fecha=False)).pack(side=tk.LEFT, padx=5)
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
            self.cliente_hist_total_gastado_var.set(f"Total Gastado: RD$ {resultado.get('total_gastado', 0.0):.2f}")
        else:
            self.historial_compras_cliente_actual = []
            messagebox.showerror("Error", resultado.get("mensaje", "No se pudo obtener el historial del cliente."), parent=self.display_frame)
            self.cliente_hist_info_nombre_var.set("Nombre: N/A"); self.cliente_hist_info_telefono_var.set("Telefono: N/A")
            self.cliente_hist_info_direccion_var.set("Direccion: N/A"); self.cliente_hist_total_gastado_var.set("Total Gastado: RD$0.00")

    def historial_cliente_action(self):
        if not self._guard('historial_cliente'):
            return
        self._clear_display_frame()
        seleccion_frame = ttk.Frame(self.display_frame, padding="5")
        seleccion_frame.pack(fill=tk.X, pady=5)
        ttk.Label(seleccion_frame, text="Seleccionar Cliente:").pack(side=tk.LEFT, padx=(0, 5))
        self.cliente_hist_combo = ttk.Combobox(seleccion_frame, textvariable=self.cliente_hist_seleccionado_var, state="readonly", width=30)
        self.cliente_hist_combo.pack(side=tk.LEFT, padx=5)
        btn_ver_historial = ttk.Button(seleccion_frame, text="Ver Historial", command=self._ver_historial_cliente_seleccionado)
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
        except Exception as e:
            print(f"Error mostrando detalle de venta del cliente: {e}")

    def _mostrar_factura_en_ventana(self, texto_factura, venta_id, nombre_archivo_factura_guardada=None):
        factura_window = tk.Toplevel(self.root)
        factura_window.title(f"Factura #: {venta_id:05d}")
        factura_window.geometry("480x650") 
        factura_window.transient(self.root)
        factura_window.grab_set(); factura_window.focus_set()
        text_frame = ttk.Frame(factura_window); text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Courier New", 9), padx=10, pady=10, relief=tk.SOLID, borderwidth=1)
        text_widget.insert(tk.END, texto_factura); text_widget.config(state=tk.DISABLED)
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

        texto_factura = generar_texto_factura(venta_obj, nombre_cliente)
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
        self._clear_display_frame()
        seleccion_frame = ttk.Frame(self.display_frame, padding="5")
        seleccion_frame.pack(fill=tk.X, pady=5)
        ttk.Label(seleccion_frame, text="Seleccionar Proveedor:").pack(side=tk.LEFT, padx=(0, 5))
        self.proveedor_hist_combo = ttk.Combobox(seleccion_frame, textvariable=self.proveedor_hist_seleccionado_var, state="readonly", width=30)
        self.proveedor_hist_combo.pack(side=tk.LEFT, padx=5)
        btn_ver_historial = ttk.Button(seleccion_frame, text="Ver Historial", command=self._ver_historial_proveedor_seleccionado)
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
    # Asegurar que los archivos JSON existan antes de iniciar la GUI
    try:
        from Modulos.Datos import inicializar_archivos
        inicializar_archivos()
    except Exception as e:
        # No impedir el arranque de la GUI, pero avisar en consola si algo falla
        print(f"Advertencia: No se pudieron inicializar los archivos de datos. {e}")

    # Mostrar login antes de cargar la app principal
    root = tk.Tk()
    try:
        # No ocultar completamente la raíz para evitar "pantalla en blanco"
        login = LoginDialog(root)
        # Asegurar procesamiento de eventos para mostrar el diálogo
        try:
            root.update()
        except Exception:
            pass
        root.wait_window(login)
        if not login.result.get("exito"):
            root.destroy()
        else:
            user = login.result.get("usuario") or {}
            root.title(f"Sistema de Colmado PyColmado - Usuario: {user.get('username','')} ({user.get('rol','')})")
            app = ColmadoApp(root, current_user=user)
            root.mainloop()
    except Exception as e:
        print(f"Error durante el proceso de login: {e}")
        try:
            root.destroy()
        except Exception:
            pass
