"""Compatibilidad de módulo de productos que ahora opera sobre la base de datos.

Este archivo delega toda la lógica a :mod:`Modulos.Repo` para evitar cualquier
dependencia con archivos JSON. Se conservan las funciones públicas originales
para mantener compatibilidad con scripts o utilidades de consola.
"""

from __future__ import annotations

from typing import List, Dict

from Modulos.Repo import (
    guardar_nuevo_producto as _guardar_nuevo_producto,
    obtener_productos_para_gui as _obtener_productos_para_gui,
    obtener_productos_para_venta_gui as _obtener_productos_para_venta_gui,
    obtener_categorias_existentes as _obtener_categorias_existentes,
    obtener_producto_por_id as _obtener_producto_por_id,
    actualizar_producto as _actualizar_producto,
)

# Reexportar funciones principales para mantener la interfaz pública previa.
guardar_nuevo_producto = _guardar_nuevo_producto
obtener_productos_para_gui = _obtener_productos_para_gui
obtener_productos_para_venta_gui = _obtener_productos_para_venta_gui
obtener_categorias_existentes = _obtener_categorias_existentes
obtener_producto_por_id = _obtener_producto_por_id
actualizar_producto = _actualizar_producto


def agregar_producto():
    """Mantiene un flujo muy básico en consola para alta de productos."""
    print("\n--- AGREGAR PRODUCTO (Consola / Base de Datos) ---")
    nombre = input("Nombre: ").strip()
    if not nombre:
        print("❌ Nombre obligatorio.")
        return
    descripcion = input("Descripción: ").strip()
    categoria = input("Categoría (opcional): ").strip() or "General"
    proveedor_id = input("ID de proveedor (opcional): ").strip()
    proveedor_id_final = int(proveedor_id) if proveedor_id else None

    try:
        precio_compra = float(input("Precio compra: ") or 0.0)
        precio_sin_itbis = float(input("Precio venta sin ITBIS: ") or 0.0)
        aplica_itbis = input("¿Aplica ITBIS? (s/n): ").strip().lower() == "s"
        tasa_itbis = float(input("Tasa ITBIS (ej: 0.18): ") or 0.0) if aplica_itbis else 0.0
        stock = float(input("Stock inicial: ") or 0.0)
    except ValueError:
        print("❌ Valores numéricos inválidos.")
        return

    itbis_monto = precio_sin_itbis * tasa_itbis if aplica_itbis else 0.0
    precio_final = precio_sin_itbis + itbis_monto

    payload = {
        "nombre": nombre,
        "descripcion": descripcion,
        "categoria": categoria,
        "proveedor_id": proveedor_id_final,
        "precio_compra": precio_compra,
        "precio_venta_sin_itbis": precio_sin_itbis,
        "aplica_itbis": aplica_itbis,
        "tasa_itbis": tasa_itbis,
        "itbis_monto_producto": itbis_monto,
        "precio_final_venta": precio_final,
        "stock": stock,
    }
    resultado = guardar_nuevo_producto(payload)
    if resultado.get("exito"):
        print(f"✅ {resultado.get('mensaje')}")
    else:
        print(f"❌ {resultado.get('mensaje')}")


def listar_productos(mostrar_encabezado: bool = True) -> bool:
    """Lista productos directamente desde la base de datos."""
    productos: List[Dict] = obtener_productos_para_gui()
    if not productos:
        if mostrar_encabezado:
            print("\n--- LISTA DE PRODUCTOS (Consola) ---")
        print("⚠️ No hay productos registrados.")
        return False

    if mostrar_encabezado:
        print("\n--- LISTA DE PRODUCTOS (Consola) ---")

    for producto in productos:
        precio = producto.get("precio_final_venta", producto.get("precio", 0.0))
        print(
            f"ID: {producto.get('id')} | {producto.get('nombre')} | "
            f"Precio Final: RD$ {precio:.2f} | Stock: {producto.get('stock')} | "
            f"Categoría: {producto.get('categoria', 'N/A')} | "
            f"Proveedor: {producto.get('proveedor', 'N/A')}"
        )
    return True
