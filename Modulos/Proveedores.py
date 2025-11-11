"""Interfaz de proveedores respaldada por la base de datos."""

from __future__ import annotations

from Modulos.Repo import (
    obtener_lista_proveedores_para_combobox as _obtener_lista_proveedores_para_combobox,
    obtener_proveedores_para_tabla_gui as _obtener_proveedores_para_tabla_gui,
    obtener_historial_proveedor_gui as _obtener_historial_proveedor_gui,
    guardar_nuevo_proveedor_desde_gui as _guardar_nuevo_proveedor_desde_gui,
    obtener_proveedor_por_id as _obtener_proveedor_por_id,
    actualizar_proveedor as _actualizar_proveedor,
)

obtener_lista_proveedores_para_combobox = _obtener_lista_proveedores_para_combobox
obtener_proveedores_para_tabla_gui = _obtener_proveedores_para_tabla_gui
obtener_historial_proveedor_gui = _obtener_historial_proveedor_gui
guardar_nuevo_proveedor_desde_gui = _guardar_nuevo_proveedor_desde_gui
obtener_proveedor_por_id = _obtener_proveedor_por_id
actualizar_proveedor = _actualizar_proveedor
