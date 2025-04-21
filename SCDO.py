import json
import os
from datetime import datetime
from typing import TextIO

# --------------------------
# Configuración Inicial
# --------------------------
ARCHIVO_PRODUCTOS = "productos.json"
ARCHIVO_VENTAS = "ventas.json"
ARCHIVO_CLIENTES = "clientes.json"


def cargar_datos(archivo):
    """Carga datos desde un archivo JSON. Si no existe, retorna la estructura adecuada según el archivo."""
    if os.path.exists(archivo):
        with open(archivo, "r") as f:
            return json.load(f)

    # Estructuras por defecto específicas para cada archivo
    if archivo == ARCHIVO_CLIENTES:
        return {"clientes": []}
    elif archivo == ARCHIVO_VENTAS:
        return {"ventas": []}
    else:  # ARCHIVO_PRODUCTOS
        return {"productos": []}

def guardar_datos(datos, archivo):
    """Guarda datos en un archivo JSON."""
    f: TextIO
    with open(archivo, "w") as f:
        json.dump(datos, f, indent=4)

# --------------------------
# Módulo de Productos
# --------------------------
def agregar_producto():
    """Registra uno o más productos en el archivo, con opción de asociar proveedor."""
    while True:
        print("\n--- AGREGAR PRODUCTO ---")
        nombre = input("Nombre del producto: ")
        precio = float(input("Precio unitario: "))
        stock = int(input("Stock inicial: "))
        categoria = input("Categoría (opcional): ") or "General"

        # Opción para asociar proveedor (cliente)
        proveedor_id = None
        if input("¿Asociar a un proveedor/cliente registrado? (s/n): ").lower() == 's': # ojo con lo que recibe
            listar_clientes()
            try:
                proveedor_id = int(input("ID del proveedor/cliente (0 para omitir): "))
                if proveedor_id == 0:
                    proveedor_id = None
            except ValueError:
                print("⚠️ ID inválido. Se continuará sin proveedor.")

        datos = cargar_datos(ARCHIVO_PRODUCTOS)
        nuevo_producto = {
            "id": len(datos["productos"]) + 1,
            "nombre": nombre,
            "precio": precio,
            "stock": stock,
            "categoria": categoria,
            "proveedor_id": proveedor_id  # Nuevo campo
        }

        datos["productos"].append(nuevo_producto)
        guardar_datos(datos, ARCHIVO_PRODUCTOS)

        # Mostrar info del proveedor si existe
        if proveedor_id:
            datos_clientes = cargar_datos(ARCHIVO_CLIENTES)
            proveedor = next((c for c in datos_clientes["clientes"] if c["id"] == proveedor_id), None)
            if proveedor:
                print(f"✅ Producto '{nombre}' agregado con proveedor: {proveedor['nombre']}")
            else:
                print(f"✅ Producto '{nombre}' agregado (proveedor ID {proveedor_id} no encontrado)")
        else:
            print(f"✅ Producto '{nombre}' agregado!")

        if input("¿Agregar otro producto? (s/n): ").lower() != 's':
            break


def listar_productos():
    """Muestra todos los productos en stock con información de cliente/proveedor asociado."""
    datos = cargar_datos(ARCHIVO_PRODUCTOS)
    productos = datos["productos"]
    datos_clientes = cargar_datos(ARCHIVO_CLIENTES)
    clientes = datos_clientes["clientes"]

    print("\n--- LISTA DE PRODUCTOS ---")
    for producto in productos:
        # Buscar el cliente/proveedor asociado si existe
        nombre_cliente = "N/A"
        if "proveedor_id" in producto and producto["proveedor_id"]:
            cliente = next((c for c in clientes if c["id"] == producto["proveedor_id"]), None)
            nombre_cliente = cliente["nombre"] if cliente else "Proveedor no encontrado"

        print(
            f"ID: {producto['id']} | {producto['nombre']} | ${producto['precio']:.2f} | Stock: {producto['stock']} | Proveedor: {nombre_cliente}")
# --------------------------
# Módulo de Ventas
# --------------------------
def nueva_venta():
    """Procesa una venta con opción de cliente, descuentos y validación mejorada."""
    print("\n--- NUEVA VENTA ---")

    # Cargar datos
    datos_productos = cargar_datos(ARCHIVO_PRODUCTOS)
    datos_ventas = cargar_datos(ARCHIVO_VENTAS)
    datos_clientes = cargar_datos(ARCHIVO_CLIENTES) if os.path.exists(ARCHIVO_CLIENTES) else {"clientes": []}

    # Validar productos
    if not datos_productos["productos"]:
        print("❌ No hay productos registrados.")
        return

    # Selección de cliente (opcional)
    cliente_id = None
    if input("¿Asociar a cliente registrado? (s/n): ").lower() == 's':
        listar_clientes()
        try:
            cliente_id = int(input("ID del cliente (0 para omitir): "))
            if cliente_id != 0 and not any(c["id"] == cliente_id for c in datos_clientes["clientes"]):
                print("⚠️ ID no encontrado. Continuando sin cliente.")
                cliente_id = None
        except ValueError:
            print("⚠️ Entrada inválida. Continuando sin cliente.")

    # Proceso de venta
    listar_productos()
    productos_vendidos = []
    total = 0.0

    while True:
        try:
            id_producto = int(input("\nID del producto (0 para finalizar): "))
            if id_producto == 0:
                break

            producto = next((p for p in datos_productos["productos"] if p["id"] == id_producto), None)
            if not producto:
                print("❌ Producto no encontrado.")
                continue

            cantidad = float(input(f"Cantidad de '{producto['nombre']}': "))
            if cantidad <= 0:
                print("❌ La cantidad debe ser mayor a 0.")
                continue
            if cantidad > producto["stock"]:
                print(f"❌ Stock insuficiente. Disponible: {producto['stock']}")
                continue

            # Actualizar datos
            producto["stock"] -= cantidad
            subtotal = producto["precio"] * cantidad
            total += subtotal
            productos_vendidos.append({
                "id": producto["id"],
                "nombre": producto["nombre"],
                "precio_unitario": producto["precio"],
                "cantidad": cantidad,
                "subtotal": subtotal
            })
            print(f"➕ {producto['nombre']} x{cantidad} | ${subtotal:.2f}")

        except ValueError:
            print("❌ Entrada inválida. Use números.")

    # Validar venta
    if not productos_vendidos:
        print("❌ Venta cancelada (no hay productos).")
        return

    # Aplicar descuento (opcional)
    if input("\n¿Aplicar descuento? (s/n): ").lower() == 's':
        try:
            tipo = input("Tipo (% o monto): ").lower()
            if tipo == '%':
                porcentaje = float(input("Porcentaje (ej. 10): "))
                descuento = total * (porcentaje / 100)
            else:
                descuento = float(input("Monto (ej. 5.00): "))
            total = max(0, total - descuento)
            print(f"🎫 Descuento aplicado: ${descuento:.2f}")
        except ValueError:
            print("⚠️ Descuento no válido. Ignorando.")

    # Confirmación final
    print(f"\n🛒 TOTAL A PAGAR: ${total:.2f}")
    if input("¿Confirmar venta? (s/n): ").lower() != 's':
        print("❌ Venta cancelada.")
        return

    # Guardar venta
    nueva_venta = {
        "id": len(datos_ventas["ventas"]) + 1,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": total,
        "cliente_id": cliente_id,
        "productos": productos_vendidos
    }
    datos_ventas["ventas"].append(nueva_venta)

    # Actualizar historial del cliente
    if cliente_id:
        cliente = next(c for c in datos_clientes["clientes"] if c["id"] == cliente_id)
        cliente["compras"].append(nueva_venta["id"])

    # Guardar todos los datos
    guardar_datos(datos_productos, ARCHIVO_PRODUCTOS)
    guardar_datos(datos_ventas, ARCHIVO_VENTAS)
    if cliente_id:
        guardar_datos(datos_clientes, ARCHIVO_CLIENTES)

    print(f"\n✅ Venta registrada (ID: {nueva_venta['id']})")
    if cliente_id:
        cliente = next(c for c in datos_clientes["clientes"] if c["id"] == cliente_id)
        print(f"📝 Cliente: {cliente['nombre']} (ID: {cliente_id})")

# Buscar productos nombre o categoria
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
        for producto in resultados:
            print(f"ID: {producto['id']} | {producto['nombre']} | ${producto['precio']:.2f} | Stock: {producto['stock']}")

# modificar productos
def modificar_producto():
    """Edita los detalles de un producto existente."""
    print("\n--- MODIFICAR PRODUCTO ---")
    listar_productos()
    id_producto = int(input("ID del producto a modificar: "))
    datos = cargar_datos(ARCHIVO_PRODUCTOS)

    producto = next((p for p in datos["productos"] if p["id"] == id_producto), None)
    if not producto:
        print("❌ ID no válido.")
        return

    print(f"\nEditando: {producto['nombre']} (Stock: {producto['stock']})")
    producto["nombre"] = input(f"Nuevo nombre ({producto['nombre']}): ") or producto["nombre"]
    producto["precio"] = float(input(f"Nuevo precio ({producto['precio']:.2f}): ") or producto["precio"])
    producto["stock"] = int(input(f"Nuevo stock ({producto['stock']}): ") or producto["stock"])
    producto["categoria"] = input(f"Nueva categoría ({producto['categoria']}): ") or producto["categoria"]

    guardar_datos(datos, ARCHIVO_PRODUCTOS)
    print("✅ Producto actualizado!")

#Eliminar Productos
def eliminar_producto():
    """Elimina un producto del archivo y reindexa los IDs."""
    print("\n--- ELIMINAR PRODUCTO ---")
    listar_productos()
    id_producto = int(input("ID del producto a eliminar: "))
    datos = cargar_datos(ARCHIVO_PRODUCTOS)

    producto = next((p for p in datos["productos"] if p["id"] == id_producto), None)
    if not producto:
        print("❌ ID no válido.")
        return

    confirmacion = input(f"¿Eliminar '{producto['nombre']}'? (s/n): ").lower()
    if confirmacion == 's':
        # Elimina el producto
        datos["productos"] = [p for p in datos["productos"] if p["id"] != id_producto]

    #problema resuelto con el else
    else:
        print("Producto no eliminado.")
        return

    #  Reindexa los IDs restantes
    for i, producto in enumerate(datos["productos"], start=1):
        producto["id"] = i

    guardar_datos(datos, ARCHIVO_PRODUCTOS)
    print("✅ Producto eliminado y IDs actualizados!")

#Alertas de stock
def alertas_stock():
    """Muestra productos con stock bajo."""
    umbral = int(input("\nStock mínimo para alerta (ej. 10): "))
    datos = cargar_datos(ARCHIVO_PRODUCTOS)
    productos_bajos = [p for p in datos["productos"] if p["stock"] < umbral]

    print(f"\n--- PRODUCTOS CON STOCK menor a {umbral} ---")
    if not productos_bajos:
        print("✅ Todos los productos están bien surtidos.")
    else:
        for producto in productos_bajos:
            print(f"{producto['nombre']} | Stock: {producto['stock']}")


#-----------------------------------------------------------------------------------------------------------------------
# Historial de ventas
def historial_ventas():
    """Muestra ventas filtradas por fecha y calcula totales."""
    print("\n--- HISTORIAL DE VENTAS ---")
    print("1. Ver todas las ventas")
    print("2. Filtrar por rango de fechas")
    opcion = input("Seleccione una opción (1/2): ")

    datos = cargar_datos(ARCHIVO_VENTAS)
    if not datos["ventas"]:
        print("❌ No hay ventas registradas.")
        return

    ventas_filtradas = []
    if opcion == "1":
        ventas_filtradas = datos["ventas"]
    elif opcion == "2":
        fecha_inicio = input("Fecha inicial (YYYY-MM-DD): ")
        fecha_fin = input("Fecha final (YYYY-MM-DD): ")
        for venta in datos["ventas"]:
            if fecha_inicio <= venta["fecha"][:10] <= fecha_fin:
                ventas_filtradas.append(venta)
    else:
        print("❌ Opción inválida.")
        return

    if not ventas_filtradas:
        print("❌ No hay ventas en el rango seleccionado.")
        return

    print("\n--- RESULTADOS ---")
    total_periodo = 0.0
    for venta in ventas_filtradas:
        print(f"\n📅 Fecha: {venta['fecha']} | Total: ${venta['total']:.2f}")
        print("📦 Productos:")
        for producto in venta["productos"]:
            print(f"   - {producto['nombre']} x{producto['cantidad']} (${producto['subtotal']:.2f})")
        total_periodo += venta["total"]

    print(f"\n💰 TOTAL DEL PERÍODO: ${total_periodo:.2f}")
#-----------------------------------------------------------------------------------------------------------------------
#Registrar Cliente
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

#Listar Clientes
def listar_clientes():
    """Muestra todos los clientes registrados."""
    datos = cargar_datos(ARCHIVO_CLIENTES)
    print("\n--- CLIENTES REGISTRADOS ---")
    for cliente in datos["clientes"]:
        print(f"ID: {cliente['id']} | {cliente['nombre']} | Tel: {cliente['telefono']}")

def historial_cliente():
    """Muestra las compras de un cliente específico."""
    listar_clientes()
    id_cliente = int(input("\nID del cliente a consultar: "))
    datos_clientes = cargar_datos(ARCHIVO_CLIENTES)
    datos_ventas = cargar_datos(ARCHIVO_VENTAS)

    cliente = next((c for c in datos_clientes["clientes"] if c["id"] == id_cliente), None)
    if not cliente:
        print("❌ Cliente no encontrado.")
        return

    print(f"\n📋 HISTORIAL DE {cliente['nombre'].upper()}")
    for venta_id in cliente["compras"]:
        venta = next((v for v in datos_ventas["ventas"] if v["id"] == venta_id), None)
        if venta:
            print(f"\n📅 {venta['fecha']} | Total: ${venta['total']:.2f}")
            for producto in venta["productos"]:
                print(f"   - {producto['nombre']} x{producto['cantidad']}")





# --------------------------
# Menú Principal
# --------------------------
def mostrar_menu():
    print("\n=== GESTIÓN DE COLOMADO ===")
    print("1. Agregar Producto")
    print("2. Listar Productos")
    print("3. Buscar Producto")
    print("4. Modificar Producto")
    print("5. Eliminar Producto")
    print("6. Alertas de Stock")
    print("7. Nueva Venta")
    print("8. Historial de ventas")
    print("9. Registrar Cliente")
    print("10. Historial de Cliente")
    print("0. Salir")

def main():
    # Crear archivos si no existen
    if not os.path.exists(ARCHIVO_PRODUCTOS):
        guardar_datos({"productos": []}, ARCHIVO_PRODUCTOS)
    if not os.path.exists(ARCHIVO_VENTAS):
        guardar_datos({"ventas": []}, ARCHIVO_VENTAS)

    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            agregar_producto()
        elif opcion == "2":
            listar_productos()
        elif opcion == "3":
            buscar_producto()
        elif opcion == "4":
            modificar_producto()
        elif opcion == "5":
            eliminar_producto()
        elif opcion == "6":
            alertas_stock()
        elif opcion == "7":
            nueva_venta()
        elif opcion =="8":
            historial_ventas()
        elif opcion == "9":
            registrar_cliente()
        elif opcion == "10":
            historial_cliente()
        elif opcion == "0":
            print("¡Hasta luego! 👋")
            break
        else:
            print("❌ Opción inválida. Intente de nuevo.")

if __name__ == "__main__":
    main()