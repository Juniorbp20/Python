-- Esquema MariaDB para PyColmado
-- Crea la base de datos y todas las tablas necesarias
-- Ejecutar con: mysql -u root -p < db/sistemaPy.sql

DROP DATABASE IF EXISTS `sistemaPy`;
CREATE DATABASE `sistemaPy` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `sistemaPy`;

-- Tabla de usuarios del sistema
CREATE TABLE `usuarios` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(64) NOT NULL,
  `password` VARCHAR(255) NOT NULL, -- Nota: en producción usar hash con sal
  `rol` ENUM('admin','cajero','almacen') NOT NULL DEFAULT 'cajero',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_usuarios_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Semilla: usuario Admin (contraseña: 1234)
INSERT INTO `usuarios`(`username`,`password`,`rol`) VALUES ('Admin','1234','admin');

-- Tabla de clientes
CREATE TABLE `clientes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(128) NOT NULL,
  `telefono` VARCHAR(32) NULL,
  `direccion` VARCHAR(255) NULL,
  PRIMARY KEY (`id`),
  KEY `ix_clientes_nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla de proveedores
CREATE TABLE `proveedores` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(128) NOT NULL,
  `telefono` VARCHAR(32) NULL,
  `direccion` VARCHAR(255) NULL,
  PRIMARY KEY (`id`),
  KEY `ix_proveedores_nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla de productos
CREATE TABLE `productos` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(160) NOT NULL,
  `descripcion` VARCHAR(512) NULL,
  `precio_compra` DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  `precio_venta_sin_itbis` DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  `aplica_itbis` TINYINT(1) NOT NULL DEFAULT 0,
  `tasa_itbis` DECIMAL(5,4) NOT NULL DEFAULT 0.0000,
  `itbis_monto_producto` DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  `precio_final_venta` DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  `stock` DECIMAL(12,3) NOT NULL DEFAULT 0.000,
  `categoria` VARCHAR(128) NULL,
  `proveedor_id` INT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_productos_nombre` (`nombre`),
  KEY `ix_productos_proveedor` (`proveedor_id`),
  CONSTRAINT `fk_productos_proveedor` FOREIGN KEY (`proveedor_id`) REFERENCES `proveedores` (`id`) ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla de ventas (cabecera)
CREATE TABLE `ventas` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `fecha` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `cliente_id` INT NULL,
  `subtotal_bruto_sin_itbis` DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  `itbis_total_venta` DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  `subtotal_bruto_con_itbis` DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  `descuento_aplicado` DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  `total_neto` DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  `dinero_recibido` DECIMAL(12,2) NULL,
  `cambio_devuelto` DECIMAL(12,2) NULL,
  PRIMARY KEY (`id`),
  KEY `ix_ventas_fecha` (`fecha`),
  KEY `ix_ventas_cliente` (`cliente_id`),
  CONSTRAINT `fk_ventas_cliente` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`) ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla de detalle de ventas
CREATE TABLE `ventas_detalle` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `venta_id` INT NOT NULL,
  `producto_id` INT NULL, -- puede quedar NULL si el producto fue eliminado
  `nombre_producto` VARCHAR(160) NOT NULL, -- snapshot
  `cantidad` DECIMAL(12,3) NOT NULL DEFAULT 0.000,
  `precio_unitario` DECIMAL(12,2) NOT NULL DEFAULT 0.00, -- final con ITBIS
  `subtotal` DECIMAL(12,2) NOT NULL DEFAULT 0.00,        -- final con ITBIS
  `itbis_item_total` DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`id`),
  KEY `ix_vd_venta` (`venta_id`),
  KEY `ix_vd_producto` (`producto_id`),
  CONSTRAINT `fk_vd_venta` FOREIGN KEY (`venta_id`) REFERENCES `ventas` (`id`) ON UPDATE RESTRICT ON DELETE CASCADE,
  CONSTRAINT `fk_vd_producto` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Índices útiles adicionales
CREATE INDEX `ix_productos_categoria` ON `productos` (`categoria`);

-- Vistas opcionales (descomentarlas si las quieres)
-- CREATE VIEW vw_listado_productos AS
--   SELECT p.*, pr.nombre AS proveedor
--   FROM productos p LEFT JOIN proveedores pr ON pr.id = p.proveedor_id;

