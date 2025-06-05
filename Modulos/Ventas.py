from datetime import datetime

from Modulos.Clientes import listar_clientes  # Necesitamos listar_clientes para asociar venta
from Modulos.Datos import cargar_datos, guardar_datos, ARCHIVO_PRODUCTOS, ARCHIVO_VENTAS, ARCHIVO_CLIENTES
from Modulos.Productos import listar_productos  # Necesitamos listar_productos para la venta


def nueva_venta():
    """Procesa una venta con opción de cliente, descuentos y validación mejorada."""
    print("\n--- NUEVA VENTA ---")

    datos_productos = cargar_datos(ARCHIVO_PRODUCTOS)
    datos_ventas = cargar_datos(ARCHIVO_VENTAS)
    datos_clientes = cargar_datos(ARCHIVO_CLIENTES)

    if not datos_productos["productos"]:
        print("❌ No hay productos registrados para vender.")
        return

    cliente_id = None
    if input("¿Asociar a cliente registrado? (s/n): ").lower() == 's':
        if listar_clientes():  # Solo si hay clientes
            try:
                cliente_id_input = input("ID del cliente (0 para omitir): ")
                if cliente_id_input:
                    cliente_id = int(cliente_id_input)
                    if cliente_id != 0 and not any(c["id"] == cliente_id for c in datos_clientes["clientes"]):
                        print("⚠️ ID de cliente no encontrado. Continuando sin cliente asociado.")
                        cliente_id = None
                    elif cliente_id == 0:
                        cliente_id = None
            except ValueError:
                print("⚠️ Entrada inválida para ID de cliente. Continuando sin cliente.")
                cliente_id = None
        else:
            print("ℹ️ No hay clientes registrados para asociar.")

    if not listar_productos(mostrar_encabezado=False):  # No mostrar encabezado si no hay productos
        return  # Ya se imprimió mensaje desde listar_productos

    productos_vendidos = []
    total_venta = 0.0

    while True:
        try:
            id_producto_str = input("\nID del producto (0 para finalizar): ")
            if not id_producto_str:  # Si presiona Enter sin nada
                continue
            id_producto = int(id_producto_str)

            if id_producto == 0:
                break

            producto_en_stock = None
            # Iterar para encontrar el producto y trabajar con la referencia directa
            for p_stock in datos_productos["productos"]:
                if p_stock["id"] == id_producto:
                    producto_en_stock = p_stock
                    break

            if not producto_en_stock:
                print("❌ Producto no encontrado.")
                continue

            cantidad_str = input(f"Cantidad de '{producto_en_stock['nombre']}': ")
            if not cantidad_str:  # Si presiona Enter sin nada
                continue
            cantidad = float(cantidad_str)  # Permitir decimales para productos por peso/volumen

            if cantidad <= 0:
                print("❌ La cantidad debe ser mayor a 0.")
                continue
            if cantidad > producto_en_stock["stock"]:
                print(f"❌ Stock insuficiente. Disponible: {producto_en_stock['stock']}")
                continue

            # Actualizar stock del producto original
            producto_en_stock["stock"] -= cantidad
            subtotal = producto_en_stock["precio"] * cantidad
            total_venta += subtotal
            productos_vendidos.append({
                "id": producto_en_stock["id"],
                "nombre": producto_en_stock["nombre"],
                "precio_unitario": producto_en_stock["precio"],
                "cantidad": cantidad,
                "subtotal": subtotal
            })
            print(f"➕ {producto_en_stock['nombre']} x{cantidad} | ${subtotal:.2f}")

        except ValueError:
            print("❌ Entrada inválida. Use números para ID y cantidad.")
        except Exception as e:
            print(f"⚠️ Ocurrió un error inesperado: {e}")

    if not productos_vendidos:
        print("ℹ️ Venta cancelada (no se agregaron productos).")
        return

    descuento_aplicado = 0.0
    if input("\n¿Aplicar descuento? (s/n): ").lower() == 's':
        try:
            tipo_descuento = input("Tipo de descuento (% o monto fijo, ej: 10% o 50): ").lower()
            if '%' in tipo_descuento:
                porcentaje_str = tipo_descuento.replace('%', '').strip()
                porcentaje = float(porcentaje_str)
                if 0 < porcentaje <= 100:
                    descuento_aplicado = total_venta * (porcentaje / 100)
                else:
                    print("⚠️ Porcentaje de descuento inválido. No se aplicará descuento.")
            else:
                monto_descuento = float(tipo_descuento)
                if 0 < monto_descuento <= total_venta:
                    descuento_aplicado = monto_descuento
                else:
                    print("⚠️ Monto de descuento inválido o excede el total. No se aplicará descuento.")

            total_venta = max(0, total_venta - descuento_aplicado)
            if descuento_aplicado > 0:
                print(f"🎫 Descuento aplicado: ${descuento_aplicado:.2f}")
        except ValueError:
            print("⚠️ Descuento no válido. Ignorando.")

    print(f"\n🛒 TOTAL A PAGAR: ${total_venta:.2f}")
    if input("¿Confirmar venta? (s/n): ").lower() != 's':
        print("❌ Venta cancelada por el usuario.")
        # Devolver stock si la venta se cancela aquí
        for producto_vendido in productos_vendidos:
            for producto_original in datos_productos["productos"]:
                if producto_vendido["id"] == producto_original["id"]:
                    producto_original["stock"] += producto_vendido["cantidad"]

        print("ℹ️ Venta cancelada por el usuario. El stock ha sido restablecido.")
        return

    nueva_id_venta = len(datos_ventas["ventas"]) + 1
    registro_nueva_venta = {
        "id": nueva_id_venta,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": total_venta,
        "cliente_id": cliente_id,
        "productos": productos_vendidos,
        "descuento": descuento_aplicado
    }
    datos_ventas["ventas"].append(registro_nueva_venta)

    if cliente_id:
        cliente_actualizado = next((c for c in datos_clientes["clientes"] if c["id"] == cliente_id), None)
        if cliente_actualizado:
            cliente_actualizado["compras"].append(nueva_id_venta)
            guardar_datos(datos_clientes, ARCHIVO_CLIENTES)

    guardar_datos(datos_productos, ARCHIVO_PRODUCTOS)  # Guardar el stock actualizado
    guardar_datos(datos_ventas, ARCHIVO_VENTAS)

    print(f"\n✅ Venta registrada (ID: {nueva_id_venta})")
    if cliente_id:
        cliente_info = next((c for c in datos_clientes["clientes"] if c["id"] == cliente_id), None)
        if cliente_info:
            print(f"📝 Cliente: {cliente_info['nombre']} (ID: {cliente_id})")


def historial_ventas():
    """Muestra ventas filtradas por fecha y calcula totales."""
    print("\n--- HISTORIAL DE VENTAS ---")
    print("1. Ver todas las ventas")
    print("2. Filtrar por rango de fechas")
    opcion = input("Seleccione una opción (1/2): ")

    datos_ventas = cargar_datos(ARCHIVO_VENTAS)
    if not datos_ventas["ventas"]:
        print("❌ No hay ventas registradas.")
        return

    ventas_filtradas = []
    if opcion == "1":
        ventas_filtradas = datos_ventas["ventas"]
    elif opcion == "2":
        try:
            fecha_inicio_str = input("Fecha inicial (YYYY-MM-DD): ")
            fecha_fin_str = input("Fecha final (YYYY-MM-DD): ")
            # Validar formato simple
            datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
            datetime.strptime(fecha_fin_str, "%Y-%m-%d")

            for venta in datos_ventas["ventas"]:
                if fecha_inicio_str <= venta["fecha"][:10] <= fecha_fin_str:
                    ventas_filtradas.append(venta)
        except ValueError:
            print("❌ Formato de fecha incorrecto. Use YYYY-MM-DD.")
            return
    else:
        print("❌ Opción inválida.")
        return

    if not ventas_filtradas:
        print("ℹ️ No hay ventas en el período seleccionado o que coincidan con el filtro.")
        return

    print("\n--- RESULTADOS DEL HISTORIAL ---")
    total_periodo_ventas = 0.0
    datos_clientes = cargar_datos(ARCHIVO_CLIENTES)  # Para mostrar nombre de cliente

    for venta in ventas_filtradas:
        nombre_cliente = "N/A"
        if venta.get("cliente_id"):
            cliente_obj = next((c for c in datos_clientes["clientes"] if c["id"] == venta["cliente_id"]), None)
            if cliente_obj:
                nombre_cliente = cliente_obj["nombre"]

        print(
            f"\nID Venta: {venta['id']} | 📅 Fecha: {venta['fecha']} | Cliente: {nombre_cliente} (ID: {venta.get('cliente_id', 'N/A')})")
        print("📦 Productos:")
        for producto in venta["productos"]:
            print(f"    - {producto['nombre']} x{producto['cantidad']} (${producto['subtotal']:.2f})")
        if venta.get("descuento", 0) > 0:
            print(f"   Descuento Aplicado: ${venta['descuento']:.2f}")
        print(f"   Total Venta: ${venta['total']:.2f}")
        total_periodo_ventas += venta["total"]

    print(f"\n💰 TOTAL GENERAL DEL PERÍODO SELECCIONADO: ${total_periodo_ventas:.2f}")

#-----------------------------------------------------------------------------------------------------------------------

def procesar_nueva_venta_gui(cliente_id_seleccionado, items_vendidos, total_bruto,
                             descuento_aplicado, total_neto, dinero_recibido=None,
                             cambio_devuelto=None):  # Nuevos parámetros
    """
    Procesa y guarda una nueva venta realizada desde la GUI.
    Actualiza el stock de productos y el historial del cliente.
    Items_vendidos: lista de dicts [{id, nombre, precio_unitario, cantidad, subtotal}, ...]
    Retorna un diccionario con {'exito': True/False, 'mensaje': '...'}
    """
    datos_ventas = cargar_datos(ARCHIVO_VENTAS)  #
    datos_productos = cargar_datos(ARCHIVO_PRODUCTOS)  #

    # ... (verificación de stock como estaba) ...
    for item_gui in items_vendidos:
        producto_en_stock = next((p for p in datos_productos["productos"] if p["id"] == item_gui["id"]), None)
        if not producto_en_stock:
            return {'exito': False,
                    'mensaje': f"Error crítico: Producto '{item_gui['nombre']}' (ID: {item_gui['id']}) no encontrado en stock."}
        if item_gui["cantidad"] > producto_en_stock["stock"]:
            return {'exito': False,
                    'mensaje': f"Stock insuficiente para '{item_gui['nombre']}'. Disponible: {producto_en_stock['stock']}, Solicitado: {item_gui['cantidad']}."}

    for p_stock in datos_productos["productos"]:
        for item_gui in items_vendidos:
            if p_stock["id"] == item_gui["id"]:
                p_stock["stock"] -= item_gui["cantidad"]
                break  # El producto ya se encontró y actualizó, pasar al siguiente producto en stock

    guardar_datos(datos_productos, ARCHIVO_PRODUCTOS)  #

    if datos_ventas.get("ventas", []):
        nueva_id_venta = max(v.get("id", 0) for v in datos_ventas["ventas"]) + 1
    else:
        nueva_id_venta = 1

    registro_nueva_venta = {
        "id": nueva_id_venta,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": total_neto,
        "cliente_id": cliente_id_seleccionado,
        "productos": items_vendidos,
        "descuento_aplicado": descuento_aplicado,
        "subtotal_bruto": total_bruto,
        "dinero_recibido": dinero_recibido,  # Nuevo campo
        "cambio_devuelto": cambio_devuelto  # Nuevo campo
    }
    datos_ventas.setdefault("ventas", []).append(registro_nueva_venta)
    guardar_datos(datos_ventas, ARCHIVO_VENTAS)  #

    if cliente_id_seleccionado:
        datos_clientes = cargar_datos(ARCHIVO_CLIENTES)  #
        cliente_actualizado = next((c for c in datos_clientes["clientes"] if c["id"] == cliente_id_seleccionado), None)
        if cliente_actualizado:
            cliente_actualizado.setdefault("compras", []).append(nueva_id_venta)
            guardar_datos(datos_clientes, ARCHIVO_CLIENTES)  #

    if cliente_id_seleccionado:
        # ... (lógica para actualizar cliente como estaba) ...
        pass  # Asegúrate que esta parte esté completa

    return {
        'exito': True,
        'mensaje': f"Venta ID: {nueva_id_venta} registrada con éxito.",
        'venta_registrada': registro_nueva_venta  # <-- AÑADIR ESTO
    }

#-----------------------------------------------------------------------------------------------------------------------

def obtener_ventas_para_historial_gui(fecha_inicio_str=None, fecha_fin_str=None):
    """
    Carga y filtra las ventas, incluyendo nombres de clientes y detalles de productos.
    Retorna un diccionario: {'ventas_mostradas': lista_de_ventas, 'total_periodo': float}
    Cada 'venta' en la lista es un diccionario con todos los detalles necesarios para la GUI.
    """
    datos_ventas = cargar_datos(ARCHIVO_VENTAS)  #
    if not datos_ventas.get("ventas"):
        return {'ventas_mostradas': [], 'total_periodo': 0.0}

    ventas_todas = datos_ventas["ventas"]
    ventas_filtradas_por_fecha = []

    if fecha_inicio_str and fecha_fin_str:
        try:
            # Validar fechas (la GUI debería enviar formato correcto, pero una verificación no daña)
            datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
            datetime.strptime(fecha_fin_str, "%Y-%m-%d")
            for venta in ventas_todas:
                fecha_venta_corta = venta.get("fecha", " विपक्ष ")[0:10]  # Tomar solo YYYY-MM-DD
                if fecha_inicio_str <= fecha_venta_corta <= fecha_fin_str:
                    ventas_filtradas_por_fecha.append(venta)
        except ValueError:
            # Si las fechas son inválidas, se podría retornar un error o lista vacía.
            # Por ahora, si hay error de formato de fecha, no se aplicará el filtro de fecha.
            # Lo ideal es que la GUI valide antes de llamar.
            # Para este ejemplo, si las fechas son inválidas, mostraremos todas.
            print(
                f"Advertencia: Formato de fecha inválido para filtro: {fecha_inicio_str} / {fecha_fin_str}. Mostrando todas las ventas.")
            ventas_filtradas_por_fecha = ventas_todas
    else:
        ventas_filtradas_por_fecha = ventas_todas

    if not ventas_filtradas_por_fecha:
        return {'ventas_mostradas': [], 'total_periodo': 0.0}

    datos_clientes = cargar_datos(ARCHIVO_CLIENTES)  #
    clientes_map = {c["id"]: c["nombre"] for c in datos_clientes.get("clientes", [])}

    ventas_para_gui = []
    total_del_periodo = 0.0

    for venta_raw in reversed(ventas_filtradas_por_fecha):  # Mostrar las más recientes primero
        cliente_id = venta_raw.get("cliente_id")
        nombre_cliente = clientes_map.get(cliente_id, "Consumidor Final") if cliente_id else "Consumidor Final"

        productos_detalle = []
        for p_vendido in venta_raw.get("productos", []):
            cantidad = p_vendido.get("cantidad", 0)
            subtotal = p_vendido.get("subtotal", 0.0)
            # Calcular precio unitario si no está explícitamente
            precio_unitario = p_vendido.get("precio_unitario")
            if precio_unitario is None and cantidad > 0:
                precio_unitario = subtotal / cantidad
            elif precio_unitario is None:
                precio_unitario = 0.0

            productos_detalle.append({
                "nombre": p_vendido.get("nombre", "N/A"),
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "subtotal": subtotal
            })

        ventas_para_gui.append({
            "id_venta": venta_raw.get("id"),
            "fecha": venta_raw.get("fecha"),
            "nombre_cliente": nombre_cliente,
            "productos_detalle": productos_detalle,
            "subtotal_bruto": venta_raw.get("subtotal_bruto",
                                            venta_raw.get("total", 0.0) + venta_raw.get("descuento_aplicado", 0.0)),
            # Calcular si no está
            "descuento_aplicado": venta_raw.get("descuento_aplicado", 0.0),
            "total_final": venta_raw.get("total"),
            "dinero_recibido": venta_raw.get("dinero_recibido"),
            "cambio_devuelto": venta_raw.get("cambio_devuelto")
        })
        total_del_periodo += venta_raw.get("total", 0.0)

    return {'ventas_mostradas': ventas_para_gui, 'total_periodo': total_del_periodo}

#-----------------------------------------------------------------------------------------------------------------------
# Estilo de la Factura

def generar_texto_factura(datos_venta, nombre_cliente_str="Consumidor Final"):
    """
    Genera un string de texto formateado para la factura.
    datos_venta es el diccionario de la venta tal como se guarda en ventas.json.
    """
    if nombre_cliente_str == "Ninguno" or not nombre_cliente_str:
        nombre_cliente_str = "Consumidor Final"

    separador_largo = "=" * 45
    separador_corto = "-" * 45
    texto = []

    # Encabezado del Colmado (Personaliza esto)
    texto.append("       *** PYCOLMADO *** ")
    texto.append("     Avenida Ejemplo #123    ")
    texto.append("   La Vega, República Dominicana  ")
    texto.append("       RNC: 101-00000-1       ")
    texto.append(separador_largo)

    texto.append(f"FACTURA #: {datos_venta.get('id', 'N/A'):05d}")
    texto.append(f"Fecha y Hora: {datos_venta.get('fecha', 'N/A')}")
    texto.append(f"Cliente: {nombre_cliente_str}")
    texto.append(separador_corto)

    texto.append(f"{'Cant':>4} {'Descripción':<20} {'P.Unit':>9} {'Monto':>9}")
    texto.append(separador_corto)

    productos = datos_venta.get("productos", [])
    for prod in productos:
        nombre_prod = prod.get("nombre", "N/A")[:20]
        cantidad = prod.get('cantidad', 0)
        precio_u = prod.get('precio_unitario', 0.0)
        # Calcular precio unitario si no está y la cantidad es válida
        if precio_u == 0.0 and cantidad != 0:
            precio_u = prod.get('subtotal', 0.0) / cantidad if cantidad else 0.0

        subtotal_item = prod.get('subtotal', 0.0)

        try:
            if float(cantidad).is_integer():
                cantidad_str = f"{int(cantidad):>4}"
            else:
                cantidad_str = f"{float(cantidad):>4.2f}"
        except ValueError:
            cantidad_str = f"{str(cantidad):>4}"

        texto.append(f"{cantidad_str} {nombre_prod:<20} ${precio_u:>8.2f} ${subtotal_item:>8.2f}")

    texto.append(separador_corto)

    ancho_etiqueta_total = 30

    texto.append(f"{'SUBTOTAL BRUTO:':>{ancho_etiqueta_total}} ${datos_venta.get('subtotal_bruto', 0.0):>10.2f}")
    if datos_venta.get('descuento_aplicado', 0.0) > 0:
        texto.append(f"{'DESCUENTO:':>{ancho_etiqueta_total}} ${datos_venta.get('descuento_aplicado', 0.0):>10.2f}")
    texto.append(f"{'TOTAL NETO:':>{ancho_etiqueta_total}} ${datos_venta.get('total', 0.0):>10.2f}")
    texto.append(separador_corto)
    texto.append(f"{'DINERO RECIBIDO:':>{ancho_etiqueta_total}} ${datos_venta.get('dinero_recibido', 0.0):>10.2f}")
    texto.append(f"{'CAMBIO DEVUELTO:':>{ancho_etiqueta_total}} ${datos_venta.get('cambio_devuelto', 0.0):>10.2f}")

    texto.append(separador_largo)
    texto.append("    ¡Gracias por su compra!    ")
    texto.append(separador_largo)

    return "\n".join(texto)
