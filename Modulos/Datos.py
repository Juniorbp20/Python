import json
import os
from typing import TextIO

# --------------------------
# Configuración Inicial
# --------------------------
ARCHIVO_PRODUCTOS = "productos.json"
ARCHIVO_VENTAS = "ventas.json"
ARCHIVO_CLIENTES = "clientes.json"
ARCHIVO_PROVEEDORES = "proveedores.json"

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
    elif archivo == ARCHIVO_PROVEEDORES:
        return {"proveedores": []}
    else:  # ARCHIVO_PRODUCTOS
        return {"productos": []}

def guardar_datos(datos, archivo):
    """Guarda datos en un archivo JSON."""
    f: TextIO
    with open(archivo, "w") as f:
        json.dump(datos, f, indent=4)

def inicializar_archivos():
    """Crea los archivos de datos con estructura vacía si no existen."""
    if not os.path.exists(ARCHIVO_PRODUCTOS):
        guardar_datos({"productos": []}, ARCHIVO_PRODUCTOS)
    if not os.path.exists(ARCHIVO_VENTAS):
        guardar_datos({"ventas": []}, ARCHIVO_VENTAS)
    if not os.path.exists(ARCHIVO_CLIENTES):
        guardar_datos({"clientes": []}, ARCHIVO_CLIENTES)
    if not os.path.exists(ARCHIVO_PROVEEDORES):
        guardar_datos({"proveedores": []}, ARCHIVO_PROVEEDORES)