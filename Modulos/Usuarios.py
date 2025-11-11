"""Módulo de usuarios respaldado por la capa de base de datos (`Modulos.Repo`)."""

from __future__ import annotations

from Modulos.Repo import (
    autenticar_usuario as _autenticar_usuario,
    crear_usuario as _crear_usuario,
    obtener_usuarios_para_gui as _obtener_usuarios_para_gui,
    eliminar_usuario_por_id as _eliminar_usuario_por_id,
    actualizar_password_usuario as _actualizar_password_usuario,
)

autenticar_usuario = _autenticar_usuario
crear_usuario = _crear_usuario
obtener_usuarios_para_gui = _obtener_usuarios_para_gui
eliminar_usuario_por_id = _eliminar_usuario_por_id
actualizar_password_usuario = _actualizar_password_usuario
