Base de datos MariaDB: sistemaPy

Cómo crear DB y tablas
- Requisitos: MariaDB/MySQL instalado y accesible con un usuario con permisos para crear DB.
- Comando:
  - mysql -u root -p < db/sistemaPy.sql

Qué crea
- Base de datos: sistemaPy (charset utf8mb4)
- Tablas: configuracion_app, usuarios, clientes, proveedores, productos, ventas, ventas_detalle
- Índices y claves foráneas para integridad referencial
- Usuario Admin inicial: username Admin, contraseña 1234

Notas
- Montos en DECIMAL(12,2), cantidades en DECIMAL(12,3), tasas ITBIS DECIMAL(5,4)
- En producción, almacena contraseñas con hash (campo password actual es texto plano por compatibilidad con la app)
- Para personalizar colores de botones desde la aplicación, asegúrate de tener la columna `colores_json` en `configuracion_app` (`ALTER TABLE configuracion_app ADD COLUMN colores_json TEXT NULL;` en instalaciones existentes).

