from Modulos.Datos import cargar_datos, guardar_datos, ARCHIVO_CLIENTES, ARCHIVO_VENTAS

def registrar_cliente():
    """Registra un nuevo cliente en el sistema."""
    print("\n--- REGISTRAR CLIENTE ---")
    nombre = input("Nombre completo: ")
    telefono = input("Teléfono: ")
    direccion = input("Dirección (opcional): ")

    datos = cargar_datos(ARCHIVO_CLIENTES)
    nuevo_cliente = {
        "id": len(datos["clientes"]) + 1,
        "nombre": nombre,
        "telefono": telefono,
        "direccion": direccion,
        "compras": []  # Historial de IDs de ventas
    }
    datos["clientes"].append(nuevo_cliente)
    guardar_datos(datos, ARCHIVO_CLIENTES)
    print(f"✅ Cliente '{nombre}' registrado (ID: {nuevo_cliente['id']})")


def listar_clientes():
    """Muestra todos los clientes registrados."""
    datos = cargar_datos(ARCHIVO_CLIENTES)
    print("\n--- CLIENTES REGISTRADOS ---")
    if not datos["clientes"]:
        print("ℹ️ No hay clientes registrados.")
        return False  # Indicar que no hay clientes para evitar errores en otras funciones
    for cliente in datos["clientes"]:
        print(f"ID: {cliente['id']} | {cliente['nombre']} | Tel: {cliente['telefono']}")
    return True  # Indicar que se listaron clientes


def historial_cliente():
    """Muestra las compras de un cliente específico."""
    if not listar_clientes():  # Primero lista y verifica si hay clientes
        return

    try:
        id_cliente = int(input("\nID del cliente a consultar: "))
    except ValueError:
        print("❌ ID inválido. Debe ser un número.")
        return

    datos_clientes = cargar_datos(ARCHIVO_CLIENTES)
    datos_ventas = cargar_datos(ARCHIVO_VENTAS)

    cliente = next((c for c in datos_clientes["clientes"] if c["id"] == id_cliente), None)
    if not cliente:
        print("❌ Cliente no encontrado.")
        return

    print(f"\n📋 HISTORIAL DE {cliente['nombre'].upper()}")
    if not cliente["compras"]:
        print("ℹ️ Este cliente no tiene compras registradas.")
        return

    for venta_id in cliente["compras"]:
        venta = next((v for v in datos_ventas["ventas"] if v["id"] == venta_id), None)
        if venta:
            print(f"\n📅 {venta['fecha']} | Total: ${venta['total']:.2f}")
            for producto in venta["productos"]:
                print(f"    - {producto['nombre']} x{producto['cantidad']}")
        else:
            print(f"⚠️ Venta con ID {venta_id} no encontrada en el historial general.")

#-----------------------------------------------------------------------------------------------------------------------

def obtener_lista_clientes_para_combobox():
    """
    Carga los clientes y devuelve una lista de diccionarios con 'id' y 'nombre',
    adecuada para un combobox.
    """
    datos_clientes = cargar_datos(ARCHIVO_CLIENTES) #
    clientes = datos_clientes.get("clientes", [])
    if not clientes:
        return []

    # Devolver solo clientes que tengan un ID y un nombre
    return [{"id": cliente["id"], "nombre": cliente["nombre"]}
            for cliente in clientes if cliente.get("id") and cliente.get("nombre")]