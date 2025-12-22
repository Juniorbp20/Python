# Manual de uso del sistema PyColmado

## 1. Introducción
Este manual explica cómo interactuar con PyColmado en el día a día: inicio de sesión, navegación por el panel izquierdo, gestión de ventas, inventario, clientes y proveedores, así como las opciones de configuración disponibles.

## 2. Requisitos previos
- Tener acceso al archivo `.env` con la configuración de la base de datos y credenciales habilitadas.  
- Contar con un usuario válido en la tabla de `usuarios` para poder autenticarse como `admin`, `cajero` o `almacen`.  
- Ejecutar `python app_gui.py` y asegurarse de que la ventana del login se abre correctamente.

## 3. Inicio de sesión
1. Ejecuta `python app_gui.py`.  
2. En la ventana de login completa el campo **Usuario** y **Contraseña**.  
3. Presiona “Iniciar sesión”. Si las credenciales son válidas verás la ventana principal; de lo contrario, el sistema mostrará la razón del rechazo.

## 4. Navegación y roles
- El menú lateral muestra todas las acciones disponibles según tu rol.  
- Los administradores ven todo (productos, ventas, proveedores, clientes, usuarios y configuración).  
- Cajeros y almacenistas tienen accesos limitados (nueva venta, registrar cliente, etc.).  
- Usa el botón “Salir” para cerrar la sesión y la aplicación.

## 5. Dashboard (Inicio)
- Al ingresar verás un banner con tu nombre, rol y un reloj.  
- Abajo aparecen tarjetas con métricas clave (productos activos, clientes registrados, proveedores y ventas del día).  
- Haz clic en “Ventas del día” para abrir un resumen en una ventana aparte.

## 6. Nueva Venta
1. Selecciona “Nueva Venta” desde el menú lateral.  
2. Elige un cliente del combo (o “Ninguno”).  
3. Empieza a escribir el nombre o código del producto en el campo “Producto”; el sistema mostrará un popup filtrado sin quitarte el foco.  
4. Navega con ↑/↓ si necesitas escoger otro ítem y presiona Enter o haz clic para cargarlo.  
5. Ajusta cantidad y presiona “Agregar a Venta”.  
6. Repite hasta que la lista refleje todos los productos.  
7. Ingresa el dinero recibido y confirma la venta.  

## 7. Listar y editar productos
1. “Listar Productos” abre una tabla con búsqueda rápida (barra superior).  
2. Puedes hacer doble clic en un producto (o usar el botón “Editar Producto Seleccionado”) para abrir la ventana de edición.  
3. Cambia precio, stock o categoría y guarda para actualizar la base.

## 8. Agregar producto nuevo
1. Ve a “Agregar Producto”.  
2. Completa nombre, precios, stock, proveedor y categoría.  
3. Ajusta la tasa ITBIS y el sistema calcula automáticamente el precio final.  
4. Presiona “Guardar Producto” para añadirlo al inventario.

## 9. Clientes y proveedores
- “Registrar Cliente” permite guardar nombre, teléfono y dirección.  
- “Registrar Proveedor” ofrece formulario similar y actualiza los combos para productos.  
- Los históriales muestran compras por cliente o productos por proveedor; selecciona el nombre y presiona “Ver Historial”.

## 10. Usuarios y configuración
- “Gestionar Usuarios” agrega, edita o elimina cuentas.  
- “Configuración” permite cambiar datos del negocio (nombre, RNC, logo) y el tema visual.  
- Los cambios se mantienen en la base y en `configuracion_app.json`.

## 11. Consejos y solución de problemas
- Si el popup no muestra resultados, limpia el campo y vuelve a escribir; el filtro se actualiza al instante.  
- Si el sistema no puede cargar datos (productos o clientes) aparece un `messagebox` con la razón; revisa la conexión a la base.  
- Para mantener el foco mientras escribes usa Enter o Escape si no necesitas seleccionar un producto del menú.

## 12. Referencias
- Consulta `MANUAL_TESTING.md` para el checklist de pruebas.  
- Revisa `DOCUMENTATION.md` para detalles técnicos y flujo de datos.
