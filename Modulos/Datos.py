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
ARCHIVO_USUARIOS = "usuarios.json"  # Nuevo archivo para credenciales de usuarios

def cargar_datos(archivo):
    """Carga datos desde un archivo JSON (UTF-8).
    Si no existe, retorna la estructura adecuada según el archivo.
    """
    if os.path.exists(archivo):
        # Abrir siempre en UTF-8 para consistencia cross-platform
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)

    # Estructuras por defecto específicas para cada archivo
    if archivo == ARCHIVO_CLIENTES:
        return {"clientes": []}
    elif archivo == ARCHIVO_VENTAS:
        return {"ventas": []}
    elif archivo == ARCHIVO_PROVEEDORES:
        return {"proveedores": []}
    elif archivo == ARCHIVO_USUARIOS:
        # Estructura por defecto sin usuarios; se inicializa admin en inicializar_archivos()
        return {"usuarios": []}
    else:  # ARCHIVO_PRODUCTOS
        return {"productos": []}

def guardar_datos(datos, archivo):
    """Guarda datos en un archivo JSON (UTF-8) de forma segura.

    - Usa escritura atómica básica (archivo temporal + os.replace) para evitar
      corrupciones si el proceso se interrumpe a mitad de escritura.
    - Asegura UTF-8 y caracteres legibles (ensure_ascii=False).
    """
    # Escribir a un archivo temporal en el mismo directorio para que os.replace sea atómico
    tmp_path = f"{archivo}.tmp"
    f: TextIO
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())  # Garantizar que los datos se escriban al disco
    os.replace(tmp_path, archivo)

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
    # Crear usuarios.json con usuario Admin por defecto (Admin/1234) si no existe
    if not os.path.exists(ARCHIVO_USUARIOS):
        guardar_datos({
            "usuarios": [
                {
                    "id": 1,
                    "username": "Admin",
                    # Nota: Por simplicidad se guarda en texto plano. En producción usa hashing (p.ej., SHA-256 + sal).
                    "password": "1234",
                    "rol": "admin"
                }
            ]
        }, ARCHIVO_USUARIOS)
