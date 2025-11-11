"""Operaciones de ventas respaldadas por la base de datos."""

from __future__ import annotations

from typing import Dict, List, Optional

from Modulos.Repo import (
    procesar_nueva_venta_gui as _procesar_nueva_venta_gui,
    obtener_ventas_para_historial_gui as _obtener_ventas_para_historial_gui,
    obtener_venta_para_factura as _obtener_venta_para_factura,
    obtener_productos_para_gui,
    obtener_lista_clientes_para_combobox,
)

procesar_nueva_venta_gui = _procesar_nueva_venta_gui
obtener_ventas_para_historial_gui = _obtener_ventas_para_historial_gui
obtener_venta_para_factura = _obtener_venta_para_factura


def nueva_venta():
    """Interfaz de consola simple que opera directamente contra la DB."""
    productos = obtener_productos_para_gui()
    if not productos:
        print("⚠️ No hay productos con stock disponible.")
        return

    productos_por_id = {p["id"]: p for p in productos}
    stock_restante = {p["id"]: float(p.get("stock", 0.0) or 0.0) for p in productos}

    print("\n--- NUEVA VENTA (Consola / DB) ---")
    for p in productos:
        print(
            f"ID: {p['id']} | {p['nombre']} | Stock: {p.get('stock')} | "
            f"Precio final: RD$ {p.get('precio_final_venta', 0.0):.2f}"
        )

    clientes = obtener_lista_clientes_para_combobox()
    cliente_id: Optional[int] = None
    if clientes:
        resp = input("\n¿Asociar cliente registrado? (s/n): ").strip().lower()
        if resp == "s":
            print("Clientes disponibles:")
            for c in clientes:
                print(f" - {c['id']}: {c['nombre']}")
            entrada = input("ID de cliente (vacío para consumidor final): ").strip()
            if entrada:
                try:
                    cliente_id = int(entrada)
                except ValueError:
                    print("⚠️ ID de cliente inválido. Continuando sin asociación.")
                    cliente_id = None

    items: List[Dict] = []
    while True:
        try:
            id_str = input("\nID producto (0 para finalizar): ").strip()
            if not id_str:
                continue
            prod_id = int(id_str)
        except ValueError:
            print("⚠️ Debe ingresar un ID numérico.")
            continue

        if prod_id == 0:
            break
        producto = productos_por_id.get(prod_id)
        if not producto:
            print("❌ Producto no encontrado.")
            continue

        try:
            cantidad = float(input(f"Cantidad para '{producto['nombre']}': ").strip())
        except ValueError:
            print("⚠️ Cantidad inválida.")
            continue

        if cantidad <= 0:
            print("⚠️ La cantidad debe ser mayor que cero.")
            continue

        if stock_restante[prod_id] != 0 and cantidad > stock_restante[prod_id]:
            print(f"⚠️ Stock insuficiente. Disponible: {stock_restante[prod_id]:.2f}")
            continue

        precio_final = float(producto.get("precio_final_venta", producto.get("precio", 0.0)))
        precio_sin_itbis = float(producto.get("precio_venta_sin_itbis", precio_final))
        itbis_unitario = max(precio_final - precio_sin_itbis, 0.0)

        items.append(
            {
                "id": prod_id,
                "nombre": producto.get("nombre"),
                "cantidad": cantidad,
                "precio_unitario": precio_final,
                "subtotal": cantidad * precio_final,
                "itbis_item_total": cantidad * itbis_unitario,
            }
        )
        stock_restante[prod_id] = max(stock_restante[prod_id] - cantidad, 0.0)
        print(f"✅ Añadido {cantidad} x '{producto['nombre']}' (RD$ {precio_final:.2f} c/u)")

    if not items:
        print("⚠️ Venta cancelada. No se agregaron productos.")
        return

    descuento = 0.0
    resp_desc = input("\n¿Aplicar descuento? (s/n): ").strip().lower()
    if resp_desc == "s":
        try:
            descuento = float(input("Monto de descuento (RD$): ").strip() or "0")
        except ValueError:
            descuento = 0.0
            print("⚠️ Descuento inválido. Se ignora.")

    total_con_itbis = sum(item["subtotal"] for item in items)
    itbis_total = sum(item["itbis_item_total"] for item in items)
    subtotal_sin_itbis = total_con_itbis - itbis_total
    total_neto = max(total_con_itbis - descuento, 0.0)

    try:
        dinero_recibido = float(input(f"Dinero recibido (>= RD$ {total_neto:.2f}): ").strip())
    except ValueError:
        print("❌ Monto inválido.")
        return
    if dinero_recibido < total_neto:
        print("❌ Dinero insuficiente. Venta cancelada.")
        return

    cambio = dinero_recibido - total_neto
    resultado = procesar_nueva_venta_gui(
        cliente_id_seleccionado=cliente_id,
        items_vendidos=items,
        total_bruto_sin_itbis=subtotal_sin_itbis,
        itbis_total_venta=itbis_total,
        descuento_aplicado=descuento,
        total_neto=total_neto,
        dinero_recibido=dinero_recibido,
        cambio_devuelto=cambio,
    )
    if resultado.get("exito"):
        print(f"\n✅ {resultado.get('mensaje')}")
        venta = resultado.get("venta_registrada")
        if venta:
            print(f"Venta #{venta.get('id')} registrada. Total: RD$ {venta.get('total_neto', 0.0):.2f} | Cambio: RD$ {cambio:.2f}")
    else:
        print(f"❌ {resultado.get('mensaje')}")
