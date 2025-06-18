from Modulos.Datos import cargar_datos, guardar_datos, ARCHIVO_CLIENTES, ARCHIVO_VENTAS

def registrar_cliente():
    """Registra un nuevo cliente en el sistema (versión de consola)."""
    print("\n--- REGISTRAR CLIENTE (Consola) ---")
    nombre = input("Nombre completo: ")
    telefono = input("Teléfono: ")
    direccion = input("Dirección (opcional): ")

    datos = cargar_datos(ARCHIVO_CLIENTES)
    clientes = datos.get("clientes", []) # Usar .get para seguridad
    
    # Generar nuevo ID
    if clientes:
        nuevo_id = max(c.get("id", 0) for c in clientes) + 1
    else:
        nuevo_id = 1
        
    nuevo_cliente = {
        "id": nuevo_id,
        "nombre": nombre.strip(),
        "telefono": telefono.strip(),
        "direccion": direccion.strip(),
        "compras": []  # Historial de IDs de ventas
    }
    clientes.append(nuevo_cliente)
    datos["clientes"] = clientes
    guardar_datos(datos, ARCHIVO_CLIENTES)
    print(f"✅ Cliente '{nombre}' registrado (ID: {nuevo_cliente['id']})")


def guardar_nuevo_cliente_desde_gui(nombre, telefono, direccion):
    """
    Guarda un nuevo cliente desde la GUI.
    Valida que el nombre y teléfono no estén vacíos.
    Retorna un diccionario con 'exito': True/False y 'mensaje': "..."
    """
    if not nombre.strip() or not telefono.strip():
        return {"exito": False, "mensaje": "El nombre y el teléfono son obligatorios."}

    datos_clientes = cargar_datos(ARCHIVO_CLIENTES)
    clientes = datos_clientes.get("clientes", [])

    # Verificar si el cliente ya existe (por nombre y teléfono)
    for cliente_existente in clientes:
        if cliente_existente.get("nombre", "").lower() == nombre.strip().lower() and \
           cliente_existente.get("telefono", "") == telefono.strip():
            return {
                "exito": False,
                "mensaje": f"El cliente '{nombre.strip()}' con teléfono '{telefono.strip()}' ya existe (ID: {cliente_existente.get('id')})."
            }

    if clientes:
        nuevo_id = max(c.get("id", 0) for c in clientes) + 1
    else:
        nuevo_id = 1
    
    nuevo_cliente = {
        "id": nuevo_id,
        "nombre": nombre.strip(),
        "telefono": telefono.strip(),
        "direccion": direccion.strip(),
        "compras": [] 
    }
    
    clientes.append(nuevo_cliente)
    datos_clientes["clientes"] = clientes 
    guardar_datos(datos_clientes, ARCHIVO_CLIENTES)
    
    return {"exito": True, "mensaje": f"Cliente '{nombre.strip()}' (ID: {nuevo_id}) registrado exitosamente."}


def listar_clientes():
    """Muestra todos los clientes registrados (versión de consola)."""
    datos = cargar_datos(ARCHIVO_CLIENTES)
    clientes = datos.get("clientes", [])
    print("\n--- CLIENTES REGISTRADOS (Consola) ---")
    if not clientes:
        print("ℹ️ No hay clientes registrados.")
        return False 
    for cliente in clientes:
        print(f"ID: {cliente.get('id','N/A')} | {cliente.get('nombre','Sin Nombre')} | Tel: {cliente.get('telefono','Sin Teléfono')}")
    return True


def historial_cliente():
    """Muestra las compras de un cliente específico (versión de consola)."""
    if not listar_clientes(): 
        return

    try:
        id_cliente_str = input("\nID del cliente a consultar: ")
        if not id_cliente_str.strip():
            print("❌ ID no proporcionado.")
            return
        id_cliente = int(id_cliente_str)
    except ValueError:
        print("❌ ID inválido. Debe ser un número.")
        return

    datos_clientes = cargar_datos(ARCHIVO_CLIENTES)
    datos_ventas = cargar_datos(ARCHIVO_VENTAS)
    clientes = datos_clientes.get("clientes", [])
    ventas = datos_ventas.get("ventas", [])

    cliente = next((c for c in clientes if c.get("id") == id_cliente), None)
    if not cliente:
        print(f"❌ Cliente con ID {id_cliente} no encontrado.")
        return

    print(f"\n📋 HISTORIAL DE {cliente.get('nombre','Cliente Desconocido').upper()}")
    ids_compras_cliente = cliente.get("compras", [])
    
    if not ids_compras_cliente:
        print("ℹ️ Este cliente no tiene compras registradas.")
        return

    compras_encontradas = 0
    total_gastado_cliente = 0.0

    for venta_id in ids_compras_cliente:
        venta_detalle = next((v for v in ventas if v.get("id") == venta_id), None)
        if venta_detalle:
            compras_encontradas += 1
            total_venta_actual = venta_detalle.get('total', 0.0)
            total_gastado_cliente += total_venta_actual
            print(f"\n📅 Fecha: {venta_detalle.get('fecha','N/A')} | Venta ID: {venta_id} | Total: ${total_venta_actual:.2f}")
            productos_vendidos = venta_detalle.get("productos", [])
            if productos_vendidos:
                for producto in productos_vendidos:
                    print(f"    - {producto.get('nombre','N/A')} x{producto.get('cantidad','N/A')} (${producto.get('subtotal',0.0):.2f})")
            else:
                print("    - No hay detalle de productos para esta venta.")
        else:
            print(f"⚠️ Venta con ID {venta_id} (listada en historial del cliente) no fue encontrada en el archivo general de ventas.")
    
    if compras_encontradas > 0:
        print(f"\n💰 Total gastado por {cliente.get('nombre','Cliente Desconocido')}: ${total_gastado_cliente:.2f}")
    elif not ids_compras_cliente: # Doble chequeo, aunque el primero ya debería cubrirlo.
        print("ℹ️ Este cliente no tiene compras registradas.")


def obtener_lista_clientes_para_combobox():
    """
    Carga los clientes y devuelve una lista de diccionarios con 'id' y 'nombre',
    adecuada para un combobox. Incluye un cliente genérico "Consumidor Final" sin ID persistente.
    """
    datos_clientes = cargar_datos(ARCHIVO_CLIENTES)
    clientes_registrados = datos_clientes.get("clientes", [])
    
    lista_para_combobox = []
    # lista_para_combobox.append({"id": None, "nombre": "Consumidor Final"}) # Opción si quieres que "Consumidor Final" sea seleccionable

    for cliente in clientes_registrados:
        if cliente.get("id") and cliente.get("nombre"): # Asegurar que tengan ID y nombre
            lista_para_combobox.append({"id": cliente["id"], "nombre": cliente["nombre"]})
            
    # Ordenar por nombre para facilitar la búsqueda en el combobox
    lista_para_combobox.sort(key=lambda x: x["nombre"])
    
    return lista_para_combobox

def obtener_historial_compras_cliente_gui(cliente_id):
    """
    Obtiene la información del cliente y su historial de compras formateado para la GUI.
    Retorna un diccionario con los datos del cliente, su historial y el total gastado.
    """
    datos_clientes = cargar_datos(ARCHIVO_CLIENTES)
    datos_ventas = cargar_datos(ARCHIVO_VENTAS)

    cliente_encontrado = None
    for c in datos_clientes.get("clientes", []):
        if c.get("id") == cliente_id:
            cliente_encontrado = c
            break
    
    if not cliente_encontrado:
        return {"exito": False, "mensaje": f"Cliente con ID {cliente_id} no encontrado."}

    cliente_info = {
        "id": cliente_encontrado.get("id"),
        "nombre": cliente_encontrado.get("nombre", "N/A"),
        "telefono": cliente_encontrado.get("telefono", "N/A"),
        "direccion": cliente_encontrado.get("direccion", "N/A")
    }

    historial_compras_gui = []
    total_gastado_cliente = 0.0
    
    ids_compras_del_cliente = cliente_encontrado.get("compras", [])
    
    # También es buena idea verificar las ventas que tengan el cliente_id directamente,
    # por si el array 'compras' del cliente no estuviera sincronizado por alguna razón.
    # (Aunque la lógica actual en procesar_nueva_venta_gui debería mantenerlos sincronizados)
    
    for venta_guardada in datos_ventas.get("ventas", []):
        # Comprobar si la venta pertenece al cliente por ID directo o por estar en su lista de compras
        if venta_guardada.get("cliente_id") == cliente_id or venta_guardada.get("id") in ids_compras_del_cliente:
            # Asegurar que no se añadan duplicados si ambos criterios se cumplen
            if not any(hc['id_venta'] == venta_guardada.get("id") for hc in historial_compras_gui):
                
                productos_detalle_gui = []
                for prod_vendido in venta_guardada.get("productos", []):
                    # Intentar obtener precio_unitario, si no, calcularlo si es posible
                    precio_u = prod_vendido.get("precio_unitario")
                    cantidad = prod_vendido.get("cantidad", 0)
                    subtotal = prod_vendido.get("subtotal", 0.0)

                    if precio_u is None and cantidad > 0: # Si no hay precio unitario pero sí cantidad
                        precio_u = subtotal / cantidad
                    elif precio_u is None: # Si no hay ni precio_unitario ni cantidad para calcularlo
                        precio_u = 0.0
                        
                    productos_detalle_gui.append({
                        "nombre": prod_vendido.get("nombre", "N/A"),
                        "cantidad": cantidad,
                        "precio_unitario": precio_u,
                        "subtotal": subtotal
                    })
                
                venta_para_gui = {
                    "id_venta": venta_guardada.get("id"),
                    "fecha": venta_guardada.get("fecha", "N/A"),
                    "total_final": venta_guardada.get("total", 0.0), # 'total' es el total neto de la venta
                    "productos_detalle": productos_detalle_gui,
                    # Podrías añadir más detalles de la venta si los necesitas en la GUI
                    # "descuento_aplicado": venta_guardada.get("descuento_aplicado", 0.0),
                    # "subtotal_bruto": venta_guardada.get("subtotal_bruto", 0.0)
                }
                historial_compras_gui.append(venta_para_gui)
                total_gastado_cliente += venta_guardada.get("total", 0.0)

    # Ordenar el historial de compras por fecha (más recientes primero, opcional)
    try:
        historial_compras_gui.sort(key=lambda v: v.get("fecha", ""), reverse=True)
    except Exception as e:
        print(f"Advertencia: No se pudo ordenar el historial de compras del cliente por fecha. {e}")


    return {
        "exito": True,
        "cliente_info": cliente_info,
        "historial_compras": historial_compras_gui,
        "total_gastado": total_gastado_cliente
    }