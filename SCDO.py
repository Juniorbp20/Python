import os

from Modulos.Productos import listar_productos, buscar_producto, modificar_producto, eliminar_producto,alertas_stock
from Modulos.Ventas import nueva_venta, historial_ventas
from Modulos.Clientes import registrar_cliente, historial_cliente
from Modulos.Datos import guardar_datos, ARCHIVO_PRODUCTOS, ARCHIVO_VENTAS


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
    ARCHIVO_PRODUCTOS = "productos.json"
    if not os.path.exists(ARCHIVO_PRODUCTOS):
        guardar_datos({"productos": []}, ARCHIVO_PRODUCTOS) # Ensure to define guardar_datos before use
    if not os.path.exists(ARCHIVO_VENTAS):
        guardar_datos({"ventas": []}, ARCHIVO_VENTAS) # Placeholder logic

    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            from Modulos.Productos import agregar_producto
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