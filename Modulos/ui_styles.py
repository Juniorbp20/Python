"""
Configuracion de paletas y estilos ttk para la aplicacion PyColmado.
Centraliza los temas de color para facilitar los cambios de apariencia.
"""
from __future__ import annotations

import platform
from tkinter import ttk, Misc
from typing import Dict

try:
    import winreg  # type: ignore
except ImportError:  # pragma: no cover
    winreg = None  # type: ignore


THEME_PALETTES: Dict[str, Dict[str, str]] = {
    "claro": {
        "bg": "#f4f6fb",
        "panel": "#ffffff",
        "panel_alt": "#f8fbff",
        "accent": "#2b8a8e",
        "accent_hover": "#237276",
        "accent_dark": "#1b585b",
        "accent_light": "#d9f2f2",
        "text": "#1f2933",
        "muted": "#5c6c7d",
        "border": "#d9e2ec",
        "nav_bg": "#e8eff9",
        "nav_border": "#d0d9e8",
        "danger": "#f25f5c",
        "danger_hover": "#d94b45",
    },
    "oscuro": {
        "bg": "#1f2430",
        "panel": "#2b303a",
        "panel_alt": "#353b47",
        "accent": "#0f7048",
        "accent_hover": "#2ab8d6",
        "accent_dark": "#1f8aa1",
        "accent_light": "#1e3a44",
        "text": "#f5f7fa",
        "muted": "#94a4b8",
        "border": "#3d4452",
        "nav_bg": "#252a34",
        "nav_border": "#3a4050",
        "danger": "#ee2f2f",
        "danger_hover": "#ee2f2f",
    },
}

THEME_LABELS = {
    "sistema": "Tema del sistema",
    "claro": "Tema claro",
    "oscuro": "Tema oscuro",
}


def _detect_system_theme() -> str:
    """Intenta detectar el tema del sistema operativo (ligero/oscuro)."""
    system = platform.system().lower()
    if system == "windows" and winreg:
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:  # type: ignore[arg-type]
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return "claro" if value == 1 else "oscuro"
        except OSError:
            pass
    return "claro"


def get_available_themes():
    """Devuelve listado de opciones de tema para poblar comboboxes."""
    return [
        {"key": "sistema", "label": THEME_LABELS.get("sistema", "Sistema")},
        {"key": "claro", "label": THEME_LABELS.get("claro", "Claro")},
        {"key": "oscuro", "label": THEME_LABELS.get("oscuro", "Oscuro")},
    ]


def get_theme_palette(theme_name: str | None) -> Dict[str, str]:
    key = (theme_name or "claro").lower()
    if key == "sistema":
        key = _detect_system_theme()
    return THEME_PALETTES.get(key, THEME_PALETTES["claro"]).copy()


def configure_app_styles(root: Misc, theme_name: str = "claro", custom_palette: dict | None = None) -> dict:
    """
    Configura el tema ttk y retorna la paleta de colores aplicada.
    Se puede pasar un diccionario custom_palette para personalizar colores.
    """
    colors = (custom_palette or get_theme_palette(theme_name)).copy()
    try:
        style = ttk.Style(root)
        base_theme = 'clam'
        if base_theme in style.theme_names():
            style.theme_use(base_theme)
        # Fuente base para widgets ttk (usar llaves para familias con espacios)
        root.option_add("*Font", "{Segoe UI} 10")
        root.configure(bg=colors["bg"])

        # Fondo base (fallback)
        style.configure('.', background=colors['panel'], foreground=colors['text'])

        # Marcos y etiquetas base
        style.configure('Background.TFrame', background=colors['bg'])
        style.configure('Content.TFrame', background=colors['panel'], relief='flat')
        style.configure('Header.TFrame', background=colors['panel'])
        style.configure('UserCard.TFrame', background=colors['panel'])
        style.configure('TFrame', background=colors['panel'])
        style.configure('TLabelframe', background=colors['panel'], bordercolor=colors['border'])
        style.configure('TLabelframe.Label', background=colors['panel'], foreground=colors['muted'])
        style.configure('Nav.TLabelframe', background=colors['nav_bg'], relief='flat', borderwidth=0)
        style.configure('Nav.TLabelframe.Label', background=colors['nav_bg'], foreground=colors['muted'], font=("Segoe UI", 11, 'bold'))
        style.configure('TLabel', background=colors['panel'], foreground=colors['text'])
        style.configure('Header.TLabel', background=colors['panel'], foreground=colors['text'], font=("Segoe UI", 16, 'bold'))
        style.configure('Subheader.TLabel', background=colors['panel'], foreground=colors['muted'], font=("Segoe UI", 11))
        style.configure('Badge.TLabel', background=colors['accent_light'], foreground=colors['accent'], font=("Segoe UI", 10, 'bold'))
        style.configure('CardTitle.TLabel', background=colors['panel'], foreground=colors['text'], font=("Segoe UI", 11, 'bold'))
        style.configure('Muted.TLabel', background=colors['panel'], foreground=colors['muted'], font=("Segoe UI", 9))
        style.configure('Welcome.TLabel', background=colors['panel'], foreground=colors['text'], font=("Segoe UI", 13, 'bold'))
        style.configure('TSeparator', background=colors['border'])
        style.configure('Nav.TSeparator', background=colors['nav_border'])
        translucent_thumb = "#6d6d77"
        translucent_thumb_dark = "#4c4c55"
        style.configure(
            'Vertical.TScrollbar',
            background=translucent_thumb,
            troughcolor=colors['panel_alt'],
            arrowcolor=colors['text'],
            bordercolor=colors['panel_alt'],
            lightcolor=translucent_thumb,
            darkcolor=translucent_thumb_dark,
            relief='flat'
        )
        style.configure(
            'Horizontal.TScrollbar',
            background=translucent_thumb,
            troughcolor=colors['panel_alt'],
            arrowcolor=colors['text'],
            bordercolor=colors['panel_alt'],
            lightcolor=translucent_thumb,
            darkcolor=translucent_thumb_dark,
            relief='flat'
        )
        style.map(
            'Vertical.TScrollbar',
            background=[('active', translucent_thumb_dark), ('pressed', translucent_thumb_dark)],
            arrowcolor=[('active', '#ffffff'), ('pressed', '#ffffff')]
        )
        style.map(
            'Horizontal.TScrollbar',
            background=[('active', translucent_thumb_dark), ('pressed', translucent_thumb_dark)],
            arrowcolor=[('active', '#ffffff'), ('pressed', '#ffffff')]
        )

        style.configure('TNotebook', background=colors['panel'], borderwidth=0)
        style.configure('TNotebook.Tab', background=colors['panel'], foreground=colors['muted'], padding=(10, 4))
        style.map(
            'TNotebook.Tab',
            background=[('selected', colors['accent_light']), ('active', colors['panel_alt'])],
            foreground=[('selected', colors['text']), ('active', colors['text'])]
        )

        # Botones
        button_base_layout = [
            ('Button.padding', {'sticky': 'nswe', 'children': [
                ('Button.label', {'sticky': 'nswe'})
            ]})
        ]
        style.configure(
            'TButton',
            padding=9,
            borderwidth=0,
            relief='flat',
            background=colors['accent'],
            foreground='#ffffff',
            focuscolor=colors['accent'],
            highlightthickness=0
        )
        style.layout('TButton', button_base_layout)
        style.map(
            'TButton',
            background=[('pressed', colors['accent_dark']), ('active', colors['accent_hover'])],
            foreground=[('pressed', '#ffffff'), ('active', '#ffffff')]
        )
        style.configure(
            'Secondary.TButton',
            padding=8,
            borderwidth=0,
            background=colors['accent_light'],
            foreground=colors['accent'],
            focuscolor=colors['accent_light'],
            highlightthickness=0
        )
        style.layout('Secondary.TButton', button_base_layout)
        style.map(
            'Secondary.TButton',
            background=[('pressed', colors['accent']), ('active', colors['accent_hover'])],
            foreground=[('pressed', '#ffffff'), ('active', '#ffffff')]
        )
        style.configure('Nav.TButton', background=colors['panel'], foreground=colors['text'], anchor='w', padding=10)
        style.layout('Nav.TButton', button_base_layout)
        style.map(
            'Nav.TButton',
            background=[('pressed', colors['accent_dark']), ('active', colors['accent'])],
            foreground=[('pressed', '#ffffff'), ('active', '#ffffff')]
        )
        style.configure('NavActive.TButton', background=colors['accent'], foreground='#ffffff', anchor='w', padding=10)
        style.layout('NavActive.TButton', button_base_layout)
        style.map(
            'NavActive.TButton',
            background=[('pressed', colors['accent_dark']), ('active', colors['accent_hover']), ('!disabled', colors['accent'])],
            foreground=[('pressed', '#ffffff'), ('active', '#ffffff'), ('!disabled', '#ffffff')]
        )
        style.configure('Accent.TButton', background=colors['accent'], foreground='#ffffff')
        style.layout('Accent.TButton', button_base_layout)
        style.map(
            'Accent.TButton',
            background=[('pressed', colors['accent_dark']), ('active', colors['accent_hover'])],
            foreground=[('pressed', '#ffffff'), ('active', '#ffffff')]
        )
        style.configure('Exit.TButton', background=colors['danger'], foreground='#ffffff')
        style.layout('Exit.TButton', button_base_layout)
        style.map(
            'Exit.TButton',
            background=[('pressed', colors['danger_hover']), ('active', colors['danger_hover'])],
            foreground=[('pressed', '#ffffff'), ('active', '#ffffff')]
        )

        # Campos de texto y combobox
        style.configure(
            'TEntry',
            fieldbackground=colors['panel'],
            foreground=colors['text'],
            padding=6,
            bordercolor=colors['border'],
            lightcolor=colors['border'],
            darkcolor=colors['border'],
            insertcolor=colors['text'],
            selectbackground=colors['accent'],
            selectforeground='#ffffff',
            relief='flat'
        )
        style.configure(
            'TCombobox',
            fieldbackground=colors['panel'],
            arrowsize=16,
            padding=4,
            foreground=colors['text'],
            background=colors['panel'],
            bordercolor=colors['border'],
            lightcolor=colors['border'],
            darkcolor=colors['border'],
            insertcolor=colors['text'],
            relief='flat'
        )
        style.map(
            'TCombobox',
            fieldbackground=[('readonly', colors['panel'])],
            background=[('readonly', colors['panel'])],
            arrowcolor=[('active', colors['accent']), ('!disabled', colors['text'])]
        )

        # Treeview
        style.configure(
            'Treeview',
            background=colors['panel'],
            fieldbackground=colors['panel'],
            bordercolor=colors['border'],
            lightcolor=colors['border'],
            darkcolor=colors['border'],
            borderwidth=1,
            relief='flat',
            highlightthickness=0,
            rowheight=26,
            font=("Segoe UI", 10),
            foreground=colors['text']
        )
        style.layout(
            'Treeview',
            [
                ('Treeview.border', {'sticky': 'nswe', 'children': [
                    ('Treeview.padding', {'sticky': 'nswe', 'children': [
                        ('Treeview.treearea', {'sticky': 'nswe'})
                    ]})
                ]})
            ]
        )
        style.map(
            'Treeview',
            background=[('selected', colors['accent'])],
            foreground=[('selected', '#ffffff')]
        )
        style.configure(
            'Treeview.Heading',
            background=colors['panel_alt'],
            foreground=colors['text'],
            font=("Segoe UI", 10, 'bold'),
            relief='flat',
            borderwidth=0
        )
        style.map(
            'Treeview.Heading',
            background=[('active', colors['nav_bg'])],
            foreground=[('active', colors['text'])]
        )

        # Separadores y otros widgets
        style.configure('Nav.TSeparator', background=colors['nav_border'])
    except Exception as exc:
        print(f"Advertencia: No se pudieron configurar estilos ttk: {exc}")
    return colors
