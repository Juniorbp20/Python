"""Operaciones de clientes respaldadas por la base de datos (vía Modulos.Repo)."""

from __future__ import annotations

from typing import List, Dict

from Modulos.Repo import (
    guardar_nuevo_cliente_desde_gui as _guardar_nuevo_cliente_desde_gui,
    obtener_lista_clientes_para_combobox as _obtener_lista_clientes_para_combobox,
    obtener_clientes_para_tabla_gui as _obtener_clientes_para_tabla_gui,
    obtener_historial_compras_cliente_gui as _obtener_historial_compras_cliente_gui,
)

guardar_nuevo_cliente_desde_gui = _guardar_nuevo_cliente_desde_gui
obtener_lista_clientes_para_combobox = _obtener_lista_clientes_para_combobox
obtener_clientes_para_tabla_gui = _obtener_clientes_para_tabla_gui
obtener_historial_compras_cliente_gui = _obtener_historial_compras_cliente_gui


def registrar_cliente():
    """CLI mínima que reutiliza el backend de base de datos."""
    print("\n--- REGISTRAR CLIENTE (Consola / DB) ---")
    nombre = input("Nombre completo: ").strip()
    telefono = input("Teléfono: ").strip()
    direccion = input("Dirección (opcional): ").strip()
    resultado = guardar_nuevo_cliente_desde_gui(nombre, telefono, direccion)
    if resultado.get("exito"):
        print(f"✅ {resultado.get('mensaje')}")
    else:
        print(f"❌ {resultado.get('mensaje')}")


def listar_clientes() -> bool:
    """Lista clientes directamente desde la tabla `clientes`."""
    clientes: List[Dict] = obtener_clientes_para_tabla_gui()
    print("\n--- CLIENTES REGISTRADOS (Consola) ---")
    if not clientes:
        print("⚠️ No hay clientes registrados.")
        return False
    for cliente in clientes:
        print(
            f"ID: {cliente.get('id')} | {cliente.get('nombre')} | "
            f"Tel: {cliente.get('telefono') or 'Sin teléfono'} | "
            f"Dirección: {cliente.get('direccion') or 'Sin registro'}"
        )
    return True


def historial_cliente():
    """Muestra historial de compras del cliente seleccionado."""
    if not listar_clientes():
        return
    try:
        cliente_id = int(input("\nID del cliente a consultar: ").strip())
    except (ValueError, TypeError):
        print("❌ ID inválido.")
        return

    resultado = obtener_historial_compras_cliente_gui(cliente_id)
    if not resultado.get("exito"):
        print(f"❌ {resultado.get('mensaje')}")
        return

    cliente_info = resultado.get("cliente_info") or {}
    historial = resultado.get("historial_compras") or []
    total = resultado.get("total_gastado", 0.0)

    print(f"\n=== HISTORIAL DE {cliente_info.get('nombre', 'Cliente').upper()} ===")
    if not historial:
        print("⚠️ No se registran compras para este cliente.")
        return
    for compra in historial:
        print(f"- Venta #{compra.get('id_venta')} | Fecha: {compra.get('fecha')} | Total: RD$ {compra.get('total_final', 0.0):.2f}")
        for detalle in compra.get("productos_detalle", []):
            print(
                f"    · {detalle.get('nombre')} x{detalle.get('cantidad')} "
                f"@ RD$ {detalle.get('precio_unitario'):.2f} = RD$ {detalle.get('subtotal'):.2f}"
            )
    print(f"\nTOTAL GASTADO: RD$ {total:.2f}")
