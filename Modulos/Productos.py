from Modulos.Datos import cargar_datos, guardar_datos, ARCHIVO_PRODUCTOS, ARCHIVO_CLIENTES
from .Clientes import listar_clientes,registrar_cliente, historial_cliente

def agregar_producto():
    """Registra uno o más productos en el archivo, con opción de asociar proveedor."""
    while True:
        print("\n--- AGREGAR PRODUCTO ---")
        nombre = input("Nombre del producto: ")
        try:
            precio = float(input("Precio unitario: "))
            stock = int(input("Stock inicial: "))
        except ValueError:
            print("❌ Precio y stock deben ser números. Intente de nuevo.")
            continue

        categoria = input("Categoría (opcional): ") or "General"

        proveedor_id = None
        if input("¿Asociar a un proveedor/cliente registrado? (s/n): ").lower() == 's':
            if listar_clientes():  # Solo preguntar si hay clientes
                try:
                    proveedor_id_input = input("ID del proveedor/cliente (0 para omitir): ")
                    if proveedor_id_input:  # Evitar error si se deja vacío
                        proveedor_id = int(proveedor_id_input)
                        if proveedor_id == 0:
                            proveedor_id = None
                        else:  # Validar que el proveedor exista
                            datos_clientes_temp = cargar_datos(ARCHIVO_CLIENTES)
                            if not any(c["id"] == proveedor_id for c in datos_clientes_temp["clientes"]):
                                print(f"⚠️ Proveedor/Cliente con ID {proveedor_id} no encontrado. No se asociará.")
                                proveedor_id = None
                except ValueError:
                    print("⚠️ ID inválido. Se continuará sin proveedor.")
                    proveedor_id = None
            else:
                print("ℹ️ No hay proveedores/clientes registrados para asociar.")

        datos = cargar_datos(ARCHIVO_PRODUCTOS)
        nuevo_producto = {
            "id": len(datos["productos"]) + 1,
            "nombre": nombre,
            "precio": precio,
            "stock": stock,
            "categoria": categoria,
            "proveedor_id": proveedor_id
        }

        datos["productos"].append(nuevo_producto)
        guardar_datos(datos, ARCHIVO_PRODUCTOS)

        if proveedor_id:
            datos_clientes = cargar_datos(ARCHIVO_CLIENTES)
            proveedor = next((c for c in datos_clientes["clientes"] if c["id"] == proveedor_id), None)
            if proveedor:
                print(f"✅ Producto '{nombre}' agregado con proveedor: {proveedor['nombre']}")
            # La validación anterior ya cubre el caso de proveedor no encontrado
        else:
            print(f"✅ Producto '{nombre}' agregado!")

        if input("¿Agregar otro producto? (s/n): ").lower() != 's':
            break


def listar_productos(mostrar_encabezado=True):
    """Muestra todos los productos en stock con información de cliente/proveedor asociado."""
    datos_productos = cargar_datos(ARCHIVO_PRODUCTOS)
    productos = datos_productos["productos"]

    if not productos:
        if mostrar_encabezado:  # Solo mostrar si es llamado directamente y no hay productos
            print("\n--- LISTA DE PRODUCTOS ---")
        print("ℹ️ No hay productos registrados.")
        return False  # Indicar que no hay productos

    if mostrar_encabezado:
        print("\n--- LISTA DE PRODUCTOS ---")

    datos_clientes = cargar_datos(ARCHIVO_CLIENTES)
    clientes = datos_clientes["clientes"]

    for producto in productos:
        nombre_proveedor = "N/A"
        if "proveedor_id" in producto and producto["proveedor_id"]:
            proveedor = next((c for c in clientes if c["id"] == producto["proveedor_id"]), None)
            nombre_proveedor = proveedor["nombre"] if proveedor else f"ID {producto['proveedor_id']} no encontrado"

        print(
            f"ID: {producto['id']} | {producto['nombre']} | ${producto['precio']:.2f} | "
            f"Stock: {producto['stock']} | Categoría: {producto['categoria']} | Proveedor: {nombre_proveedor}"
        )
    return True  # Indicar que se listaron productos


def buscar_producto():
    """Busca productos por nombre o categoría y muestra resultados."""
    print("\n--- BUSCAR PRODUCTO ---")
    termino = input("Ingrese nombre o categoría del producto: ").lower()
    datos = cargar_datos(ARCHIVO_PRODUCTOS)
    resultados = [
        p for p in datos["productos"]
        if termino in p["nombre"].lower() or termino in p["categoria"].lower()
    ]

    if not resultados:
        print("❌ No se encontraron coincidencias.")
    else:
        print("\n--- RESULTADOS ---")
        datos_clientes = cargar_datos(ARCHIVO_CLIENTES)
        clientes = datos_clientes["clientes"]
        for producto in resultados:
            nombre_proveedor = "N/A"
            if "proveedor_id" in producto and producto["proveedor_id"]:
                proveedor = next((c for c in clientes if c["id"] == producto["proveedor_id"]), None)
                nombre_proveedor = proveedor["nombre"] if proveedor else f"ID {producto['proveedor_id']} no encontrado"
            print(
                f"ID: {producto['id']} | {producto['nombre']} | ${producto['precio']:.2f} | "
                f"Stock: {producto['stock']} | Categoría: {producto['categoria']} | Proveedor: {nombre_proveedor}"
            )


def modificar_producto():
    """Edita los detalles de un producto existente."""
    print("\n--- MODIFICAR PRODUCTO ---")
    if not listar_productos(mostrar_encabezado=False):  # No mostrar encabezado si no hay productos
        return

    try:
        id_producto = int(input("ID del producto a modificar: "))
    except ValueError:
        print("❌ ID inválido. Debe ser un número.")
        return

    datos = cargar_datos(ARCHIVO_PRODUCTOS)
    producto_encontrado = None
    for p in datos["productos"]:
        if p["id"] == id_producto:
            producto_encontrado = p
            break

    if not producto_encontrado:
        print("❌ Producto con ID no válido.")
        return

    print(f"\nEditando: {producto_encontrado['nombre']} (Stock: {producto_encontrado['stock']})")

    # Nombre
    nuevo_nombre = input(f"Nuevo nombre ({producto_encontrado['nombre']}): ")
    if nuevo_nombre:
        producto_encontrado["nombre"] = nuevo_nombre

    # Precio
    while True:
        nuevo_precio_str = input(f"Nuevo precio ({producto_encontrado['precio']:.2f}): ")
        if not nuevo_precio_str:
            break  # Mantener el precio actual si no se ingresa nada
        try:
            producto_encontrado["precio"] = float(nuevo_precio_str)
            break
        except ValueError:
            print("❌ Precio inválido. Debe ser un número.")

    # Stock
    while True:
        nuevo_stock_str = input(f"Nuevo stock ({producto_encontrado['stock']}): ")
        if not nuevo_stock_str:
            break  # Mantener el stock actual
        try:
            producto_encontrado["stock"] = int(nuevo_stock_str)
            break
        except ValueError:
            print("❌ Stock inválido. Debe ser un número entero.")

    # Categoría
    nueva_categoria = input(f"Nueva categoría ({producto_encontrado['categoria']}): ")
    if nueva_categoria:
        producto_encontrado["categoria"] = nueva_categoria

    # Proveedor
    if input(
            f"¿Modificar proveedor actual ('{producto_encontrado.get('proveedor_id', 'Ninguno')}')? (s/n): ").lower() == 's':
        if listar_clientes():  # Solo si hay clientes para elegir
            try:
                proveedor_id_input = input("ID del nuevo proveedor/cliente (0 para ninguno, Enter para no cambiar): ")
                if proveedor_id_input:  # Si el usuario ingresa algo
                    proveedor_id = int(proveedor_id_input)
                    if proveedor_id == 0:
                        producto_encontrado["proveedor_id"] = None
                    else:
                        datos_clientes_temp = cargar_datos(ARCHIVO_CLIENTES)
                        if any(c["id"] == proveedor_id for c in datos_clientes_temp["clientes"]):
                            producto_encontrado["proveedor_id"] = proveedor_id
                        else:
                            print(
                                f"⚠️ Proveedor/Cliente con ID {proveedor_id} no encontrado. No se modificó el proveedor.")
            except ValueError:
                print("⚠️ ID de proveedor inválido. No se modificó el proveedor.")
        else:
            print("ℹ️ No hay proveedores/clientes registrados para seleccionar.")

    guardar_datos(datos, ARCHIVO_PRODUCTOS)
    print("✅ Producto actualizado!")


def eliminar_producto():
    """Elimina un producto del archivo y reindexa los IDs."""
    print("\n--- ELIMINAR PRODUCTO ---")
    if not listar_productos(mostrar_encabezado=False):
        return

    try:
        id_producto = int(input("ID del producto a eliminar: "))
    except ValueError:
        print("❌ ID inválido. Debe ser un número.")
        return

    datos = cargar_datos(ARCHIVO_PRODUCTOS)
    producto_a_eliminar = next((p for p in datos["productos"] if p["id"] == id_producto), None)

    if not producto_a_eliminar:
        print("❌ Producto con ID no válido.")
        return

    confirmacion = input(f"¿Eliminar '{producto_a_eliminar['nombre']}'? (s/n): ").lower()
    if confirmacion == 's':
        datos["productos"] = [p for p in datos["productos"] if p["id"] != id_producto]

        # Reindexa los IDs restantes
        for i, producto_actualizado in enumerate(datos["productos"]):
            producto_actualizado["id"] = i + 1

        guardar_datos(datos, ARCHIVO_PRODUCTOS)
        print("✅ Producto eliminado y IDs actualizados!")
    else:
        print("ℹ️ Producto no eliminado.")


def alertas_stock():
    """Muestra productos con stock bajo."""
    try:
        umbral = int(input("\nStock mínimo para alerta (ej. 10): "))
        if umbral < 0:
            print("❌ El umbral debe ser un número positivo.")
            return
    except ValueError:
        print("❌ Entrada inválida. Debe ser un número.")
        return

    datos = cargar_datos(ARCHIVO_PRODUCTOS)
    productos_bajos = [p for p in datos["productos"] if p["stock"] < umbral]

    print(f"\n--- PRODUCTOS CON STOCK MENOR A {umbral} ---")
    if not productos_bajos:
        print("✅ Todos los productos están bien surtidos o por encima del umbral.")
    else:
        for producto in productos_bajos:
            print(f"{producto['nombre']} | Stock: {producto['stock']}")

#-----------------------------------------------------------------------------------------------------------------------

def obtener_productos_para_gui():
    """
    Carga los productos y la información de sus proveedores (clientes)
    y los devuelve en un formato adecuado para una GUI (lista de diccionarios).
    """
    datos_productos = cargar_datos(ARCHIVO_PRODUCTOS)  #
    productos = datos_productos.get("productos", [])

    if not productos:
        return []  # Devuelve lista vacía si no hay productos

    datos_clientes = cargar_datos(ARCHIVO_CLIENTES)  #
    clientes = datos_clientes.get("clientes", [])

    productos_para_mostrar = []
    for producto in productos:
        nombre_proveedor = "N/A"
        # Asegurarse que 'proveedor_id' existe y no es None antes de buscar
        if producto.get("proveedor_id") is not None:
            proveedor = next((c for c in clientes if c["id"] == producto["proveedor_id"]), None)
            if proveedor:
                nombre_proveedor = proveedor.get("nombre", "Error al obtener nombre")
            else:
                # Si hay un ID de proveedor pero no se encuentra el cliente
                nombre_proveedor = f"ID Proveedor: {producto['proveedor_id']} (No encontrado)"

        productos_para_mostrar.append({
            "id": producto.get("id", "N/A"),
            "nombre": producto.get("nombre", "Sin nombre"),
            "precio": f"{producto.get('precio', 0.0):.2f}",  # Formatear precio a 2 decimales
            "stock": producto.get("stock", 0),
            "categoria": producto.get("categoria", "General"),
            "proveedor": nombre_proveedor
        })
    return productos_para_mostrar

#-----------------------------------------------------------------------------------------------------------------------

def guardar_nuevo_producto(nombre_prod, precio_prod_str, stock_prod_str, categoria_prod, proveedor_id_str):
    """
    Guarda un nuevo producto en el archivo.
    Valida las entradas y el ID del proveedor.
    Retorna un diccionario con 'exito': True/False y 'mensaje': "..."
    """
    # Validación de precio y stock
    try:
        precio = float(precio_prod_str)
        stock = int(stock_prod_str)  # El stock se maneja como entero en el JSON original
        if precio <= 0:  # Permitimos stock 0, pero precio debe ser > 0
            return {"exito": False, "mensaje": "El precio debe ser un número positivo."}
        if stock < 0:
            return {"exito": False, "mensaje": "El stock no puede ser negativo."}
    except ValueError:
        return {"exito": False, "mensaje": "Precio y stock deben ser números válidos."}

    datos_productos = cargar_datos(ARCHIVO_PRODUCTOS)  #

    # Validación de proveedor_id si se proporciona
    proveedor_final_id = None
    if proveedor_id_str and proveedor_id_str.strip():  # Asegurarse que no es cadena vacía
        try:
            proveedor_id_int = int(proveedor_id_str)
            if proveedor_id_int != 0:  # Si es 0, se considera None o "sin proveedor"
                datos_clientes_temp = cargar_datos(ARCHIVO_CLIENTES)  #
                if any(c["id"] == proveedor_id_int for c in datos_clientes_temp.get("clientes", [])):
                    proveedor_final_id = proveedor_id_int
                else:
                    return {"exito": False, "mensaje": f"ID de Proveedor/Cliente {proveedor_id_int} no encontrado."}
            # Si proveedor_id_int es 0, proveedor_final_id permanece None (sin proveedor)
        except ValueError:
            return {"exito": False, "mensaje": "ID de proveedor inválido. Debe ser un número entero."}

    # Asignar ID nuevo al producto
    # Los IDs existentes en productos.json no son siempre secuenciales debido a eliminaciones.
    # Buscamos el ID más alto y sumamos 1, o empezamos en 1 si no hay productos.
    if datos_productos.get("productos", []):
        nuevo_id = max(p.get("id", 0) for p in datos_productos["productos"]) + 1
    else:
        nuevo_id = 1

    nuevo_producto = {
        "id": nuevo_id,
        "nombre": nombre_prod,
        "precio": precio,  # Guardar como float
        "stock": stock,  # Guardar como int
        "categoria": categoria_prod if categoria_prod and categoria_prod.strip() else "General",
        # Default a "General" si está vacío
        "proveedor_id": proveedor_final_id
    }

    datos_productos.setdefault("productos", []).append(nuevo_producto)
    guardar_datos(datos_productos, ARCHIVO_PRODUCTOS)  #

    mensaje_exito = f"Producto '{nombre_prod}' (ID: {nuevo_id}) agregado con éxito."
    # Opcional: Añadir info del proveedor al mensaje de éxito
    if proveedor_final_id:
        datos_clientes = cargar_datos(ARCHIVO_CLIENTES)
        proveedor_obj = next((c for c in datos_clientes.get("clientes", []) if c["id"] == proveedor_final_id), None)
        if proveedor_obj:
            mensaje_exito += f" Proveedor: {proveedor_obj['nombre']}"

    return {"exito": True, "mensaje": mensaje_exito}

#-----------------------------------------------------------------------------------------------------------------------

def obtener_categorias_existentes():
    """
    Carga los productos y devuelve una lista ordenada de nombres de categorías únicos.
    """
    datos_productos = cargar_datos(ARCHIVO_PRODUCTOS) #
    productos = datos_productos.get("productos", [])
    if not productos:
        return []

    categorias = set() # Usar un set para evitar duplicados automáticamente
    for producto in productos:
        # Añadir categoría solo si existe y no es solo espacios en blanco
        if producto.get("categoria") and str(producto.get("categoria")).strip():
            categorias.add(str(producto.get("categoria")).strip())

    return sorted(list(categorias))

#-----------------------------------------------------------------------------------------------------------------------

def obtener_productos_para_venta_gui():
    """
    Carga los productos y devuelve una lista de diccionarios con
    'id', 'nombre', 'precio', 'stock' para productos con stock > 0.
    """
    datos_productos = cargar_datos(ARCHIVO_PRODUCTOS) #
    productos = datos_productos.get("productos", [])
    productos_disponibles = []
    for p in productos:
        if p.get("stock", 0) > 0: # Solo listar productos que tengan stock
            productos_disponibles.append({
                "id": p["id"],
                "nombre": p["nombre"],
                "precio": p.get("precio", 0.0),
                "stock": p.get("stock", 0)
            })
    return productos_disponibles