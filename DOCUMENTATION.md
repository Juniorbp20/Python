# Documentación del sistema PyColmado

## 1. Visión general
PyColmado es una aplicación de escritorio construida con Tkinter para gestionar inventario, ventas, clientes y proveedores en un colmado. Tiene autenticación, panel principal con dashboard, acciones rápidas desde un menú lateral y formularios para altas y consultas. El núcleo está en `app_gui.py`, que orquesta vistas, controles y llamadas a los módulos de persistencia (`Modulos.Repo`).

## 2. Arquitectura

### 2.1 Login
- `LoginDialog` crea un `Toplevel` modal que pide credenciales al usuario. Usa `_load_empresa_info` para mostrar datos del negocio y `_start_dashboard_clock` para mostrar la fecha/hora en tiempo real.
- La información de login se valida con `autenticar_usuario` y solo se abre `ColmadoApp` si retorna `exito`.

### 2.2 Interfaz principal (`ColmadoApp`)
- Se inicializa tomando configuraciones guardadas (tema, empresa) y aplica estilos vía `Modulos.ui_styles.configure_app_styles`.
- La ventana principal monta una barra lateral de acciones (`_create_actions_panel`) y un área de contenido (`display_frame`).
- Las acciones disponibles dependen del rol (`admin`, `cajero`, `almacen`) y se guardan en `_role_permissions`.

### 2.3 Acciones principales
- El dashboard (“Inicio”) muestra la bienvenida, reloj y métricas calculadas por `_collect_dashboard_metrics`.
- Cada acción (listar productos, registrar venta, clientes, proveedores, configuración) tiene su propio método que limpia la pantalla y crea los controles necesarios.
- El buscador dinámico de productos usa un popup integrado (no es un `Toplevel`) y mantiene el foco del input sin interferir mientras el usuario escribe.

## 3. Configuración y dependencias

### 3.1 Repositorios
- `Modulos.Repo` contiene los accesos a la base de datos para productos (`obtener_productos_para_gui`, `guardar_nuevo_producto`), clientes y proveedores. El método `_safe_repo_call` centraliza los `try/except` y muestra `messagebox` cuando falla una consulta, evitando bloqueos.

### 3.2 Estilos y temas
- `Modulos.ui_styles` define paletas para temas claro/oscuro y detecta el tema del sistema operativo.
- Los estilos de ttk (`Nav.TButton`, `Accent.TButton`, etc.) se aplican durante el arranque para garantizar coherencia visual.
- El popup de búsqueda hereda los colores del tema y muestra un scrollbar con etiquetas legibles.

## 4. Flujo de datos y operaciones críticas

- **Ventas:** `_cargar_datos_para_nueva_venta` carga clientes/productos, `nueva_venta_action` arma la vista y `_agregar_item_a_venta_actual` integra cantidades/stock. `_confirmar_venta_action` valida montos y llama a `procesar_nueva_venta_gui`.
- **Productos:** `listar_productos_action` muestra tabla con filtro, `_abrir_editar_producto_dialog` usa `obtener_producto_por_id` y `actualizar_producto`.
- **Clientes/Proveedores:** Hay formularios de registro (`guardar_nuevo_cliente_desde_gui`, `guardar_nuevo_proveedor_desde_gui`) y vistas de historial para consultar compras o entregas.
- **Configuración:** Permite editar datos de empresa y tema, guardando con `guardar_configuracion_app`.

## 5. Manejo de errores y resiliencia
- `_safe_repo_call` captura excepciones y deja un mensaje en pantalla sin romper el loop principal.
- `_mostrar_popup_busqueda_productos` y `.focus_set()` manejan focus sin que la lista tome control absoluto.
- `_start_dashboard_clock` y otros timers manejan errores internos con `try/except` silenciosos para no detener la UI.

## 6. Checklist de pruebas manuales
Ver `MANUAL_TESTING.md` para los pasos completos de validación: login, búsqueda, navegación de popup, scroll, ESC, y resiliencia ante fallos de datos.

## 7. Preparación para producción
- Antes de empaquetar, asegurar que `db/` está poblada y la `.env` apunta a las credenciales correctas.
- Usar `MANUAL_TESTING.md` como guía de aceptación. Si se desea, se puede crear un instalador con PyInstaller usando `PyColmadoApp.spec`.
