from __future__ import annotations

# Paleta de colores
COLORS: dict[str, str] = {
    "bg":           "#07101e",
    "bg_deep":      "#050c18",
    "bg_edit":      "#050c18",
    "bg_xdeep":     "#0a0f1a",
    "bg_dark":      "#050a12",

    "border":       "#1a3050",
    "border_mid":   "#0d1c2e",
    "border_accent":"#2a5a8a",
    "border_focus": "#4a8abf",

    "text":         "#a8c8e8",
    "text_muted":   "#3a6080",
    "text_dim":     "#2a4a6a",
    "placeholder":  "#2a4a6a",

    "accent":       "#4a8abf",
    "accent_light": "#6ab0e0",
    "accent_bright":"#90d0ff",
    "accent_mid":   "#5ba0d0",
    "accent_hover": "#1a3f60",
    "accent_deep":  "#2a5a8b",

    "ok":           "#4aaa70",
    "warn":         "#c09040",
    "error":        "#c05060",

    "spinner_track":"#0f2035",
    "spinner_arc":  "#4a8abf",

    "btn_bg":       "#0f2a45",
    "btn_fg":       "#6ab0e0",
    "btn_border":   "#2a5a8a",
    "btn_hover_bg": "#1a3f60",
    "btn_hover_bd": "#4a8abf",
    "btn_hover_fg": "#90d0ff",
    "btn_pressed":  "#0a1f35",

    "btn2_fg":      "#3a5a7a",
    "btn2_border":  "#1a3050",
    "btn2_hover_bg":"#1a1a2e",
    "btn2_hover_bd":"#8a3040",
    "btn2_hover_fg":"#c06070",
    "btn2_dis_fg":  "#1a2a3a",
    "btn2_dis_bd":  "#111e2e",

    "sev_normal":   "#4aaa70",
    "sev_leve":     "#c09040",
    "sev_moderado": "#c09040",
    "sev_severo":   "#c05060",
    "sev_critico":  "#c05060",
}

SEVERITY_COLOR: dict[str, str] = {
    "normal":   COLORS["sev_normal"],
    "leve":     COLORS["sev_leve"],
    "moderado": COLORS["sev_moderado"],
    "severo":   COLORS["sev_severo"],
    "crítico":  COLORS["sev_critico"],
}

STATUS_COLOR: dict[str, str] = {
    "idle":  COLORS["text_muted"],
    "busy":  COLORS["accent"],
    "ok":    COLORS["ok"],
    "error": COLORS["error"],
}

# Tipografía
FONT_MONO = "'Courier New', monospace"


# Bloques QSS reutilizables
_SCROLLBAR_V = f"""
    QScrollBar:vertical {{
        background: {COLORS['bg']};
        width: 6px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS['border']};
        border-radius: 3px;
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
"""

_PANEL_TITLE = f"""
    QLabel#panelTitle {{
        font-family: {FONT_MONO};
        font-size: 11px;
        font-weight: bold;
        letter-spacing: 3px;
        color: {COLORS['accent']};
        padding: 4px 0;
    }}
"""

_BTN_PRIMARY = f"""
    QPushButton#btnLoad,
    QPushButton#btnApply {{
        background-color: {COLORS['btn_bg']};
        color: {COLORS['btn_fg']};
        border: 1px solid {COLORS['btn_border']};
        border-radius: 5px;
        padding: 8px 16px;
        font-family: {FONT_MONO};
        font-size: 11px;
        letter-spacing: 1px;
    }}
    QPushButton#btnLoad:hover,
    QPushButton#btnApply:hover {{
        background-color: {COLORS['btn_hover_bg']};
        border-color: {COLORS['btn_hover_bd']};
        color: {COLORS['btn_hover_fg']};
    }}
    QPushButton#btnLoad:pressed,
    QPushButton#btnApply:pressed {{
        background-color: {COLORS['btn_pressed']};
    }}
"""

_BTN_SECONDARY = f"""
    QPushButton#btnClear,
    QPushButton#btnReset {{
        background-color: transparent;
        color: {COLORS['btn2_fg']};
        border: 1px solid {COLORS['btn2_border']};
        border-radius: 5px;
        padding: 7px 16px;
        font-family: {FONT_MONO};
        font-size: 11px;
        letter-spacing: 1px;
    }}
    QPushButton#btnClear:hover,
    QPushButton#btnReset:hover {{
        background-color: {COLORS['btn2_hover_bg']};
        border-color: {COLORS['btn2_hover_bd']};
        color: {COLORS['btn2_hover_fg']};
    }}
    QPushButton#btnClear:disabled {{
        color: {COLORS['btn2_dis_fg']};
        border-color: {COLORS['btn2_dis_bd']};
    }}
"""

# Hojas de estilo por widget
QSS: dict[str, str] = {

    "image_panel": f"""
        ImagePanel {{
            background-color: {COLORS['bg']};
            border-right: 1px solid {COLORS['border']};
        }}

        QLabel#infoLabel {{
            font-family: {FONT_MONO};
            font-size: 10px;
            color: {COLORS['text_muted']};
            padding: 2px 0;
        }}

        {_PANEL_TITLE}
        {_BTN_PRIMARY}
        {_BTN_SECONDARY}
    """,

    "prompt_panel": f"""
        QLabel#promptTitle {{
            font-family: {FONT_MONO};
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 3px;
            color: {COLORS['accent']};
            padding: 2px 0;
        }}

        QLabel#hintLabel {{
            font-family: {FONT_MONO};
            font-size: 9px;
            color: {COLORS['placeholder']};
            padding: 1px 2px;
        }}

        QPlainTextEdit#promptEditor {{
            background-color: {COLORS['bg_edit']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: 10px;
            color: {COLORS['text']};
            font-family: {FONT_MONO};
            font-size: 11px;
            selection-background-color: {COLORS['accent_hover']};
        }}
        QPlainTextEdit#promptEditor:focus {{
            border-color: {COLORS['border_focus']};
        }}

        {_BTN_PRIMARY}
        {_BTN_SECONDARY}
        {_SCROLLBAR_V}
    """,

    "results_panel": f"""
        ResultsPanel {{
            background-color: {COLORS['bg']};
        }}

        QLabel#footerLabel {{
            font-family: {FONT_MONO};
            font-size: 9px;
            color: {COLORS['text_muted']};
            padding: 2px 4px;
        }}

        QTextEdit#resultsEdit {{
            background-color: {COLORS['bg_edit']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: 12px;
            color: {COLORS['text']};
            font-family: {FONT_MONO};
            font-size: 11px;
            selection-background-color: {COLORS['accent_hover']};
        }}

        QStackedWidget {{
            background-color: {COLORS['bg']};
        }}

        {_PANEL_TITLE}
        {_SCROLLBAR_V}
    """,

    "splitter": f"""
        QSplitter::handle         {{ background: {COLORS['border_mid']}; }}
        QSplitter::handle:hover   {{ background: {COLORS['accent_hover']}; }}
        QSplitter::handle:pressed {{ background: {COLORS['border_accent']}; }}
    """,

    "toolbar": f"""
        QToolBar {{
            background: {COLORS['bg_deep']};
            border-bottom: 1px solid {COLORS['border_mid']};
            spacing: 2px;
            padding: 3px 10px;
        }}
        QToolButton {{
            color: {COLORS['accent']};
            font-family: {FONT_MONO};
            font-size: 11px;
            padding: 5px 12px;
            border-radius: 4px;
            border: none;
            background: transparent;
        }}
        QToolButton:hover    {{ background: {COLORS['btn_bg']}; color: {COLORS['accent_bright']}; }}
        QToolButton:pressed  {{ background: {COLORS['bg_dark']}; }}
        QToolButton:disabled {{ color: {COLORS['border']}; }}
        QToolBar::separator  {{ width: 1px; background: {COLORS['border_mid']}; margin: 5px 8px; }}
    """,

    "statusbar": f"""
        QStatusBar {{
            background: {COLORS['bg_deep']};
            border-top: 1px solid {COLORS['border_mid']};
            font-family: {FONT_MONO};
            font-size: 10px;
            padding: 0 10px;
        }}
        QStatusBar::item {{ border: none; }}
    """,
}





def char_counter_style(over_limit: bool) -> str:
    color = COLORS["warn"] if over_limit else COLORS["text_muted"]
    return f"font-family: {FONT_MONO}; font-size: 9px; color: {color};"


def statusbar_style(level: str) -> str:
    color = STATUS_COLOR.get(level, STATUS_COLOR["idle"])
    return f"""
        QStatusBar {{
            background: {COLORS['bg_deep']};
            border-top: 1px solid {COLORS['border_mid']};
            font-family: {FONT_MONO};
            font-size: 10px;
            color: {color};
            padding: 0 10px;
        }}
        QStatusBar::item {{ border: none; }}
    """


def thread_indicator_style(active: bool) -> str:
    color = COLORS["accent"] if active else COLORS["border"]
    return f"color: {color}; font-size: 11px; padding: 0 8px;"


def inference_time_style(slow: bool) -> str:
    color = COLORS["warn"] if slow else COLORS["ok"]
    return f"font-family: {FONT_MONO}; font-size: 9px; color: {color}; padding-right: 10px;"
