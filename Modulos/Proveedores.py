import json
from .Datos import cargar_datos, ARCHIVO_PROVEEDORES, ARCHIVO_PRODUCTOS

def obtener_lista_proveedores_para_combobox():
    datos = cargar_datos(ARCHIVO_PROVEEDORES)
    proveedores = datos.get("proveedores", [])
    return [{"id": p.get("id"), "nombre": p.get("nombre")} for p in proveedores if p.get("id") and p.get("nombre")]

def obtener_historial_proveedor_gui(proveedor_id):
    datos_productos = cargar_datos(ARCHIVO_PRODUCTOS)
    productos = datos_productos.get("productos", [])
    productos_del_proveedor = [p for p in productos if p.get("proveedor_id") == proveedor_id]
    total_productos = len(productos_del_proveedor)
    total_stock = sum(p.get("stock", 0) for p in productos_del_proveedor)
    return {
        "exito": True,
        "productos": productos_del_proveedor,
        "total_productos": total_productos,
        "total_stock": total_stock
    }

def guardar_nuevo_proveedor_desde_gui(nombre, telefono, direccion):
    datos = cargar_datos(ARCHIVO_PROVEEDORES)
    proveedores = datos.get("proveedores", [])
    # Verifica duplicados
    for prov in proveedores:
        if prov.get("nombre", "").lower() == nombre.strip().lower() and prov.get("telefono", "") == telefono.strip():
            return {"exito": False, "mensaje": f"El proveedor '{nombre.strip()}' con teléfono '{telefono.strip()}' ya existe."}
    nuevo_id = max([p.get("id", 0) for p in proveedores], default=0) + 1
    nuevo_proveedor = {
        "id": nuevo_id,
        "nombre": nombre.strip(),
        "telefono": telefono.strip(),
        "direccion": direccion.strip()
    }
    proveedores.append(nuevo_proveedor)
    datos["proveedores"] = proveedores
    from Modulos.Datos import guardar_datos
    guardar_datos(datos, ARCHIVO_PROVEEDORES)
    return {"exito": True, "mensaje": f"Proveedor '{nombre.strip()}' (ID: {nuevo_id}) registrado exitosamente."}