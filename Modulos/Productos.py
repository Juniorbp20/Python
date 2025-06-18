# Modulos/Productos.py

from Modulos.Datos import cargar_datos, guardar_datos, ARCHIVO_PRODUCTOS, ARCHIVO_CLIENTES
# No es ideal importar funciones de Clientes aquí si solo se usan en la versión de consola.
# Para la GUI, la lógica de obtener clientes para el combobox de proveedor está en app_gui.py.

# La función agregar_producto() original es para la consola, la dejamos como referencia
# o la adaptamos si también queremos una entrada de consola más detallada.
# Por ahora, nos enfocamos en las funciones para la GUI.

def guardar_nuevo_producto(datos_producto_nuevo):
    """
    Guarda un nuevo producto en el archivo, recibiendo un diccionario con todos los datos.
    Valida las entradas y el ID del proveedor.
    Retorna un diccionario con 'exito': True/False y 'mensaje': "..."
    """
    # Validación básica de campos obligatorios (la GUI debería hacer la mayoría)
    if not datos_producto_nuevo.get("nombre", "").strip():
        return {"exito": False, "mensaje": "El nombre del producto es obligatorio."}
    if datos_producto_nuevo.get("stock") is None: # Stock puede ser 0, pero debe estar presente
        return {"exito": False, "mensaje": "El stock del producto es obligatorio."}
    if datos_producto_nuevo.get("precio_venta_sin_itbis") is None:
        return {"exito": False, "mensaje": "El precio de venta sin ITBIS es obligatorio."}
    
    # Validar que los valores numéricos sean correctos
    try:
        # Estos ya deberían ser floats/bools si vienen de la GUI procesada, pero una verificación no daña
        stock = float(datos_producto_nuevo["stock"])
        precio_compra = float(datos_producto_nuevo.get("precio_compra", 0.0))
        precio_venta_sin_itbis = float(datos_producto_nuevo["precio_venta_sin_itbis"])
        # Los demás campos relacionados con ITBIS son calculados en la GUI, pero los recibimos
    except ValueError:
        return {"exito": False, "mensaje": "Precio de compra, venta o stock deben ser numeros validos."}

    if precio_venta_sin_itbis < 0 or precio_compra < 0 or stock < 0:
         return {"exito": False, "mensaje": "Los precios y el stock no pueden ser negativos."}


    datos_productos_existentes = cargar_datos(ARCHIVO_PRODUCTOS)
    productos = datos_productos_existentes.get("productos", [])

    # Asignar ID nuevo al producto
    if productos:
        nuevo_id = max(p.get("id", 0) for p in productos) + 1
    else:
        nuevo_id = 1

    # Construir el objeto del nuevo producto para guardar
    producto_a_guardar = {
        "id": nuevo_id,
        "nombre": datos_producto_nuevo["nombre"].strip(),
        "precio_compra": datos_producto_nuevo.get("precio_compra", 0.0),
        "precio_venta_sin_itbis": datos_producto_nuevo["precio_venta_sin_itbis"],
        "aplica_itbis": datos_producto_nuevo.get("aplica_itbis", False),
        "tasa_itbis": datos_producto_nuevo.get("tasa_itbis", 0.0),
        "itbis_monto_producto": datos_producto_nuevo.get("itbis_monto_producto", 0.0),
        "precio_final_venta": datos_producto_nuevo.get("precio_final_venta", datos_producto_nuevo["precio_venta_sin_itbis"]),
        "descripcion": datos_producto_nuevo.get("descripcion", "").strip(),
        "stock": stock,
        "categoria": datos_producto_nuevo.get("categoria", "General").strip() or "General",
        "proveedor_id": datos_producto_nuevo.get("proveedor_id")
    }
    # El campo "precio" que usaba la GUI ahora se deriva de "precio_final_venta".
    # Si tu JSON aún tiene un campo "precio" antiguo, este se ignorará al cargar y se
    # sobrescribirá con "precio_final_venta" al guardar si modificas un producto.

    productos.append(producto_a_guardar)
    datos_productos_existentes["productos"] = productos
    guardar_datos(datos_productos_existentes, ARCHIVO_PRODUCTOS)

    mensaje_exito = f"Producto '{producto_a_guardar['nombre']}' (ID: {nuevo_id}) agregado con exito."
    
    return {"exito": True, "mensaje": mensaje_exito, "producto_agregado": producto_a_guardar}


def obtener_productos_para_gui():
    """
    Carga los productos y la informacion de sus proveedores.
    Devuelve una lista de diccionarios con todos los campos necesarios para la GUI,
    asegurando que exista la clave 'precio' para compatibilidad con la GUI actual.
    """
    datos_productos = cargar_datos(ARCHIVO_PRODUCTOS)
    productos_guardados = datos_productos.get("productos", [])

    if not productos_guardados:
        return []

    datos_clientes = cargar_datos(ARCHIVO_CLIENTES)
    clientes_map = {c["id"]: c.get("nombre", "Error Nombre Prov.") for c in datos_clientes.get("clientes", [])}

    productos_para_mostrar = []
    for producto_json in productos_guardados: # Renombrado para claridad
        nombre_proveedor = "N/A"
        proveedor_id = producto_json.get("proveedor_id")
        if proveedor_id is not None:
            nombre_proveedor = clientes_map.get(proveedor_id, f"ID Proveedor: {proveedor_id} (No encontrado)")

        # Determinar el precio final de venta
        # Si el producto en JSON ya tiene 'precio_final_venta' (productos nuevos/actualizados), úsalo.
        # Si no, intenta usar 'precio_venta_sin_itbis' (para productos donde ITBIS no aplica o aún no se ha calculado precio final).
        # Como último recurso, usa el campo 'precio' antiguo si existe, o 0.0.
        precio_final = producto_json.get("precio_final_venta", 
                                       producto_json.get("precio_venta_sin_itbis", 
                                                         producto_json.get("precio", 0.0)))
        
        # Si 'precio_final_venta' no estaba en el JSON, pero 'aplica_itbis' sí, recalculamos por si acaso.
        if "precio_final_venta" not in producto_json and producto_json.get("aplica_itbis"):
            precio_base = producto_json.get("precio_venta_sin_itbis", producto_json.get("precio",0.0))
            tasa = producto_json.get("tasa_itbis", 0.0) # Debería ser 0.18 si aplica_itbis es true
            itbis_monto = precio_base * tasa
            precio_final = precio_base + itbis_monto


        producto_para_lista = {
            "id": producto_json.get("id", "N/A"),
            "nombre": producto_json.get("nombre", "Sin nombre"),
            "precio_compra": producto_json.get("precio_compra", 0.0),
            "precio_venta_sin_itbis": producto_json.get("precio_venta_sin_itbis", 0.0),
            "aplica_itbis": producto_json.get("aplica_itbis", False),
            "tasa_itbis": producto_json.get("tasa_itbis", 0.0),
            "itbis_monto_producto": producto_json.get("itbis_monto_producto", (precio_final - producto_json.get("precio_venta_sin_itbis", precio_final)) if producto_json.get("aplica_itbis") else 0.0),
            "precio_final_venta": precio_final,
            "precio": precio_final, # <--- CLAVE AÑADIDA PARA COMPATIBILIDAD CON GUI
            "descripcion": producto_json.get("descripcion", ""),
            "stock": producto_json.get("stock", 0),
            "categoria": producto_json.get("categoria", "General"),
            "proveedor": nombre_proveedor
        }
        productos_para_mostrar.append(producto_para_lista)
    return productos_para_mostrar


def obtener_productos_para_venta_gui():
    """
    Carga los productos para la GUI de venta.
    Asegura que 'precio_final_venta' y otros campos necesarios estén presentes.
    """
    productos_data_completa = obtener_productos_para_gui() # Usar la función que ya maneja la lógica de precios
    productos_disponibles_venta = []

    for p in productos_data_completa:
        if float(p.get("stock", 0)) > 0: 
            productos_disponibles_venta.append({
                "id": p.get("id"),
                "nombre": p.get("nombre"),
                "precio_final_venta": p.get("precio_final_venta"), # Ya está calculado y es el precio a usar
                "stock": float(p.get("stock", 0)),
                "aplica_itbis": p.get("aplica_itbis", False),
                "precio_venta_sin_itbis": p.get("precio_venta_sin_itbis", 0.0),
                "tasa_itbis": p.get("tasa_itbis", 0.0)
            })
    return productos_disponibles_venta


def obtener_categorias_existentes():
    """
    Carga los productos y devuelve una lista ordenada de nombres de categorias unicos.
    """
    datos_productos = cargar_datos(ARCHIVO_PRODUCTOS)
    productos = datos_productos.get("productos", [])
    if not productos:
        return []

    categorias = set() 
    for producto in productos:
        categoria_prod = producto.get("categoria")
        if categoria_prod and str(categoria_prod).strip():
            categorias.add(str(categoria_prod).strip())

    return sorted(list(categorias))


# --- Funciones de consola (mantener o eliminar si no se usan) ---
def agregar_producto():
    print("\n--- AGREGAR PRODUCTO (Consola) ---")
    print("Esta funcion de consola no esta actualizada para los nuevos campos de precio/ITBIS.")
    pass

def listar_productos(mostrar_encabezado=True):
    productos_data = obtener_productos_para_gui()

    if not productos_data:
        if mostrar_encabezado:
            print("\n--- LISTA DE PRODUCTOS (Consola) ---")
        print("ℹ️ No hay productos registrados.")
        return False

    if mostrar_encabezado:
        print("\n--- LISTA DE PRODUCTOS (Consola) ---")

    for producto in productos_data:
        print(
            f"ID: {producto.get('id')} | {producto.get('nombre')} | Precio (Final): ${producto.get('precio'):.2f} | " # Usa 'precio'
            f"Stock: {producto.get('stock')} | Categoria: {producto.get('categoria')} | Proveedor: {producto.get('proveedor')}"
        )
        if producto.get('aplica_itbis'):
            print(f"    (ITBIS Incluido: ${producto.get('itbis_monto_producto'):.2f}, Precio s/ITBIS: ${producto.get('precio_venta_sin_itbis'):.2f})")
    return True
