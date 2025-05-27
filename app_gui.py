import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
from Modulos.Productos import (obtener_productos_para_gui, guardar_nuevo_producto, obtener_categorias_existentes, obtener_productos_para_venta_gui)# Para la venta
from Modulos.Clientes import obtener_lista_clientes_para_combobox
from Modulos.Ventas import procesar_nueva_venta_gui, obtener_ventas_para_historial_gui, generar_texto_factura


class ColmadoApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Nombre")
        self.root.geometry("1000x750")  # Ajustado para más espacio en la venta

        # --- Variables para el formulario de agregar producto ---
        self.nombre_prod_var = tk.StringVar()
        self.precio_prod_var = tk.StringVar()
        self.stock_prod_var = tk.StringVar()
        self.categoria_prod_var = tk.StringVar()
        self.proveedor_nombre_var = tk.StringVar()  # Para Combobox en Agregar Producto
        self.proveedores_map = {}  # Para mapear nombre a ID en Agregar Producto
        self.lista_display_proveedores = ["Ninguno"]  # Para Combobox en Agregar Producto
        self.lista_categorias = []  # Para Combobox en Agregar Producto

        # --- Variables para la sección de Nueva Venta ---
        self.cliente_venta_var = tk.StringVar()
        self.producto_venta_seleccionado_var = tk.StringVar()
        self.cantidad_venta_var = tk.StringVar(value="1")
        self.descuento_venta_var = tk.StringVar(value="0")
        self.dinero_recibido_var = tk.StringVar()
        self.cambio_devuelto_var = tk.StringVar()

        self.clientes_venta_map = {}  # {"Nombre Cliente": id} para la venta
        self.lista_display_clientes_venta = ["Ninguno"]

        self.productos_para_venta_datos = []  # Lista de dicts {id, nombre, precio, stock}
        self.lista_display_productos_venta_original = []  # Lista de strings formateados para el combobox (original)
        self.lista_display_productos_venta_filtrada = []  # Lista de strings formateados para el combobox (filtrada)

        self.items_en_venta_actual = []  # Lista de dicts: {id, nombre, cantidad, precio_unitario, subtotal}

        self.subtotal_bruto_venta_var = tk.DoubleVar(value=0.0)
        self.total_neto_venta_var = tk.DoubleVar(value=0.0)
        self.descuento_aplicado_monto_var = tk.DoubleVar(value=0.0)
        self.fecha_inicio_hist_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        self.fecha_fin_hist_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        self.ventas_cargadas_actualmente = []  # Para almacenar las ventas cargadas actualmente

        # --- Frames Principales de la UI ---
        content_frame = ttk.Frame(self.root, padding="10")
        content_frame.pack(expand=True, fill=tk.BOTH)

        actions_frame = ttk.LabelFrame(content_frame, text="Acciones Principales", padding="10")
        actions_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.display_frame = ttk.Frame(content_frame, padding="10")
        self.display_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10, pady=10)

        self._clear_display_frame()
        self.show_welcome_message_in_display()

        # --- Botones del Menú de Acciones ---
        btn_listar_productos = ttk.Button(actions_frame, text="Listar Productos", command=self.listar_productos_action)
        btn_listar_productos.pack(fill=tk.X, pady=5)
        btn_agregar_producto = ttk.Button(actions_frame, text="Agregar Producto", command=self.agregar_producto_action)
        btn_agregar_producto.pack(fill=tk.X, pady=5)
        btn_nueva_venta = ttk.Button(actions_frame, text="Nueva Venta", command=self.nueva_venta_action)
        btn_nueva_venta.pack(fill=tk.X, pady=5)
        btn_historial_ventas = ttk.Button(actions_frame, text="Historial de Ventas", command=self.historial_ventas_action)
        btn_historial_ventas.pack(fill=tk.X, pady=5)
        btn_registrar_cliente = ttk.Button(actions_frame, text="Registrar Cliente", command=self.registrar_cliente_action)
        btn_registrar_cliente.pack(fill=tk.X, pady=5)
        btn_historial_cliente = ttk.Button(actions_frame, text="Historial de Cliente", command=self.historial_cliente_action)
        btn_historial_cliente.pack(fill=tk.X, pady=5)
        btn_salir = ttk.Button(actions_frame, text="Salir", command=self.root.quit, style="Exit.TButton")
        btn_salir.pack(fill=tk.X, pady=20)

    def _clear_display_frame(self):
        for widget in self.display_frame.winfo_children():
            widget.destroy()

    def show_welcome_message_in_display(self):
        self._clear_display_frame()
        welcome_label = ttk.Label(self.display_frame, text="Seleccione una acción del menú de la izquierda.",
                                  font=("Arial", 12))
        welcome_label.pack(padx=10, pady=10, anchor="center", expand=True)

    def listar_productos_action(self):
        self._clear_display_frame()
        productos = obtener_productos_para_gui()
        if not productos:
            no_data_label = ttk.Label(self.display_frame, text="No hay productos para mostrar.", font=("Arial", 12))
            no_data_label.pack(padx=10, pady=10, anchor="center", expand=True)
            return
        columnas = ("id", "nombre", "precio", "stock", "categoria", "proveedor")
        tree = ttk.Treeview(self.display_frame, columns=columnas, show="headings", height=15)
        tree.heading("id", text="ID");
        tree.column("id", minwidth=0, width=50, stretch=tk.NO, anchor=tk.CENTER)
        tree.heading("nombre", text="Nombre");
        tree.column("nombre", minwidth=0, width=200, stretch=tk.YES)
        tree.heading("precio", text="Precio ($)");
        tree.column("precio", minwidth=0, width=80, stretch=tk.NO, anchor=tk.E)
        tree.heading("stock", text="Stock");
        tree.column("stock", minwidth=0, width=70, stretch=tk.NO, anchor=tk.CENTER)
        tree.heading("categoria", text="Categoría");
        tree.column("categoria", minwidth=0, width=120, stretch=tk.YES)
        tree.heading("proveedor", text="Proveedor");
        tree.column("proveedor", minwidth=0, width=150, stretch=tk.YES)
        for producto in productos:
            tree.insert("", tk.END, values=(
            producto["id"], producto["nombre"], producto["precio"], producto["stock"], producto["categoria"],
            producto["proveedor"]))
        scrollbar = ttk.Scrollbar(self.display_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _cargar_datos_combobox_agregar_prod(self):
        self.lista_categorias = obtener_categorias_existentes()
        proveedores_data = obtener_lista_clientes_para_combobox()
        self.proveedores_map = {prov["nombre"]: prov["id"] for prov in proveedores_data}
        self.lista_display_proveedores = ["Ninguno"] + sorted(list(self.proveedores_map.keys()))

    def _clear_agregar_producto_form(self):
        self.nombre_prod_var.set("")
        self.precio_prod_var.set("")
        self.stock_prod_var.set("")
        self.categoria_prod_var.set("")
        self.proveedor_nombre_var.set("Ninguno")

    def agregar_producto_action(self):
        self._clear_display_frame()
        self._cargar_datos_combobox_agregar_prod()
        form_frame = ttk.LabelFrame(self.display_frame, text="Agregar Nuevo Producto", padding="15")
        form_frame.pack(padx=10, pady=10, fill=tk.X)
        ttk.Label(form_frame, text="Nombre:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        nombre_entry = ttk.Entry(form_frame, textvariable=self.nombre_prod_var, width=40)
        nombre_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(form_frame, text="Precio:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(form_frame, textvariable=self.precio_prod_var, width=40).grid(row=1, column=1, padx=5, pady=5,
                                                                                sticky="ew")
        ttk.Label(form_frame, text="Stock:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(form_frame, textvariable=self.stock_prod_var, width=40).grid(row=2, column=1, padx=5, pady=5,
                                                                               sticky="ew")
        ttk.Label(form_frame, text="Categoría:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        ttk.Combobox(form_frame, textvariable=self.categoria_prod_var, values=self.lista_categorias, width=38).grid(
            row=3, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(form_frame, text="Proveedor:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        proveedor_combo = ttk.Combobox(form_frame, textvariable=self.proveedor_nombre_var,
                                       values=self.lista_display_proveedores, width=38, state="readonly")
        proveedor_combo.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(buttons_frame, text="Guardar Producto", command=self._submit_nuevo_producto).pack(side=tk.LEFT,
                                                                                                     padx=5)
        ttk.Button(buttons_frame, text="Limpiar Formulario", command=self._clear_agregar_producto_form).pack(
            side=tk.LEFT, padx=5)
        form_frame.columnconfigure(1, weight=1)
        self._clear_agregar_producto_form()
        nombre_entry.focus()

    def _submit_nuevo_producto(self):
        nombre = self.nombre_prod_var.get()
        precio_str = self.precio_prod_var.get()
        stock_str = self.stock_prod_var.get()
        categoria = self.categoria_prod_var.get()
        proveedor_nombre_seleccionado = self.proveedor_nombre_var.get()
        if not nombre.strip(): messagebox.showerror("Error de Validación",
                                                    "El nombre del producto no puede estar vacío."); return
        proveedor_id_para_guardar = ""
        if proveedor_nombre_seleccionado != "Ninguno" and proveedor_nombre_seleccionado in self.proveedores_map:
            proveedor_id_para_guardar = str(self.proveedores_map[proveedor_nombre_seleccionado])
        resultado = guardar_nuevo_producto(nombre, precio_str, stock_str, categoria, proveedor_id_para_guardar)
        if resultado["exito"]:
            messagebox.showinfo("Éxito", resultado["mensaje"]); self._clear_agregar_producto_form()
        else:
            messagebox.showerror("Error al Guardar", resultado["mensaje"])

    # --- MÉTODOS PARA NUEVA VENTA ---
    def _cargar_datos_para_nueva_venta(self):
        """Carga clientes y productos para la venta, preparando las listas de datos."""
        # Clientes
        clientes_data = obtener_lista_clientes_para_combobox()
        self.clientes_venta_map = {cliente["nombre"]: cliente["id"] for cliente in clientes_data}
        self.lista_display_clientes_venta = ["Ninguno"] + sorted(list(self.clientes_venta_map.keys()))

        # Productos
        self.productos_para_venta_datos = obtener_productos_para_venta_gui()
        self.lista_display_productos_venta_original = []
        for p in self.productos_para_venta_datos:
            display_text = f"{p['id']} - {p['nombre']} (Precio: ${p['precio']:.2f} - Stock: {p['stock']})"
            self.lista_display_productos_venta_original.append(display_text)
        self.lista_display_productos_venta_filtrada = self.lista_display_productos_venta_original[:]

    def _on_producto_venta_keyup(self, event=None):
        """Filtra la lista del combobox de productos mientras el usuario escribe."""
        texto_busqueda = self.producto_venta_seleccionado_var.get().lower()

        if not texto_busqueda:
            self.lista_display_productos_venta_filtrada = self.lista_display_productos_venta_original[:]
        else:
            self.lista_display_productos_venta_filtrada = [
                item_display for item_display in self.lista_display_productos_venta_original
                if texto_busqueda in item_display.lower()
            ]

        # Guardar el texto actual antes de cambiar 'values' y reestablecerlo
        # Esto ayuda a que el texto que el usuario está escribiendo no se borre al actualizar la lista.
        current_text_in_box = self.producto_venta_combo.get()
        self.producto_venta_combo['values'] = self.lista_display_productos_venta_filtrada
        self.producto_venta_combo.set(current_text_in_box)  # Reestablecer el texto

        # Si hay resultados y el combobox tiene el foco, intentar abrir el desplegable
        # No siempre funciona perfectamente en todos los S.O. o con todos los eventos
        if self.lista_display_productos_venta_filtrada and self.root.focus_get() == self.producto_venta_combo:
            if len(current_text_in_box) > 0:  # Solo si hay algo de texto
                # Forzar que el desplegable se muestre (puede ser un poco agresivo)
                # self.producto_venta_combo.event_generate('<Button-1>') # Simula un clic
                # o simplemente confiar en que el usuario lo abrirá si es necesario
                pass

    def _actualizar_info_producto_seleccionado_venta(self, event=None):
        seleccion_actual_str = self.producto_venta_seleccionado_var.get()
        if not seleccion_actual_str or not self.productos_para_venta_datos:
            if hasattr(self, 'stock_disponible_venta_label'): self.stock_disponible_venta_label.config(
                text="Stock Disp: -")
            if hasattr(self, 'precio_unitario_venta_label'): self.precio_unitario_venta_label.config(text="Precio U: -")
            return

        try:
            producto_id_seleccionado = int(seleccion_actual_str.split(" - ")[0])
            producto_info = next((p for p in self.productos_para_venta_datos if p["id"] == producto_id_seleccionado),
                                 None)

            if producto_info:
                stock_ya_en_cesta = 0
                item_en_cesta = next(
                    (item for item in self.items_en_venta_actual if item["id"] == producto_id_seleccionado), None)
                if item_en_cesta: stock_ya_en_cesta = item_en_cesta["cantidad"]
                stock_visual_disponible = producto_info['stock'] - stock_ya_en_cesta
                self.stock_disponible_venta_label.config(text=f"Stock Disp: {stock_visual_disponible}")
                self.precio_unitario_venta_label.config(text=f"Precio U: ${producto_info['precio']:.2f}")
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
            messagebox.showwarning("Producto no seleccionado", "Por favor, seleccione un producto de la lista.",
                                   parent=self.display_frame)
            return

        try:
            cantidad_a_agregar = int(cantidad_str)
            if cantidad_a_agregar <= 0:
                messagebox.showwarning("Cantidad Inválida", "La cantidad debe ser mayor a cero.",
                                       parent=self.display_frame)
                return
        except ValueError:
            messagebox.showwarning("Cantidad Inválida", "La cantidad debe ser un número entero.",
                                   parent=self.display_frame)
            return

        try:
            producto_id = int(producto_seleccionado_str.split(" - ")[0])
            producto_info_original = next((p for p in self.productos_para_venta_datos if p["id"] == producto_id), None)

            if not producto_info_original:
                messagebox.showerror("Error de Producto",
                                     "El producto seleccionado no es válido. Por favor, elija de la lista desplegable.",
                                     parent=self.display_frame)
                return

            item_existente_en_cesta = next((item for item in self.items_en_venta_actual if item["id"] == producto_id),
                                           None)
            cantidad_ya_en_cesta = item_existente_en_cesta["cantidad"] if item_existente_en_cesta else 0

            if (cantidad_ya_en_cesta + cantidad_a_agregar) > producto_info_original["stock"]:
                messagebox.showwarning("Stock Insuficiente",
                                       f"No hay suficiente stock para '{producto_info_original['nombre']}'.\n"
                                       f"Stock original: {producto_info_original['stock']}\n"
                                       f"Ya en cesta: {cantidad_ya_en_cesta}\n"
                                       f"Intenta agregar: {cantidad_a_agregar}\n"
                                       f"Máximo adicional posible: {producto_info_original['stock'] - cantidad_ya_en_cesta}",
                                       parent=self.display_frame)
                return

            if item_existente_en_cesta:
                item_existente_en_cesta["cantidad"] += cantidad_a_agregar
                item_existente_en_cesta["subtotal"] = item_existente_en_cesta["cantidad"] * item_existente_en_cesta[
                    "precio_unitario"]
            else:
                self.items_en_venta_actual.append({
                    "id": producto_info_original["id"], "nombre": producto_info_original["nombre"],
                    "cantidad": cantidad_a_agregar, "precio_unitario": producto_info_original["precio"],
                    "subtotal": cantidad_a_agregar * producto_info_original["precio"]
                })

            self._actualizar_treeview_items_venta()
            self._actualizar_sumario_venta()
            self._actualizar_info_producto_seleccionado_venta()  # Actualizar stock visual
            self.cantidad_venta_var.set("1")
            # self.producto_venta_seleccionado_var.set("") # Opcional: limpiar selección de producto
            # self.producto_venta_combo.focus() # Mantener el foco para agregar más rápido
        except (ValueError, IndexError):
            messagebox.showerror("Error de Selección", "Producto no válido. Asegúrese de seleccionar de la lista.",
                                 parent=self.display_frame)
        except Exception as e:
            messagebox.showerror("Error al agregar", f"Ocurrió un error: {e}", parent=self.display_frame)

    def _actualizar_treeview_items_venta(self):
        if hasattr(self, 'tree_items_venta'):
            for i in self.tree_items_venta.get_children(): self.tree_items_venta.delete(i)
            for item in self.items_en_venta_actual:
                self.tree_items_venta.insert("", tk.END, values=(
                    item["id"], item["nombre"], item["cantidad"],
                    f"${item['precio_unitario']:.2f}", f"${item['subtotal']:.2f}"))

    def _eliminar_item_de_venta_actual(self):
        if not hasattr(self, 'tree_items_venta'): return
        seleccion = self.tree_items_venta.selection()
        if not seleccion: messagebox.showwarning("Nada seleccionado",
                                                 "Seleccione un producto de la lista para eliminar.",
                                                 parent=self.display_frame); return

        # Obtener el ID del producto del Treeview (asumiendo que el ID es el primer valor)
        item_seleccionado_id_tree = self.tree_items_venta.item(seleccion[0])["values"][0]

        self.items_en_venta_actual = [item for item in self.items_en_venta_actual if
                                      item["id"] != item_seleccionado_id_tree]
        self._actualizar_treeview_items_venta()
        self._actualizar_sumario_venta()
        self._actualizar_info_producto_seleccionado_venta()

    def _actualizar_sumario_venta(self, event=None):
        subtotal_bruto = sum(item["subtotal"] for item in self.items_en_venta_actual)
        self.subtotal_bruto_venta_var.set(round(subtotal_bruto, 2))
        descuento_str = self.descuento_venta_var.get().strip()
        monto_descuento = 0.0
        if descuento_str:
            try:
                if "%" in descuento_str:
                    porcentaje = float(descuento_str.replace("%", ""))
                    if 0 <= porcentaje <= 100:
                        monto_descuento = subtotal_bruto * (porcentaje / 100)
                    else:
                        messagebox.showwarning("Descuento Inválido", "Porcentaje debe estar entre 0 y 100.",
                                               parent=self.display_frame); self.descuento_venta_var.set("0")
                else:
                    monto_fijo = float(descuento_str)
                    if 0 <= monto_fijo <= subtotal_bruto:
                        monto_descuento = monto_fijo
                    else:
                        messagebox.showwarning("Descuento Inválido",
                                               "Monto de descuento no puede ser negativo ni mayor al subtotal.",
                                               parent=self.display_frame); self.descuento_venta_var.set("0")
            except ValueError:
                if descuento_str: messagebox.showwarning("Descuento Inválido",
                                                         "Formato de descuento no válido (ej: 50 o 10%).",
                                                         parent=self.display_frame); self.descuento_venta_var.set("0")
                monto_descuento = 0.0
        self.descuento_aplicado_monto_var.set(round(monto_descuento, 2))
        total_neto = subtotal_bruto - monto_descuento
        self.total_neto_venta_var.set(round(total_neto, 2))

        try:
            dinero_recibido = float(self.dinero_recibido_var.get() or "0")
            if dinero_recibido > 0 and dinero_recibido >= total_neto:
                cambio = dinero_recibido - total_neto
                self.cambio_devuelto_var.set(f"${cambio:.2f}")
            elif dinero_recibido > 0 and dinero_recibido < total_neto:
                self.cambio_devuelto_var.set("Insuficiente")
            else:
                self.cambio_devuelto_var.set("$0.00")
        except ValueError:
            self.cambio_devuelto_var.set("Error") if self.dinero_recibido_var.get() else "$0.00"

    def _confirmar_venta_action(self):
        if not self.items_en_venta_actual:
            messagebox.showwarning("Venta Vacía", "Agregue productos a la venta antes de confirmar.",
                                   parent=self.display_frame)
            return

        self._actualizar_sumario_venta()
        total_a_pagar = self.total_neto_venta_var.get()
        dinero_recibido_str = self.dinero_recibido_var.get()

        if not dinero_recibido_str:
            messagebox.showwarning("Pago Requerido", "Por favor, ingrese el dinero recibido.",
                                   parent=self.display_frame)
            if hasattr(self, 'dinero_recibido_entry'): self.dinero_recibido_entry.focus()
            return
        try:
            dinero_recibido_float = float(dinero_recibido_str)
        except ValueError:
            messagebox.showerror("Error en Pago", "El monto de dinero recibido debe ser un número.",
                                 parent=self.display_frame)
            if hasattr(self, 'dinero_recibido_entry'): self.dinero_recibido_entry.focus()
            return

        if dinero_recibido_float < total_a_pagar:
            messagebox.showwarning("Monto Insuficiente",
                                   f"El dinero recibido (${dinero_recibido_float:.2f}) es menor que el total a pagar (${total_a_pagar:.2f}).",
                                   parent=self.display_frame)
            if hasattr(self, 'dinero_recibido_entry'): self.dinero_recibido_entry.focus()
            return

        cambio_calculado = dinero_recibido_float - total_a_pagar
        self.cambio_devuelto_var.set(f"${cambio_calculado:.2f}")

        cliente_nombre_sel = self.cliente_venta_var.get()
        cliente_id_final = self.clientes_venta_map.get(cliente_nombre_sel) if cliente_nombre_sel != "Ninguno" else None

        subtotal_bruto = self.subtotal_bruto_venta_var.get()
        descuento_monto = self.descuento_aplicado_monto_var.get()

        confirm_msg = (f"Total a Pagar: ${total_a_pagar:.2f}\n"
                       f"Dinero Recibido: ${dinero_recibido_float:.2f}\n"
                       f"Cambio a Devolver: ${cambio_calculado:.2f}\n\n"
                       "¿Confirmar y guardar la venta?")

        # Aquí es donde el usuario presiona "Sí" o "No"
        confirm = messagebox.askyesno("Confirmar Venta Final", confirm_msg, parent=self.display_frame)
        if not confirm:  # Si el usuario presiona "No"
            return

        # Si el usuario presiona "Sí", procedemos:
        resultado = procesar_nueva_venta_gui(
            cliente_id_final, self.items_en_venta_actual,
            subtotal_bruto, descuento_monto, total_a_pagar,
            dinero_recibido_float, cambio_calculado
        )

        if resultado["exito"]:  # Si procesar_nueva_venta_gui fue exitoso
            messagebox.showinfo("Venta Exitosa", resultado["mensaje"], parent=self.display_frame)

            # --- INICIO: Generar y mostrar/guardar factura ---
            if 'venta_registrada' in resultado:  # Asegúrate que procesar_nueva_venta_gui devuelva esto
                venta_guardada = resultado['venta_registrada']
                nombre_cliente_factura = cliente_nombre_sel  # Ya tenemos el nombre del cliente seleccionado

                texto_factura_generada = generar_texto_factura(venta_guardada, nombre_cliente_factura)

                # Guardar factura en archivo automáticamente
                nombre_archivo_factura = ""
                try:
                    factura_dir = "Facturas"
                    if not os.path.exists(factura_dir):
                        os.makedirs(factura_dir)

                    id_venta_actual = venta_guardada.get('id', 'desconocida')
                    nombre_archivo_factura = os.path.join(factura_dir, f"factura_{id_venta_actual:05d}.txt")

                    with open(nombre_archivo_factura, "w", encoding="utf-8") as f_out:
                        f_out.write(texto_factura_generada)
                    print(f"Factura guardada en: {nombre_archivo_factura}")
                except Exception as e_file:
                    messagebox.showerror("Error al Guardar Factura",
                                         f"No se pudo guardar el archivo de factura:\n{e_file}",
                                         parent=self.display_frame)
                    nombre_archivo_factura = ""  # No se guardó

                # Mostrar factura en nueva ventana
                self._mostrar_factura_en_ventana(texto_factura_generada, venta_guardada.get('id', 0),
                                                 nombre_archivo_factura)
            # --- FIN: Generar y mostrar/guardar factura ---

            # Limpiar y recargar para la siguiente venta
            self._limpiar_estado_nueva_venta()
            self._cargar_datos_para_nueva_venta()
            if hasattr(self, 'producto_venta_combo'):
                self.producto_venta_combo['values'] = self.lista_display_productos_venta_filtrada
            if hasattr(self, 'cliente_venta_combo'):
                self.cliente_venta_combo['values'] = self.lista_display_clientes_venta
            self.cliente_venta_var.set("Ninguno")
        else:  # Si procesar_nueva_venta_gui falló
            messagebox.showerror("Error en Venta", resultado["mensaje"], parent=self.display_frame)

    def _limpiar_estado_nueva_venta(self):
        self.cliente_venta_var.set("Ninguno")
        self.producto_venta_seleccionado_var.set("")
        self.cantidad_venta_var.set("1")
        self.descuento_venta_var.set("0")
        self.dinero_recibido_var.set("")
        self.cambio_devuelto_var.set("")
        self.items_en_venta_actual = []

        if hasattr(self, 'tree_items_venta'): self._actualizar_treeview_items_venta()
        self._actualizar_sumario_venta()  # Esto pondrá los totales y cambio a 0.00 o ""

        if hasattr(self, 'stock_disponible_venta_label'): self.stock_disponible_venta_label.config(text="Stock Disp: -")
        if hasattr(self, 'precio_unitario_venta_label'): self.precio_unitario_venta_label.config(text="Precio U: -")

        if hasattr(self, 'producto_venta_combo') and hasattr(self, 'lista_display_productos_venta_original'):
            self.lista_display_productos_venta_filtrada = self.lista_display_productos_venta_original[:]
            self.producto_venta_combo['values'] = self.lista_display_productos_venta_filtrada

    def _limpiar_y_mostrar_welcome(self):
        self._limpiar_estado_nueva_venta()
        self.show_welcome_message_in_display()

    def nueva_venta_action(self):
        self._clear_display_frame()

        # --- Frame General para la Venta ---
        venta_main_frame = ttk.Frame(self.display_frame)
        venta_main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Frame Superior: Cliente y Selección de Producto ---
        top_controls_frame = ttk.Frame(venta_main_frame)
        top_controls_frame.pack(fill=tk.X, pady=(0, 5))  # pady top 0
        ttk.Label(top_controls_frame, text="Cliente:").pack(side=tk.LEFT, padx=(0, 2))
        self.cliente_venta_combo = ttk.Combobox(top_controls_frame, textvariable=self.cliente_venta_var,
                                                state="readonly", width=18)
        self.cliente_venta_combo.pack(side=tk.LEFT, padx=2)
        ttk.Label(top_controls_frame, text="Producto:").pack(side=tk.LEFT, padx=(5, 2))
        self.producto_venta_combo = ttk.Combobox(top_controls_frame, textvariable=self.producto_venta_seleccionado_var,
                                                 width=35)
        self.producto_venta_combo.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        self.producto_venta_combo.bind("<<ComboboxSelected>>", self._actualizar_info_producto_seleccionado_venta)
        self.producto_venta_combo.bind("<KeyRelease>", self._on_producto_venta_keyup)

        # --- Frame Info Producto y Cantidad ---
        prod_info_qty_frame = ttk.Frame(venta_main_frame)
        prod_info_qty_frame.pack(fill=tk.X, pady=(0, 5))
        self.stock_disponible_venta_label = ttk.Label(prod_info_qty_frame, text="Stock Disp: -", width=15)
        self.stock_disponible_venta_label.pack(side=tk.LEFT, padx=2)
        self.precio_unitario_venta_label = ttk.Label(prod_info_qty_frame, text="Precio U: -", width=15)
        self.precio_unitario_venta_label.pack(side=tk.LEFT, padx=2)
        ttk.Label(prod_info_qty_frame, text="Cantidad:").pack(side=tk.LEFT, padx=(5, 2))
        self.cantidad_venta_entry = ttk.Entry(prod_info_qty_frame, textvariable=self.cantidad_venta_var, width=5)
        self.cantidad_venta_entry.pack(side=tk.LEFT, padx=2)
        btn_agregar_item = ttk.Button(prod_info_qty_frame, text="Agregar a Venta",
                                      command=self._agregar_item_a_venta_actual)
        btn_agregar_item.pack(side=tk.LEFT, padx=5)

        # --- Frame para TreeView de Items en Venta ---
        items_venta_frame = ttk.LabelFrame(venta_main_frame, text="Items en Venta Actual", padding="5")
        items_venta_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        columnas_venta = ("id", "nombre", "cantidad", "precio_u", "subtotal")
        self.tree_items_venta = ttk.Treeview(items_venta_frame, columns=columnas_venta, show="headings", height=6)
        self.tree_items_venta.heading("id", text="ID");
        self.tree_items_venta.column("id", width=40, anchor=tk.CENTER, stretch=tk.NO)
        self.tree_items_venta.heading("nombre", text="Producto");
        self.tree_items_venta.column("nombre", width=200, stretch=tk.YES)
        self.tree_items_venta.heading("cantidad", text="Cant.");
        self.tree_items_venta.column("cantidad", width=50, anchor=tk.CENTER, stretch=tk.NO)
        self.tree_items_venta.heading("precio_u", text="Precio U.");
        self.tree_items_venta.column("precio_u", width=80, anchor=tk.E, stretch=tk.NO)
        self.tree_items_venta.heading("subtotal", text="Subtotal");
        self.tree_items_venta.column("subtotal", width=90, anchor=tk.E, stretch=tk.NO)
        scrollbar_items_venta = ttk.Scrollbar(items_venta_frame, orient=tk.VERTICAL,
                                              command=self.tree_items_venta.yview)
        self.tree_items_venta.configure(yscrollcommand=scrollbar_items_venta.set)
        scrollbar_items_venta.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_items_venta.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- Frame Sumario y Pago ---
        summary_payment_frame = ttk.LabelFrame(venta_main_frame, text="Resumen y Pago", padding="10")
        summary_payment_frame.pack(fill=tk.X, pady=5)
        ttk.Label(summary_payment_frame, text="Subtotal Bruto:").grid(row=0, column=0, sticky="w", padx=5, pady=1)
        ttk.Label(summary_payment_frame, textvariable=self.subtotal_bruto_venta_var, font=("Arial", 10, "bold")).grid(row=0, column=1, sticky="e", padx=5, pady=1)
        ttk.Label(summary_payment_frame, text="Descuento:").grid(row=0, column=2, sticky="w", padx=5, pady=1)
        self.descuento_venta_entry = ttk.Entry(summary_payment_frame, textvariable=self.descuento_venta_var, width=10)
        self.descuento_venta_entry.grid(row=0, column=3, sticky="ew", padx=5, pady=1)
        self.descuento_venta_entry.bind("<FocusOut>", self._actualizar_sumario_venta);
        self.descuento_venta_entry.bind("<Return>", self._actualizar_sumario_venta)
        ttk.Label(summary_payment_frame, text="Monto Desc:").grid(row=1, column=0, sticky="w", padx=5, pady=1)
        ttk.Label(summary_payment_frame, textvariable=self.descuento_aplicado_monto_var,
                  font=("Arial", 10, "bold")).grid(row=1, column=1, sticky="e", padx=5, pady=1)
        ttk.Label(summary_payment_frame, text="TOTAL A PAGAR:", font=("Arial", 11, "bold")).grid(row=2, column=0, sticky="w", padx=5, pady=3)
        ttk.Label(summary_payment_frame, textvariable=self.total_neto_venta_var, font=("Arial", 11, "bold")).grid(row=2, column=1, sticky="e", padx=5, pady=3)
        ttk.Label(summary_payment_frame, text="Dinero Recibido:", font=("Arial", 10)).grid(row=3, column=0, sticky="w",
                                                                                           padx=5, pady=1)
        self.dinero_recibido_entry = ttk.Entry(summary_payment_frame, textvariable=self.dinero_recibido_var, width=12)
        self.dinero_recibido_entry.grid(row=3, column=1, sticky="e", padx=5, pady=1)
        self.dinero_recibido_entry.bind("<FocusOut>", self._actualizar_sumario_venta);
        self.dinero_recibido_entry.bind("<Return>", self._actualizar_sumario_venta)
        ttk.Label(summary_payment_frame, text="Cambio:", font=("Arial", 10, "bold")).grid(row=3, column=2, sticky="w",
                                                                                          padx=5, pady=1)
        ttk.Label(summary_payment_frame, textvariable=self.cambio_devuelto_var, font=("Arial", 10, "bold")).grid(row=3, column=3, sticky="e", padx=5, pady=1)
        for i in range(4): summary_payment_frame.columnconfigure(i, weight=1 if i % 2 == 1 else 0)

        # --- Botones de Acción de Venta (al final) ---
        venta_actions_frame = ttk.Frame(venta_main_frame)
        venta_actions_frame.pack(fill=tk.X, pady=10, side=tk.BOTTOM)
        btn_eliminar_item_bottom = ttk.Button(venta_actions_frame, text="Eliminar Item",
                                              command=self._eliminar_item_de_venta_actual)
        btn_eliminar_item_bottom.pack(side=tk.LEFT, padx=5)
        btn_cancelar_venta = ttk.Button(venta_actions_frame, text="Cancelar Venta",
                                        command=self._limpiar_y_mostrar_welcome)
        btn_cancelar_venta.pack(side=tk.LEFT, padx=5)
        btn_confirmar_venta = ttk.Button(venta_actions_frame, text="Confirmar y Guardar Venta",
                                         command=self._confirmar_venta_action, style="Accent.TButton")
        btn_confirmar_venta.pack(side=tk.RIGHT, padx=10)

        # Cargar datos y configurar valores iniciales DESPUÉS de crear todos los widgets
        self._cargar_datos_para_nueva_venta()
        self.cliente_venta_combo['values'] = self.lista_display_clientes_venta
        self.producto_venta_combo['values'] = self.lista_display_productos_venta_filtrada

        self._limpiar_estado_nueva_venta()  # Establece defaults en StringVars y actualiza sumario
        self._actualizar_info_producto_seleccionado_venta()  # Actualiza labels de stock/precio iniciales
        self.producto_venta_combo.focus()

    # --- Resto de métodos de acción para otros botones ---
    # --- MÉTODOS PARA HISTORIAL DE VENTAS ---
    def _mostrar_detalle_venta_historial(self, event=None):
        if not hasattr(self, 'tree_detalle_historial_venta'): return  # Si el widget no existe

        # Limpiar detalle anterior
        for i in self.tree_detalle_historial_venta.get_children():
            self.tree_detalle_historial_venta.delete(i)

        # Usar el texto del LabelFrame para mostrar el ID, o un label dedicado si prefieres
        if hasattr(self,
                   'label_detalle_venta_id_frame'):  # Asumiendo que 'label_detalle_venta_id_frame' es el LabelFrame
            self.label_detalle_venta_id_frame.config(text="Detalles de Venta ID: -")

        seleccion = self.tree_historial_ventas.selection()
        if not seleccion: return

        item_id_tree = seleccion[0]  # El IID que asignamos al insertar (debe ser el ID de la venta)

        venta_seleccionada_completa = next(
            (v for v in self.ventas_cargadas_actualmente if str(v["id_venta"]) == str(item_id_tree)), None)

        if venta_seleccionada_completa:
            if hasattr(self, 'label_detalle_venta_id_frame'):
                self.label_detalle_venta_id_frame.config(
                    text=f"Detalles de Venta ID: {venta_seleccionada_completa['id_venta']}")

            for prod in venta_seleccionada_completa.get("productos_detalle", []):
                self.tree_detalle_historial_venta.insert("", tk.END, values=(
                    prod.get("nombre", "N/A"),
                    prod.get("cantidad", 0),
                    f"${prod.get('precio_unitario', 0.0):.2f}",
                    f"${prod.get('subtotal', 0.0):.2f}"
                ))

    def _poblar_historial_ventas_treeview(self, filtrar_por_fecha=False):
        fecha_inicio = None
        fecha_fin = None
        if filtrar_por_fecha:
            fecha_inicio = self.fecha_inicio_hist_var.get()
            fecha_fin = self.fecha_fin_hist_var.get()
            try:
                datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")  # Uso datetime.datetime
                datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")  # Uso datetime.datetime
                if fecha_inicio > fecha_fin:
                    messagebox.showerror("Error de Fechas",
                                         "La fecha de inicio no puede ser posterior a la fecha de fin.",
                                         parent=self.display_frame)
                    return
            except ValueError:
                messagebox.showerror("Error de Fechas", "Formato de fecha incorrecto. Use YYYY-MM-DD.",
                                     parent=self.display_frame)
                return

        resultado_ventas = obtener_ventas_para_historial_gui(fecha_inicio, fecha_fin)
        self.ventas_cargadas_actualmente = resultado_ventas.get('ventas_mostradas', [])

        if hasattr(self, 'tree_historial_ventas'):
            for i in self.tree_historial_ventas.get_children():
                self.tree_historial_ventas.delete(i)

        if hasattr(self, 'tree_detalle_historial_venta'):
            for i in self.tree_detalle_historial_venta.get_children():
                self.tree_detalle_historial_venta.delete(i)

        if hasattr(self, 'label_detalle_venta_id_frame'):
            self.label_detalle_venta_id_frame.config(text="Detalles de Venta ID: - (Seleccione una venta)")

        if not self.ventas_cargadas_actualmente:
            if hasattr(self, 'tree_historial_ventas'):
                self.tree_historial_ventas.insert("", tk.END,
                                                  values=("No hay ventas en este período.", "", "", "", ""))
            if hasattr(self, 'label_total_periodo_hist'):
                self.label_total_periodo_hist.config(text="Total del Período: $0.00")
            return

        if hasattr(self, 'tree_historial_ventas'):
            for venta in self.ventas_cargadas_actualmente:
                self.tree_historial_ventas.insert("", tk.END, iid=venta.get("id_venta"), values=(
                    venta.get("id_venta", "N/A"),
                    venta.get("fecha", "N/A"),
                    venta.get("nombre_cliente", "N/A"),
                    f"${venta.get('descuento_aplicado', 0.0):.2f}",
                    f"${venta.get('total_final', 0.0):.2f}"
                ))

        if hasattr(self, 'label_total_periodo_hist'):
            self.label_total_periodo_hist.config(
                text=f"Total del Período: ${resultado_ventas.get('total_periodo', 0.0):.2f}")

    def historial_ventas_action(self):  # Este es el método que faltaba
        self._clear_display_frame()

        # Frame para Filtros de Fecha
        filtro_frame = ttk.Frame(self.display_frame)
        filtro_frame.pack(fill=tk.X, pady=5)
        ttk.Label(filtro_frame, text="Fecha Inicio (YYYY-MM-DD):").pack(side=tk.LEFT, padx=5)
        ttk.Entry(filtro_frame, textvariable=self.fecha_inicio_hist_var, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Label(filtro_frame, text="Fecha Fin (YYYY-MM-DD):").pack(side=tk.LEFT, padx=5)
        ttk.Entry(filtro_frame, textvariable=self.fecha_fin_hist_var, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(filtro_frame, text="Filtrar",
                   command=lambda: self._poblar_historial_ventas_treeview(filtrar_por_fecha=True)).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(filtro_frame, text="Mostrar Todas",
                   command=lambda: self._poblar_historial_ventas_treeview(filtrar_por_fecha=False)).pack(
            side=tk.LEFT, padx=5)

        # Frame para TreeView de Historial de Ventas (Principal)
        hist_main_frame = ttk.Frame(self.display_frame)
        hist_main_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        columnas_hist = ("id_v", "fecha_v", "cliente_v", "descuento_v", "total_v")
        self.tree_historial_ventas = ttk.Treeview(hist_main_frame, columns=columnas_hist, show="headings",
                                                  height=10)
        self.tree_historial_ventas.heading("id_v", text="ID Venta");
        self.tree_historial_ventas.column("id_v", width=70, anchor=tk.CENTER)
        self.tree_historial_ventas.heading("fecha_v", text="Fecha y Hora");
        self.tree_historial_ventas.column("fecha_v", width=150)
        self.tree_historial_ventas.heading("cliente_v", text="Cliente");
        self.tree_historial_ventas.column("cliente_v", width=200)
        self.tree_historial_ventas.heading("descuento_v", text="Descuento");
        self.tree_historial_ventas.column("descuento_v", width=100, anchor=tk.E)
        self.tree_historial_ventas.heading("total_v", text="Total Venta");
        self.tree_historial_ventas.column("total_v", width=100, anchor=tk.E)

        scrollbar_hist_main = ttk.Scrollbar(hist_main_frame, orient=tk.VERTICAL,
                                            command=self.tree_historial_ventas.yview)
        self.tree_historial_ventas.configure(yscrollcommand=scrollbar_hist_main.set)
        scrollbar_hist_main.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_historial_ventas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree_historial_ventas.bind("<<TreeviewSelect>>", self._mostrar_detalle_venta_historial)

        # Frame para Detalles de la Venta Seleccionada
        # Guardamos la referencia al LabelFrame para poder cambiar su texto
        self.label_detalle_venta_id_frame = ttk.LabelFrame(self.display_frame,
                                                           text="Detalles de Venta ID: - (Seleccione una venta de arriba)",
                                                           padding="10")
        self.label_detalle_venta_id_frame.pack(fill=tk.X, pady=10)

        columnas_detalle = ("prod_d", "cant_d", "pu_d", "sub_d")
        self.tree_detalle_historial_venta = ttk.Treeview(self.label_detalle_venta_id_frame,
                                                         columns=columnas_detalle, show="headings", height=5)
        self.tree_detalle_historial_venta.heading("prod_d", text="Producto");
        self.tree_detalle_historial_venta.column("prod_d", width=250)
        self.tree_detalle_historial_venta.heading("cant_d", text="Cantidad");
        self.tree_detalle_historial_venta.column("cant_d", width=80, anchor=tk.CENTER)
        self.tree_detalle_historial_venta.heading("pu_d", text="Precio Unit.");
        self.tree_detalle_historial_venta.column("pu_d", width=100, anchor=tk.E)
        self.tree_detalle_historial_venta.heading("sub_d", text="Subtotal");
        self.tree_detalle_historial_venta.column("sub_d", width=100, anchor=tk.E)

        scrollbar_detalle = ttk.Scrollbar(self.label_detalle_venta_id_frame, orient=tk.VERTICAL,
                                          command=self.tree_detalle_historial_venta.yview)
        self.tree_detalle_historial_venta.configure(yscrollcommand=scrollbar_detalle.set)
        scrollbar_detalle.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_detalle_historial_venta.pack(fill=tk.BOTH, expand=True)

        # Label para el Total del Período
        self.label_total_periodo_hist = ttk.Label(self.display_frame, text="Total del Período: $0.00",
                                                  font=("Arial", 12, "bold"))
        self.label_total_periodo_hist.pack(pady=5, anchor="e")

        self._poblar_historial_ventas_treeview(filtrar_por_fecha=False)  # Cargar historial inicial

        # Métodos placeholder para los otros botones, si aún no están implementados

    def registrar_cliente_action(self):
        self._clear_display_frame()
        ttk.Label(self.display_frame, text="Formulario para Registrar Cliente (próximamente)",
                  font=("Arial", 12)).pack(padx=10, pady=10, anchor="center", expand=True)

    def historial_cliente_action(self):
        self._clear_display_frame()
        ttk.Label(self.display_frame, text="Historial de Cliente (próximamente)", font=("Arial", 12)).pack(padx=10,
                                                                                                           pady=10,
                                                                                                           anchor="center",
                                                                                                           expand=True)

#-----------------------------------------------------------------------------------------------------------------------

    def _mostrar_factura_en_ventana(self, texto_factura, venta_id, nombre_archivo_factura_guardada=None):
        factura_window = tk.Toplevel(self.root)
        factura_window.title(f"Factura #: {venta_id:05d}")
        factura_window.geometry("480x650")
        factura_window.transient(self.root)  # Hace que la ventana aparezca encima de la principal
        factura_window.grab_set()  # Hace la ventana modal (bloquea interacción con la ventana principal)
        factura_window.focus_set()  # Pone el foco en la nueva ventana

        # Frame para el texto y scrollbar
        text_frame = ttk.Frame(factura_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Courier New", 9), padx=10, pady=10, relief=tk.SOLID,
                              borderwidth=1)
        text_widget.insert(tk.END, texto_factura)
        text_widget.config(state=tk.DISABLED)  # Hacerlo de solo lectura

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Frame para botones
        button_frame = ttk.Frame(factura_window)
        button_frame.pack(fill=tk.X, pady=(5, 10))

        if nombre_archivo_factura_guardada:
            # Mostrar solo el nombre del archivo, no la ruta completa si es muy larga
            nombre_visible_archivo = os.path.basename(nombre_archivo_factura_guardada)
            if len(nombre_archivo_factura_guardada) > 50:  # Heurística para acortar
                nombre_visible_archivo = "..." + nombre_visible_archivo[-45:]

            saved_label = ttk.Label(button_frame, text=f"Guardada en: {nombre_visible_archivo}", font=("Arial", 8))
            saved_label.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

        def guardar_copia_factura():
            # Directorio inicial sugerido para guardar
            initial_dir = os.path.join(os.getcwd(), "Facturas")
            # Crear el directorio si no existe
            if not os.path.exists(initial_dir):
                try:
                    os.makedirs(initial_dir)
                except OSError as e:
                    messagebox.showerror("Error de Directorio", f"No se pudo crear el directorio Facturas:\n{e}",
                                         parent=factura_window)
                    return

            file_path = filedialog.asksaveasfilename(
                master=factura_window,  # Para que el diálogo aparezca sobre esta ventana
                initialdir=initial_dir,
                initialfile=f"copia_factura_{venta_id:05d}.txt",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if file_path:
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(texto_factura)
                    messagebox.showinfo("Guardado", f"Factura guardada en:\n{file_path}", parent=factura_window)
                except Exception as e:
                    messagebox.showerror("Error al Guardar", f"No se pudo guardar la factura:\n{e}",
                                         parent=factura_window)

        ttk.Button(button_frame, text="Guardar Copia Como...", command=guardar_copia_factura).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cerrar Vista", command=factura_window.destroy).pack(side=tk.RIGHT, padx=10)


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style(root)
    try:
        # Intenta usar un tema que permita mejor personalización si está disponible
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        elif 'vista' in style.theme_names(): # 'vista' es común en Windows
             style.theme_use('vista')
        # Puedes imprimir style.theme_names() para ver qué temas tienes disponibles
    except tk.TclError:
        print("No se pudo aplicar el tema preferido, usando default.")

    # Estilo para el botón de confirmar venta (azul)
    style.configure("Accent.TButton", foreground="white", background="#007bff", padding=6)
    style.map("Accent.TButton",
        background=[('active', '#0056b3'), ('pressed', '#004085')],
        relief=[('pressed', 'sunken'), ('!pressed', 'raised')])

    # --- NUEVO ESTILO PARA EL BOTÓN SALIR (ROJO) ---
    style.configure("Exit.TButton",
                    foreground="white",      # Color del texto blanco
                    background="#dc3545",    # Un tono de rojo (bootstrap danger red)
                    font=('Arial', 10, 'bold'),
                    padding=6)
    style.map("Exit.TButton",
        background=[('active', '#c82333'), ('pressed', '#bd2130')], # Tonos más oscuros para activo/presionado
        foreground=[('pressed', 'white'), ('active', 'white')],
        relief=[('pressed', 'sunken'), ('!pressed', 'raised')])
    # Nota: La efectividad de 'background' en ttk.Button puede depender del tema y S.O.
    # 'foreground' (color del texto) es usualmente más confiable.

    app = ColmadoApp(root)
    root.mainloop()