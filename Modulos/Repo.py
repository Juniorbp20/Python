"""
Fachada de acceso a datos para la app.
Implementa funciones equivalentes a las de los módulos JSON pero contra MariaDB
usando PyMySQL. Mantiene los mismos nombres y estructuras esperadas por la GUI.
"""

from typing import List, Dict, Optional
from Modulos.DBUtil import fetch_all, fetch_one, execute, transaction, get_connection
from Modulos.Security import hash_password, verify_password, is_hashed
from Modulos.Ventas import generar_texto_factura  # reusar


# --------------------- Productos ---------------------

def guardar_nuevo_producto(datos_producto_nuevo: Dict) -> Dict:
    sql = (
        "INSERT INTO productos (nombre, descripcion, precio_compra, precio_venta_sin_itbis, "
        "aplica_itbis, tasa_itbis, itbis_monto_producto, precio_final_venta, stock, categoria, proveedor_id) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    )
    params = (
        datos_producto_nuevo.get('nombre').strip(),
        datos_producto_nuevo.get('descripcion', '').strip(),
        float(datos_producto_nuevo.get('precio_compra', 0.0)),
        float(datos_producto_nuevo.get('precio_venta_sin_itbis', 0.0)),
        1 if datos_producto_nuevo.get('aplica_itbis') else 0,
        float(datos_producto_nuevo.get('tasa_itbis', 0.0)),
        float(datos_producto_nuevo.get('itbis_monto_producto', 0.0)),
        float(datos_producto_nuevo.get('precio_final_venta', 0.0)),
        float(datos_producto_nuevo.get('stock', 0.0)),
        (datos_producto_nuevo.get('categoria') or 'General').strip(),
        datos_producto_nuevo.get('proveedor_id'),
    )
    nuevo_id = execute(sql, params)
    return {"exito": True, "mensaje": f"Producto agregado con ID {nuevo_id}.", "producto_id": nuevo_id}


def obtener_productos_para_gui() -> List[Dict]:
    sql = (
        "SELECT p.id, p.nombre, p.descripcion, p.precio_compra, p.precio_venta_sin_itbis, "
        "p.aplica_itbis, p.tasa_itbis, p.itbis_monto_producto, p.precio_final_venta, p.stock, p.categoria, "
        "pr.nombre AS proveedor "
        "FROM productos p LEFT JOIN proveedores pr ON pr.id = p.proveedor_id ORDER BY p.nombre"
    )
    rows = fetch_all(sql)
    productos = []
    for r in rows:
        productos.append({
            'id': r['id'],
            'nombre': r['nombre'],
            'precio_compra': float(r['precio_compra']),
            'precio_venta_sin_itbis': float(r['precio_venta_sin_itbis']),
            'aplica_itbis': bool(r['aplica_itbis']),
            'tasa_itbis': float(r['tasa_itbis']),
            'itbis_monto_producto': float(r['itbis_monto_producto']),
            'precio_final_venta': float(r['precio_final_venta']),
            'precio': float(r['precio_final_venta']),  # compat GUI
            'descripcion': r.get('descripcion') or '',
            'stock': float(r['stock']),
            'categoria': r.get('categoria') or 'General',
            'proveedor': r.get('proveedor') or 'N/A',
        })
    return productos


def obtener_productos_para_venta_gui() -> List[Dict]:
    sql = (
        "SELECT id, nombre, precio_venta_sin_itbis, aplica_itbis, tasa_itbis, precio_final_venta, stock "
        "FROM productos WHERE stock > 0 ORDER BY nombre"
    )
    rows = fetch_all(sql)
    out = []
    for r in rows:
        out.append({
            'id': r['id'], 'nombre': r['nombre'], 'precio_final_venta': float(r['precio_final_venta']),
            'stock': float(r['stock']), 'aplica_itbis': bool(r['aplica_itbis']),
            'precio_venta_sin_itbis': float(r['precio_venta_sin_itbis']), 'tasa_itbis': float(r['tasa_itbis'])
        })
    return out


def obtener_categorias_existentes() -> List[str]:
    sql = "SELECT DISTINCT categoria FROM productos WHERE categoria IS NOT NULL AND categoria<>'' ORDER BY categoria"
    rows = fetch_all(sql)
    return [r['categoria'] for r in rows]


def obtener_producto_por_id(producto_id: int) -> Optional[Dict]:
    r = fetch_one(
        "SELECT p.*, pr.nombre AS proveedor_nombre FROM productos p LEFT JOIN proveedores pr ON pr.id=p.proveedor_id WHERE p.id=%s",
        (producto_id,)
    )
    return r


def actualizar_producto(producto_id: int, datos: Dict) -> Dict:
    """Actualiza un producto con los campos principales.
    Espera en datos: nombre, descripcion, precio_compra, precio_venta_sin_itbis, aplica_itbis,
    tasa_itbis, stock, categoria, proveedor_id, itbis_monto_producto, precio_final_venta
    """
    sql = (
        "UPDATE productos SET nombre=%s, descripcion=%s, precio_compra=%s, precio_venta_sin_itbis=%s, "
        "aplica_itbis=%s, tasa_itbis=%s, itbis_monto_producto=%s, precio_final_venta=%s, stock=%s, categoria=%s, proveedor_id=%s "
        "WHERE id=%s"
    )
    params = (
        datos.get('nombre').strip(),
        datos.get('descripcion', '').strip(),
        float(datos.get('precio_compra', 0.0)),
        float(datos.get('precio_venta_sin_itbis', 0.0)),
        1 if datos.get('aplica_itbis') else 0,
        float(datos.get('tasa_itbis', 0.0)),
        float(datos.get('itbis_monto_producto', 0.0)),
        float(datos.get('precio_final_venta', 0.0)),
        float(datos.get('stock', 0.0)),
        (datos.get('categoria') or 'General').strip(),
        datos.get('proveedor_id'),
        producto_id,
    )
    execute(sql, params)
    return {"exito": True, "mensaje": "Producto actualizado."}


# --------------------- Clientes ---------------------

def obtener_lista_clientes_para_combobox() -> List[Dict]:
    rows = fetch_all("SELECT id, nombre FROM clientes ORDER BY nombre")
    return [{'id': r['id'], 'nombre': r['nombre']} for r in rows]


def obtener_clientes_para_tabla_gui() -> List[Dict]:
    """Devuelve clientes con datos básicos para mostrarlos en tablas de la GUI."""
    return fetch_all("SELECT id, nombre, telefono, direccion FROM clientes ORDER BY nombre")


def guardar_nuevo_cliente_desde_gui(nombre: str, telefono: str, direccion: str) -> Dict:
    if not (nombre.strip() and telefono.strip()):
        return {"exito": False, "mensaje": "El nombre y el teléfono son obligatorios."}
    dup = fetch_one("SELECT id FROM clientes WHERE LOWER(nombre)=LOWER(%s) AND telefono=%s", (nombre.strip(), telefono.strip()))
    if dup:
        return {"exito": False, "mensaje": f"El cliente '{nombre.strip()}' con teléfono '{telefono.strip()}' ya existe."}
    new_id = execute(
        "INSERT INTO clientes (nombre, telefono, direccion) VALUES (%s,%s,%s)",
        (nombre.strip(), telefono.strip(), direccion.strip())
    )
    return {"exito": True, "mensaje": f"Cliente '{nombre.strip()}' (ID: {new_id}) registrado exitosamente."}


def obtener_historial_compras_cliente_gui(cliente_id: int) -> Dict:
    c = fetch_one("SELECT id, nombre, telefono, direccion FROM clientes WHERE id=%s", (cliente_id,))
    if not c:
        return {"exito": False, "mensaje": f"Cliente con ID {cliente_id} no encontrado."}
    ventas = fetch_all("SELECT * FROM ventas WHERE cliente_id=%s ORDER BY fecha DESC", (cliente_id,))
    historial = []
    total = 0.0
    for v in ventas:
        det = fetch_all("SELECT nombre_producto AS nombre, cantidad, precio_unitario, subtotal FROM ventas_detalle WHERE venta_id=%s", (v['id'],))
        historial.append({
            'id_venta': v['id'], 'fecha': v['fecha'].strftime('%Y-%m-%d %H:%M:%S'),
            'total_final': float(v['total_neto']), 'productos_detalle': [
                {
                    'nombre': d['nombre'], 'cantidad': float(d['cantidad']),
                    'precio_unitario': float(d['precio_unitario']), 'subtotal': float(d['subtotal'])
                } for d in det
            ]
        })
        total += float(v['total_neto'])
    return {"exito": True, "cliente_info": c, "historial_compras": historial, "total_gastado": total}


# --------------------- Proveedores ---------------------

def obtener_lista_proveedores_para_combobox() -> List[Dict]:
    rows = fetch_all("SELECT id, nombre FROM proveedores ORDER BY nombre")
    return [{'id': r['id'], 'nombre': r['nombre']} for r in rows]


def obtener_proveedores_para_tabla_gui() -> List[Dict]:
    """Devuelve proveedores con datos básicos para mostrarlos en tablas de la GUI."""
    return fetch_all("SELECT id, nombre, telefono, direccion FROM proveedores ORDER BY nombre")


def guardar_nuevo_proveedor_desde_gui(nombre: str, telefono: str, direccion: str) -> Dict:
    if not (nombre.strip() and telefono.strip()):
        return {"exito": False, "mensaje": "El nombre y el teléfono son obligatorios."}
    dup = fetch_one("SELECT id FROM proveedores WHERE LOWER(nombre)=LOWER(%s) AND telefono=%s", (nombre.strip(), telefono.strip()))
    if dup:
        return {"exito": False, "mensaje": f"El proveedor '{nombre.strip()}' con teléfono '{telefono.strip()}' ya existe."}
    new_id = execute(
        "INSERT INTO proveedores (nombre, telefono, direccion) VALUES (%s,%s,%s)",
        (nombre.strip(), telefono.strip(), direccion.strip())
    )
    return {"exito": True, "mensaje": f"Proveedor '{nombre.strip()}' (ID: {new_id}) registrado exitosamente."}


def obtener_historial_proveedor_gui(proveedor_id: int) -> Dict:
    productos = fetch_all("SELECT id, nombre, stock, precio_compra, categoria FROM productos WHERE proveedor_id=%s ORDER BY nombre", (proveedor_id,))
    total_productos = len(productos)
    total_stock = sum(float(p['stock']) for p in productos)
    return {"exito": True, "productos": productos, "total_productos": total_productos, "total_stock": total_stock}


def obtener_proveedor_por_id(proveedor_id: int) -> Optional[Dict]:
    return fetch_one("SELECT * FROM proveedores WHERE id=%s", (proveedor_id,))


def actualizar_proveedor(proveedor_id: int, nombre: str, telefono: str, direccion: str) -> Dict:
    execute("UPDATE proveedores SET nombre=%s, telefono=%s, direccion=%s WHERE id=%s", (nombre.strip(), telefono.strip(), direccion.strip(), proveedor_id))
    return {"exito": True, "mensaje": "Proveedor actualizado."}


# --------------------- Ventas ---------------------

def procesar_nueva_venta_gui(
    cliente_id_seleccionado: Optional[int],
    items_vendidos: List[Dict],
    total_bruto_sin_itbis: float,
    itbis_total_venta: float,
    descuento_aplicado: float,
    total_neto: float,
    dinero_recibido: Optional[float] = None,
    cambio_devuelto: Optional[float] = None,
) -> Dict:
    """Registra una venta con manejo de stock en transacción."""
    with transaction() as conn:
        cur = conn.cursor()
        # Validar stock
        for it in items_vendidos:
            cur.execute("SELECT stock, nombre, precio_final_venta, precio_venta_sin_itbis, aplica_itbis FROM productos WHERE id=%s FOR UPDATE", (it.get('id'),))
            row = cur.fetchone()
            if not row:
                return {'exito': False, 'mensaje': f"Producto ID {it.get('id')} no encontrado."}
            if float(it.get('cantidad', 0)) > float(row['stock']):
                return {'exito': False, 'mensaje': f"Stock insuficiente para '{row['nombre']}'."}

        # Insert cabecera
        cur.execute(
            ("INSERT INTO ventas (cliente_id, subtotal_bruto_sin_itbis, itbis_total_venta, subtotal_bruto_con_itbis, "
             "descuento_aplicado, total_neto, dinero_recibido, cambio_devuelto) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"),
            (
                cliente_id_seleccionado,
                float(total_bruto_sin_itbis), float(itbis_total_venta),
                float(total_bruto_sin_itbis + itbis_total_venta), float(descuento_aplicado), float(total_neto),
                float(dinero_recibido) if dinero_recibido is not None else None,
                float(cambio_devuelto) if cambio_devuelto is not None else None,
            )
        )
        venta_id = cur.lastrowid

        # Insert detalle + actualizar stock
        for it in items_vendidos:
            # Obtener snapshot de nombre y valores actuales por si la UI no los trae completos
            cur.execute("SELECT nombre, precio_final_venta, precio_venta_sin_itbis, aplica_itbis FROM productos WHERE id=%s", (it.get('id'),))
            p = cur.fetchone()
            nombre_prod = p['nombre'] if p else it.get('nombre', 'N/A')
            cantidad = float(it.get('cantidad', 0))
            precio_u = float(it.get('precio_unitario', p['precio_final_venta'] if p else 0.0))
            subtotal = float(it.get('subtotal', cantidad * precio_u))
            itbis_item_total = float(it.get('itbis_item_total', 0.0))

            cur.execute(
                ("INSERT INTO ventas_detalle (venta_id, producto_id, nombre_producto, cantidad, precio_unitario, subtotal, itbis_item_total) "
                 "VALUES (%s,%s,%s,%s,%s,%s,%s)"),
                (venta_id, it.get('id'), nombre_prod, cantidad, precio_u, subtotal, itbis_item_total)
            )
            cur.execute("UPDATE productos SET stock = stock - %s WHERE id=%s", (cantidad, it.get('id')))

        return {"exito": True, "mensaje": f"Venta ID: {venta_id} registrada con exito.", "venta_registrada": _venta_para_factura(conn, venta_id)}


def _venta_para_factura(conn, venta_id: int) -> Dict:
    cur = conn.cursor()
    cur.execute("SELECT * FROM ventas WHERE id=%s", (venta_id,))
    v = cur.fetchone()
    cur.execute("SELECT nombre_producto AS nombre, cantidad, precio_unitario, subtotal, itbis_item_total FROM ventas_detalle WHERE venta_id=%s", (venta_id,))
    det = cur.fetchall()
    return {
        'id': v['id'], 'fecha': v['fecha'].strftime('%Y-%m-%d %H:%M:%S'), 'cliente_id': v.get('cliente_id'),
        'productos': [
            {
                'nombre': d['nombre'], 'cantidad': float(d['cantidad']),
                'precio_unitario': float(d['precio_unitario']), 'subtotal': float(d['subtotal']),
                'itbis_item_total': float(d['itbis_item_total'])
            } for d in det
        ],
        'subtotal_bruto_sin_itbis': float(v['subtotal_bruto_sin_itbis']),
        'itbis_total_venta': float(v['itbis_total_venta']),
        'subtotal_bruto_con_itbis': float(v['subtotal_bruto_con_itbis']),
        'descuento_aplicado': float(v['descuento_aplicado']),
        'total_neto': float(v['total_neto']),
        'dinero_recibido': float(v['dinero_recibido']) if v['dinero_recibido'] is not None else None,
        'cambio_devuelto': float(v['cambio_devuelto']) if v['cambio_devuelto'] is not None else None,
    }


def obtener_venta_para_factura(venta_id: int) -> Dict:
    """Obtiene una venta completa para generar factura (con detalle)."""
    with get_connection() as conn:
        return _venta_para_factura(conn, venta_id)


def obtener_ventas_para_historial_gui(fecha_inicio_str: Optional[str] = None, fecha_fin_str: Optional[str] = None) -> Dict:
    params = []
    where = []
    if fecha_inicio_str and fecha_fin_str:
        where.append("DATE(fecha) BETWEEN %s AND %s")
        params.extend([fecha_inicio_str, fecha_fin_str])
    where_clause = (" WHERE " + " AND ".join(where)) if where else ""
    sql = (
        "SELECT v.*, COALESCE(c.nombre,'Consumidor Final') AS nombre_cliente "
        "FROM ventas v LEFT JOIN clientes c ON c.id=v.cliente_id" + where_clause + " ORDER BY v.fecha DESC"
    )
    ventas = fetch_all(sql, params)
    total_periodo = 0.0
    out = []
    for v in ventas:
        det = fetch_all("SELECT nombre_producto AS nombre, cantidad, precio_unitario, subtotal FROM ventas_detalle WHERE venta_id=%s", (v['id'],))
        out.append({
            'id_venta': v['id'], 'fecha': v['fecha'].strftime('%Y-%m-%d %H:%M:%S'), 'nombre_cliente': v['nombre_cliente'],
            'productos_detalle': [
                {
                    'nombre': d['nombre'], 'cantidad': float(d['cantidad']), 'precio_unitario': float(d['precio_unitario']), 'subtotal': float(d['subtotal'])
                } for d in det
            ],
            'subtotal_bruto_sin_itbis': float(v['subtotal_bruto_sin_itbis']),
            'itbis_total_venta': float(v['itbis_total_venta']),
            'subtotal_bruto_con_itbis': float(v['subtotal_bruto_con_itbis']),
            'descuento_aplicado': float(v['descuento_aplicado']),
            'total_final': float(v['total_neto'])
        })
        total_periodo += float(v['total_neto'])
    return {'ventas_mostradas': out, 'total_periodo': total_periodo}


# --------------------- Usuarios ---------------------

def autenticar_usuario(username: str, password: str) -> Dict:
    # Buscar por username y verificar hash. Migrar si está en texto plano.
    u = fetch_one("SELECT * FROM usuarios WHERE username=%s", (username,))
    if not u:
        return {"exito": False, "mensaje": "Usuario o contraseña incorrectos."}
    stored = u.get('password') or ''
    ok = False
    if is_hashed(stored):
        ok = verify_password(password, stored)
    else:
        # Compatibilidad: si coincide con texto plano, migrar a hash
        if password == stored:
            try:
                hpw = hash_password(password)
                execute("UPDATE usuarios SET password=%s WHERE id=%s", (hpw, u['id']))
                ok = True
            except Exception:
                ok = True  # permitir login aunque no se pudiera migrar ahora
        else:
            ok = False

    if not ok:
        return {"exito": False, "mensaje": "Usuario o contraseña incorrectos."}
    return {"exito": True, "mensaje": "Login exitoso.", "usuario": {'id': u['id'], 'username': u['username'], 'rol': u['rol']}}


def crear_usuario(username: str, password: str, rol: str = 'cajero') -> Dict:
    if rol not in ('admin', 'cajero', 'almacen'):
        return {"exito": False, "mensaje": "Rol inválido. Use 'admin', 'cajero' o 'almacen'."}
    dup = fetch_one("SELECT id FROM usuarios WHERE username=%s", (username,))
    if dup:
        return {"exito": False, "mensaje": f"El usuario '{username}' ya existe."}
    # Guardar contraseña hasheada
    new_id = execute("INSERT INTO usuarios (username, password, rol) VALUES (%s,%s,%s)", (username, hash_password(password), rol))
    return {"exito": True, "mensaje": f"Usuario '{username}' creado.", "usuario": {'id': new_id, 'username': username, 'rol': rol}}


def obtener_usuarios_para_gui() -> List[Dict]:
    rows = fetch_all("SELECT id, username, rol FROM usuarios ORDER BY id")
    return rows


def eliminar_usuario_por_id(user_id: int, usuario_actual: Optional[str] = None) -> Dict:
    # No eliminarse a sí mismo
    u = fetch_one("SELECT * FROM usuarios WHERE id=%s", (user_id,))
    if not u:
        return {"exito": False, "mensaje": f"Usuario con ID {user_id} no encontrado."}
    if usuario_actual and u.get('username') == usuario_actual:
        return {"exito": False, "mensaje": "No puede eliminar su propia cuenta mientras está conectad@."}
    if u.get('rol') == 'admin':
        total_admins = fetch_one("SELECT COUNT(*) AS c FROM usuarios WHERE rol='admin'")
        if total_admins and int(total_admins['c']) <= 1:
            return {"exito": False, "mensaje": "No se puede eliminar el último usuario administrador."}
    execute("DELETE FROM usuarios WHERE id=%s", (user_id,))
    return {"exito": True, "mensaje": f"Usuario ID {user_id} eliminado."}


def actualizar_password_usuario(user_id: int, password_actual: str, password_nuevo: str) -> Dict:
    """Actualiza la contraseña verificando la actual."""
    if not password_nuevo.strip():
        return {"exito": False, "mensaje": "La nueva contraseña no puede estar vacía."}
    user = fetch_one("SELECT id, password FROM usuarios WHERE id=%s", (user_id,))
    if not user:
        return {"exito": False, "mensaje": "Usuario no encontrado."}

    stored = user.get('password') or ''
    valid = False
    if is_hashed(stored):
        valid = verify_password(password_actual, stored)
    else:
        valid = password_actual == stored
    if not valid:
        return {"exito": False, "mensaje": "La contraseña actual no coincide."}

    hashed_new = hash_password(password_nuevo.strip())
    execute("UPDATE usuarios SET password=%s WHERE id=%s", (hashed_new, user_id))
    return {"exito": True, "mensaje": "Contraseña actualizada correctamente."}
