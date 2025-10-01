"""
Gestión básica de usuarios para la app (login y alta de usuarios).
Nota: Para simplicidad las contraseñas se guardan en texto plano. En un
entorno real se recomienda almacenar hashes con sal (p. ej., hashlib + os.urandom).
"""

from typing import Optional, Dict, List
from Modulos.Datos import cargar_datos, guardar_datos, ARCHIVO_USUARIOS


def _cargar_lista_usuarios() -> List[dict]:
    datos = cargar_datos(ARCHIVO_USUARIOS)
    return datos.get("usuarios", [])


def _guardar_lista_usuarios(usuarios: List[dict]) -> None:
    guardar_datos({"usuarios": usuarios}, ARCHIVO_USUARIOS)


def autenticar_usuario(username: str, password: str) -> Dict:
    """Valida credenciales. Retorna dict con exito, mensaje y usuario (si aplica)."""
    usuarios = _cargar_lista_usuarios()
    for u in usuarios:
        # Comparación simple (sensible a mayúsculas)
        if u.get("username") == username and u.get("password") == password:
            return {"exito": True, "mensaje": "Login exitoso.", "usuario": u}
    return {"exito": False, "mensaje": "Usuario o contraseña incorrectos."}


def crear_usuario(username: str, password: str, rol: str = "cajero") -> Dict:
    """Crea un nuevo usuario si el nombre no existe ya. Retorna dict de resultado."""
    if not username.strip() or not password:
        return {"exito": False, "mensaje": "Usuario y contraseña son obligatorios."}
    # Roles admitidos: admin (todo), cajero (ventas), almacen (stock/proveedores)
    if rol not in ("admin", "cajero", "almacen"):
        return {"exito": False, "mensaje": "Rol inválido. Use 'admin', 'cajero' o 'almacen'."}

    datos = cargar_datos(ARCHIVO_USUARIOS)
    usuarios = datos.get("usuarios", [])

    if any(u.get("username") == username for u in usuarios):
        return {"exito": False, "mensaje": f"El usuario '{username}' ya existe."}

    nuevo_id = max((u.get("id", 0) for u in usuarios), default=0) + 1
    nuevo_usuario = {
        "id": nuevo_id,
        "username": username.strip(),
        "password": password,  # Nota: guardar hash en producción
        "rol": rol
    }
    usuarios.append(nuevo_usuario)
    _guardar_lista_usuarios(usuarios)
    return {"exito": True, "mensaje": f"Usuario '{username}' creado.", "usuario": nuevo_usuario}


def obtener_usuarios_para_gui() -> List[dict]:
    """Lista básica de usuarios para mostrar en GUI (sin contraseñas)."""
    usuarios = _cargar_lista_usuarios()
    return [{"id": u.get("id"), "username": u.get("username"), "rol": u.get("rol", "usuario")} for u in usuarios]


def eliminar_usuario_por_id(user_id: int, usuario_actual: Optional[str] = None) -> Dict:
    """Elimina un usuario por ID con salvaguardas básicas.

    Reglas:
    - No permite eliminarse a sí mismo (usuario_actual == username del objetivo).
    - No permite eliminar el último administrador existente.
    """
    datos = cargar_datos(ARCHIVO_USUARIOS)
    usuarios = datos.get("usuarios", [])

    objetivo = next((u for u in usuarios if u.get("id") == user_id), None)
    if not objetivo:
        return {"exito": False, "mensaje": f"Usuario con ID {user_id} no encontrado."}

    if usuario_actual and objetivo.get("username") == usuario_actual:
        return {"exito": False, "mensaje": "No puede eliminar su propia cuenta mientras está conectad@."}

    if objetivo.get("rol") == "admin":
        total_admins = sum(1 for u in usuarios if u.get("rol") == "admin")
        if total_admins <= 1:
            return {"exito": False, "mensaje": "No se puede eliminar el último usuario administrador."}

    usuarios_filtrados = [u for u in usuarios if u.get("id") != user_id]
    _guardar_lista_usuarios(usuarios_filtrados)
    return {"exito": True, "mensaje": f"Usuario ID {user_id} eliminado."}
