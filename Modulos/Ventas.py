# Modulos/Ventas.py

from datetime import datetime
from Modulos.Datos import cargar_datos, guardar_datos, ARCHIVO_PRODUCTOS, ARCHIVO_VENTAS, ARCHIVO_CLIENTES
# Estas importaciones son para la versión de consola, pueden omitirse si solo usas GUI
from Modulos.Clientes import listar_clientes 
from Modulos.Productos import listar_productos

# La función nueva_venta() es para la consola.
# La dejaremos como está por ahora, pero no calculará ITBIS a menos que se actualice.
def nueva_venta():
    """Procesa una venta con opción de cliente, descuentos y validación mejorada."""
    print("\n--- NUEVA VENTA (Consola) ---")
    print("ADVERTENCIA: Esta version de consola no calcula ITBIS detallado.")

    datos_productos = cargar_datos(ARCHIVO_PRODUCTOS)
    datos_ventas = cargar_datos(ARCHIVO_VENTAS)
    datos_clientes = cargar_datos(ARCHIVO_CLIENTES)

    if not datos_productos.get("productos"):
        print("❌ No hay productos registrados para vender.")
        return

    cliente_id = None
    if input("¿Asociar a cliente registrado? (s/n): ").lower() == 's':
        if listar_clientes(): 
            try:
                cliente_id_input = input("ID del cliente (0 para omitir): ")
                if cliente_id_input:
                    cliente_id = int(cliente_id_input)
                    if cliente_id != 0 and not any(c.get("id") == cliente_id for c in datos_clientes.get("clientes",[])):
                        print("⚠️ ID de cliente no encontrado. Continuando sin cliente asociado.")
                        cliente_id = None
                    elif cliente_id == 0:
                        cliente_id = None
            except ValueError:
                print("⚠️ Entrada invalida para ID de cliente. Continuando sin cliente.")
                cliente_id = None
        else:
            print("ℹ️ No hay clientes registrados para asociar.")

    if not listar_productos(mostrar_encabezado=False): 
        return 

    productos_vendidos = []
    total_venta_final = 0.0 # Este será el total con ITBIS, antes de descuento

    while True:
        try:
            id_producto_str = input("\nID del producto (0 para finalizar): ")
            if not id_producto_str: 
                continue
            id_producto = int(id_producto_str)

            if id_producto == 0:
                break

            producto_en_stock = None
            for p_stock in datos_productos.get("productos",[]):
                if p_stock.get("id") == id_producto:
                    producto_en_stock = p_stock
                    break

            if not producto_en_stock:
                print("❌ Producto no encontrado.")
                continue

            cantidad_str = input(f"Cantidad de '{producto_en_stock.get('nombre')}': ")
            if not cantidad_str: 
                continue
            cantidad = float(cantidad_str) 

            if cantidad <= 0:
                print("❌ La cantidad debe ser mayor a 0.")
                continue
            
            stock_disponible = float(producto_en_stock.get("stock", 0))
            if cantidad > stock_disponible:
                print(f"❌ Stock insuficiente. Disponible: {stock_disponible}")
                continue
            
            precio_unitario_con_itbis = float(producto_en_stock.get("precio_final_venta", producto_en_stock.get("precio_venta_sin_itbis", 0.0)))

            producto_en_stock["stock"] = stock_disponible - cantidad
            subtotal_item_con_itbis = precio_unitario_con_itbis * cantidad
            total_venta_final += subtotal_item_con_itbis
            
            productos_vendidos.append({
                "id": producto_en_stock.get("id"),
                "nombre": producto_en_stock.get("nombre"),
                "precio_unitario": precio_unitario_con_itbis, 
                "cantidad": cantidad,
                "subtotal": subtotal_item_con_itbis 
            })
            print(f"➕ {producto_en_stock.get('nombre')} x{cantidad} | RD$ {subtotal_item_con_itbis:.2f}")

        except ValueError:
            print("❌ Entrada invalida. Use numeros para ID y cantidad.")
        except Exception as e:
            print(f"⚠️ Ocurrio un error inesperado: {e}")

    if not productos_vendidos:
        print("ℹ️ Venta cancelada (no se agregaron productos).")
        return

    descuento_aplicado = 0.0
    total_a_pagar = total_venta_final

    if input("\n¿Aplicar descuento? (s/n): ").lower() == 's':
        try:
            tipo_descuento = input("Tipo de descuento (% o monto fijo, ej: 10% o 50): ").lower()
            if '%' in tipo_descuento:
                porcentaje_str = tipo_descuento.replace('%', '').strip()
                porcentaje = float(porcentaje_str)
                if 0 < porcentaje <= 100:
                    descuento_aplicado = total_a_pagar * (porcentaje / 100)
                else:
                    print("⚠️ Porcentaje de descuento invalido. No se aplicara descuento.")
            else:
                monto_descuento = float(tipo_descuento)
                if 0 < monto_descuento <= total_a_pagar:
                    descuento_aplicado = monto_descuento
                else:
                    print("⚠️ Monto de descuento invalido o excede el total. No se aplicara descuento.")
            
            total_a_pagar = max(0, total_a_pagar - descuento_aplicado)
            if descuento_aplicado > 0:
                print(f"🎫 Descuento aplicado: RD$ {descuento_aplicado:.2f}")
        except ValueError:
            print("⚠️ Descuento no valido. Ignorando.")

    print(f"\n🛒 TOTAL A PAGAR: RD$ {total_a_pagar:.2f}")
    if input("¿Confirmar venta? (s/n): ").lower() != 's':
        print("❌ Venta cancelada por el usuario.")
        for producto_vendido in productos_vendidos:
            for producto_original in datos_productos.get("productos",[]):
                if producto_vendido.get("id") == producto_original.get("id"):
                    producto_original["stock"] = float(producto_original.get("stock",0)) + float(producto_vendido.get("cantidad",0))
        print("ℹ️ Venta cancelada por el usuario. El stock ha sido restablecido.")
        return

    ventas_guardadas = datos_ventas.get("ventas", [])
    nueva_id_venta = max(v.get("id", 0) for v in ventas_guardadas) + 1 if ventas_guardadas else 1
    
    registro_nueva_venta = {
        "id": nueva_id_venta,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cliente_id": cliente_id,
        "productos": productos_vendidos,
        "subtotal_bruto_con_itbis": total_venta_final,
        "descuento_aplicado": descuento_aplicado,
        "total_neto": total_a_pagar,
    }
    ventas_guardadas.append(registro_nueva_venta)
    datos_ventas["ventas"] = ventas_guardadas

    if cliente_id:
        clientes_existentes = datos_clientes.get("clientes", [])
        for c_idx, cliente_actualizado in enumerate(clientes_existentes):
            if cliente_actualizado.get("id") == cliente_id:
                cliente_actualizado.setdefault("compras", []).append(nueva_id_venta)
                datos_clientes["clientes"][c_idx] = cliente_actualizado
                guardar_datos(datos_clientes, ARCHIVO_CLIENTES)
                break
        
    guardar_datos(datos_productos, ARCHIVO_PRODUCTOS) 
    guardar_datos(datos_ventas, ARCHIVO_VENTAS)

    print(f"\n✅ Venta registrada (ID: {nueva_id_venta})")
    if cliente_id:
        cliente_info = next((c for c in datos_clientes.get("clientes",[]) if c.get("id") == cliente_id), None)
        if cliente_info:
            print(f"📝 Cliente: {cliente_info.get('nombre')} (ID: {cliente_id})")

def procesar_nueva_venta_gui(cliente_id_seleccionado, items_vendidos, 
                             total_bruto_sin_itbis, 
                             itbis_total_venta,     
                             descuento_aplicado, 
                             total_neto,            
                             dinero_recibido=None,
                             cambio_devuelto=None):
    datos_ventas = cargar_datos(ARCHIVO_VENTAS)
    datos_productos = cargar_datos(ARCHIVO_PRODUCTOS)

    for item_gui in items_vendidos:
        producto_en_stock = next((p for p in datos_productos.get("productos", []) if p.get("id") == item_gui.get("id")), None)
        if not producto_en_stock:
            return {'exito': False,
                    'mensaje': f"Error critico: Producto '{item_gui.get('nombre')}' (ID: {item_gui.get('id')}) no encontrado en stock."}
        
        stock_actual_prod = float(producto_en_stock.get("stock", 0))
        cantidad_vendida_item = float(item_gui.get("cantidad", 0))

        if cantidad_vendida_item > stock_actual_prod:
            return {'exito': False,
                    'mensaje': f"Stock insuficiente para '{item_gui.get('nombre')}'. Disponible: {stock_actual_prod}, Solicitado: {cantidad_vendida_item}."}

    for producto_stock in datos_productos.get("productos", []):
        for item_vendido_gui in items_vendidos:
            if producto_stock.get("id") == item_vendido_gui.get("id"):
                cantidad_a_restar = float(item_vendido_gui.get("cantidad", 0))
                producto_stock["stock"] = float(producto_stock.get("stock",0)) - cantidad_a_restar
                break 
    guardar_datos(datos_productos, ARCHIVO_PRODUCTOS)

    ventas_existentes = datos_ventas.get("ventas", [])
    nueva_id_venta = max(v.get("id", 0) for v in ventas_existentes) + 1 if ventas_existentes else 1

    total_bruto_con_itbis_antes_descuento = total_bruto_sin_itbis + itbis_total_venta

    registro_nueva_venta = {
        "id": nueva_id_venta,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cliente_id": cliente_id_seleccionado,
        "productos": items_vendidos, # items_vendidos ya contiene 'itbis_item_total'
        "subtotal_bruto_sin_itbis": round(total_bruto_sin_itbis, 2), 
        "itbis_total_venta": round(itbis_total_venta, 2),          
        "subtotal_bruto_con_itbis": round(total_bruto_con_itbis_antes_descuento, 2),
        "descuento_aplicado": round(descuento_aplicado, 2),
        "total_neto": round(total_neto, 2), 
        "dinero_recibido": round(dinero_recibido, 2) if dinero_recibido is not None else None,
        "cambio_devuelto": round(cambio_devuelto, 2) if cambio_devuelto is not None else None
    }
    ventas_existentes.append(registro_nueva_venta)
    datos_ventas["ventas"] = ventas_existentes
    guardar_datos(datos_ventas, ARCHIVO_VENTAS)

    if cliente_id_seleccionado:
        datos_clientes = cargar_datos(ARCHIVO_CLIENTES)
        clientes_actuales = datos_clientes.get("clientes", [])
        for i, cliente_obj in enumerate(clientes_actuales):
            if cliente_obj.get("id") == cliente_id_seleccionado:
                cliente_obj.setdefault("compras", []).append(nueva_id_venta)
                datos_clientes["clientes"][i] = cliente_obj
                guardar_datos(datos_clientes, ARCHIVO_CLIENTES)
                break
    
    return {
        'exito': True,
        'mensaje': f"Venta ID: {nueva_id_venta} registrada con exito.",
        'venta_registrada': registro_nueva_venta
    }

def obtener_ventas_para_historial_gui(fecha_inicio_str=None, fecha_fin_str=None):
    datos_ventas = cargar_datos(ARCHIVO_VENTAS)
    if not datos_ventas.get("ventas"):
        return {'ventas_mostradas': [], 'total_periodo': 0.0}

    ventas_todas = datos_ventas.get("ventas", [])
    ventas_filtradas_por_fecha = []

    if fecha_inicio_str and fecha_fin_str:
        try:
            datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
            datetime.strptime(fecha_fin_str, "%Y-%m-%d")
            for venta in ventas_todas:
                fecha_venta_corta = venta.get("fecha", " ")[0:10]
                if fecha_inicio_str <= fecha_venta_corta <= fecha_fin_str:
                    ventas_filtradas_por_fecha.append(venta)
        except ValueError:
            print(f"Advertencia: Formato de fecha invalido para filtro: {fecha_inicio_str} / {fecha_fin_str}. Mostrando todas las ventas.")
            ventas_filtradas_por_fecha = ventas_todas
    else:
        ventas_filtradas_por_fecha = ventas_todas

    if not ventas_filtradas_por_fecha:
        return {'ventas_mostradas': [], 'total_periodo': 0.0}

    datos_clientes = cargar_datos(ARCHIVO_CLIENTES)
    clientes_map = {c.get("id"): c.get("nombre") for c in datos_clientes.get("clientes", [])}

    ventas_para_gui = []
    total_del_periodo_neto = 0.0

    for venta_raw in reversed(ventas_filtradas_por_fecha):
        cliente_id = venta_raw.get("cliente_id")
        nombre_cliente = clientes_map.get(cliente_id, "Consumidor Final") if cliente_id else "Consumidor Final"

        productos_detalle_gui = []
        for p_vendido in venta_raw.get("productos", []):
            cantidad = float(p_vendido.get("cantidad", 0))
            precio_unitario_final = float(p_vendido.get("precio_unitario", 0.0))
            subtotal_final_item = float(p_vendido.get("subtotal", 0.0))
            productos_detalle_gui.append({
                "nombre": p_vendido.get("nombre", "N/A"),
                "cantidad": cantidad,
                "precio_unitario": precio_unitario_final,
                "subtotal": subtotal_final_item
            })

        ventas_para_gui.append({
            "id_venta": venta_raw.get("id"),
            "fecha": venta_raw.get("fecha"),
            "nombre_cliente": nombre_cliente,
            "productos_detalle": productos_detalle_gui,
            "subtotal_bruto_sin_itbis": venta_raw.get("subtotal_bruto_sin_itbis", 0.0),
            "itbis_total_venta": venta_raw.get("itbis_total_venta", 0.0),            
            "subtotal_bruto_con_itbis": venta_raw.get("subtotal_bruto_con_itbis", 0.0),
            "descuento_aplicado": venta_raw.get("descuento_aplicado", 0.0),
            "total_final": venta_raw.get("total_neto", 0.0),
            "dinero_recibido": venta_raw.get("dinero_recibido"),
            "cambio_devuelto": venta_raw.get("cambio_devuelto")
        })
        total_del_periodo_neto += venta_raw.get("total_neto", 0.0)

    return {'ventas_mostradas': ventas_para_gui, 'total_periodo': total_del_periodo_neto}


def generar_texto_factura(datos_venta, nombre_cliente_str="Consumidor Final", datos_empresa=None):
    if nombre_cliente_str == "Ninguno" or not nombre_cliente_str:
        nombre_cliente_str = "Consumidor Final"

    empresa = datos_empresa or {}
    nombre_negocio = empresa.get("nombre", "PyColmado")
    direccion = empresa.get("direccion", "Avenida Ejemplo #123")
    ciudad = empresa.get("ciudad", "La Vega, Republica Dominicana")
    rnc = empresa.get("rnc", "101-00000-1")
    telefono = empresa.get("telefono")

    separador_largo = "=" * 45
    separador_corto = "-" * 45
    texto = []

    texto.append(f"       *** {nombre_negocio.upper()} *** ")
    texto.append(f"     {direccion[:30]:<30}")
    texto.append(f"   {ciudad[:32]:<32}")
    texto.append(f"       RNC: {rnc}       ")
    if telefono:
        texto.append(f"       Tel: {telefono}       ")
    texto.append(separador_largo)

    texto.append(f"FACTURA #: {datos_venta.get('id', 'N/A'):05d}")
    texto.append(f"Fecha y Hora: {datos_venta.get('fecha', 'N/A')}")
    texto.append(f"Cliente: {nombre_cliente_str}")
    texto.append(separador_corto)

    # Cambiar encabezado de columna P.Unit a ITBIS/U.
    texto.append(f"{'Cant':>4} {'Descripcion':<20} {'ITBIS/U.':>9} {'Monto':>9}")
    texto.append(separador_corto)

    productos_vendidos_items = datos_venta.get("productos", [])
    for prod in productos_vendidos_items:
        nombre_prod = prod.get("nombre", "N/A")[:20]
        cantidad_item = float(prod.get('cantidad', 0))
        # El 'subtotal' del item ya es el monto final con ITBIS
        subtotal_item_final = float(prod.get('subtotal', 0.0))
        
        # Calcular ITBIS unitario
        itbis_total_del_item = float(prod.get('itbis_item_total', 0.0))
        itbis_unitario = 0.0
        if cantidad_item > 0:
            itbis_unitario = itbis_total_del_item / cantidad_item
        
        try: # Formateo de cantidad
            if cantidad_item.is_integer():
                cantidad_str = f"{int(cantidad_item):>4}"
            else:
                cantidad_str = f"{cantidad_item:>4.2f}"
        except AttributeError: # Manejar si cantidad_item es int y no tiene is_integer
             cantidad_str = f"{int(cantidad_item):>4}"
        except ValueError: # Por si acaso
            cantidad_str = f"{str(cantidad_item):>4}"

        # Mostrar ITBIS unitario en la columna correspondiente
        texto.append(f"{cantidad_str} {nombre_prod:<20} RD${itbis_unitario:>7.2f} RD${subtotal_item_final:>7.2f}")

    texto.append(separador_corto)

    ancho_etiqueta_total = 30
    subtotal_sin_itbis_factura = datos_venta.get('subtotal_bruto_sin_itbis', 0.0)
    itbis_total_factura = datos_venta.get('itbis_total_venta', 0.0)
    subtotal_con_itbis_factura = datos_venta.get('subtotal_bruto_con_itbis', subtotal_sin_itbis_factura + itbis_total_factura)

    texto.append(f"{'SUBTOTAL SIN ITBIS:':>{ancho_etiqueta_total}} RD$ {subtotal_sin_itbis_factura:>8.2f}")
    texto.append(f"{'ITBIS TOTAL:':>{ancho_etiqueta_total}} RD$ {itbis_total_factura:>8.2f}")
    texto.append(f"{'SUBTOTAL CON ITBIS:':>{ancho_etiqueta_total}} RD$ {subtotal_con_itbis_factura:>8.2f}")
    
    if datos_venta.get('descuento_aplicado', 0.0) > 0:
        texto.append(f"{'DESCUENTO:':>{ancho_etiqueta_total}} RD$ {datos_venta.get('descuento_aplicado', 0.0):>8.2f}")
    
    texto.append(f"{'TOTAL NETO A PAGAR:':>{ancho_etiqueta_total}} RD$ {datos_venta.get('total_neto', 0.0):>8.2f}")
    texto.append(separador_corto)
    
    dinero_recibido_factura = datos_venta.get('dinero_recibido', 0.0) if datos_venta.get('dinero_recibido') is not None else 0.0
    cambio_devuelto_factura = datos_venta.get('cambio_devuelto', 0.0) if datos_venta.get('cambio_devuelto') is not None else 0.0

    texto.append(f"{'DINERO RECIBIDO:':>{ancho_etiqueta_total}} RD$ {dinero_recibido_factura:>8.2f}")
    texto.append(f"{'CAMBIO DEVUELTO:':>{ancho_etiqueta_total}} RD$ {cambio_devuelto_factura:>8.2f}")

    texto.append(separador_largo)
    texto.append("    ¡Gracias por su compra!    ")
    texto.append(separador_largo)

    return "\n".join(texto)

