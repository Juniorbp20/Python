"""Backend legacy basado en JSON (deprecado).

Los datos de la aplicación ahora se almacenan exclusivamente en la base de datos.
Este módulo se mantiene únicamente para evitar import errors en scripts antiguos;
sin embargo, todas las funciones arrojan un error indicando el reemplazo.
"""

from __future__ import annotations


def _deprecated(*_args, **_kwargs):
    raise RuntimeError(
        "El backend basado en JSON fue eliminado. Utiliza Modulos.Repo para acceder "
        "a la base de datos."
    )


cargar_datos = _deprecated
guardar_datos = _deprecated
inicializar_archivos = _deprecated
