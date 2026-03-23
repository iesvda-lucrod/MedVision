"""
chart_canvas.py
===============
Widget de entrada de prompt para la aplicación de análisis de radiografías.

Proporciona un área de texto editable donde el usuario puede introducir
instrucciones personalizadas para guiar el análisis del modelo de IA.

Dependencias:
    pip install PySide6
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# ---------------------------------------------------------------------------
# Paleta visual (coherente con image_panel / results_panel)
# ---------------------------------------------------------------------------
_COLORS: dict = {
    "bg":           "#07101e",
    "bg_edit":      "#050c18",
    "border":       "#1a3050",
    "border_focus": "#4a8abf",
    "title":        "#4a8abf",
    "text":         "#a8c8e8",
    "text_muted":   "#3a6080",
    "placeholder":  "#2a4a6a",
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
    "char_ok":      "#3a6080",
    "char_warn":    "#c09040",
}

# Prompt por defecto
_DEFAULT_PROMPT: str = (
    "Analiza esta radiografía e identifica los hallazgos más relevantes. "
    "Describe la región afectada, la severidad y cualquier recomendación clínica."
)

# Límite de caracteres recomendado
_MAX_CHARS: int = 1000


# ---------------------------------------------------------------------------
# Widget principal
# ---------------------------------------------------------------------------
class PromptPanel(QWidget):
    """
    Panel de entrada de prompt para el análisis de radiografías.

    Señales
    -------
    prompt_changed(str)
        Se emite cuando el texto del prompt cambia.
    prompt_submitted(str)
        Se emite cuando el usuario confirma el prompt (botón Aplicar).

    Uso
    ---
    panel = ChartCanvas()
    panel.prompt_submitted.connect(on_new_prompt)

    # Leer el prompt actual
    texto = panel.get_prompt()

    # Resetear al prompt por defecto
    panel.reset_prompt()
    """

    prompt_changed   = Signal(str)
    prompt_submitted = Signal(str)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        # Parámetros heredados de la firma antigua (ignorados, mantienen compatibilidad)
        width: int = 5,
        height: int = 4,
        dpi: int = 100,
    ) -> None:
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(220)
        self.setStyleSheet(f"background-color: {_COLORS['bg']}; border-radius: 6px;")

        self._build_ui()
        self._apply_styles()

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # Cabecera: etiqueta + contador de caracteres
        header = QHBoxLayout()
        header.setSpacing(0)

        lbl = QLabel("PROMPT DE ANÁLISIS")
        lbl.setObjectName("promptTitle")
        header.addWidget(lbl)

        header.addStretch()

        self._char_counter = QLabel(f"0 / {_MAX_CHARS}")
        self._char_counter.setObjectName("charCounter")
        self._char_counter.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(self._char_counter)

        root.addLayout(header)

        # Área de texto
        self._editor = QPlainTextEdit()
        self._editor.setObjectName("promptEditor")
        self._editor.setPlaceholderText("Escribe aquí las instrucciones para el modelo…")
        self._editor.setPlainText(_DEFAULT_PROMPT)
        self._editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._editor.textChanged.connect(self._on_text_changed)
        root.addWidget(self._editor, stretch=1)

        # Nota de ayuda
        hint = QLabel("El prompt guía el análisis del modelo. Sé específico para mejores resultados.")
        hint.setObjectName("hintLabel")
        hint.setWordWrap(True)
        root.addWidget(hint)

        # Botones
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._btn_apply = QPushButton("✓  Aplicar prompt")
        self._btn_apply.setObjectName("btnApply")
        self._btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_apply.clicked.connect(self._on_apply)

        self._btn_reset = QPushButton("↺  Restablecer")
        self._btn_reset.setObjectName("btnReset")
        self._btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_reset.clicked.connect(self.reset_prompt)

        btn_row.addWidget(self._btn_apply)
        btn_row.addWidget(self._btn_reset)
        root.addLayout(btn_row)

        # Inicializar contador
        self._update_counter()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            f"""
            ChartCanvas {{
                background-color: {_COLORS['bg']};
                border-radius: 6px;
            }}

            QLabel#promptTitle {{
                font-family: 'Courier New', monospace;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 3px;
                color: {_COLORS['title']};
                padding: 2px 0;
            }}

            QLabel#charCounter {{
                font-family: 'Courier New', monospace;
                font-size: 9px;
                color: {_COLORS['text_muted']};
            }}

            QLabel#hintLabel {{
                font-family: 'Courier New', monospace;
                font-size: 9px;
                color: {_COLORS['placeholder']};
                padding: 1px 2px;
            }}

            QPlainTextEdit#promptEditor {{
                background-color: {_COLORS['bg_edit']};
                border: 1px solid {_COLORS['border']};
                border-radius: 6px;
                padding: 10px;
                color: {_COLORS['text']};
                font-family: 'Courier New', monospace;
                font-size: 11px;
                selection-background-color: #1a3f60;
                line-height: 1.5;
            }}
            QPlainTextEdit#promptEditor:focus {{
                border-color: {_COLORS['border_focus']};
            }}

            QScrollBar:vertical {{
                background: {_COLORS['bg']};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {_COLORS['border']};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QPushButton#btnApply {{
                background-color: {_COLORS['btn_bg']};
                color: {_COLORS['btn_fg']};
                border: 1px solid {_COLORS['btn_border']};
                border-radius: 5px;
                padding: 7px 16px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                letter-spacing: 1px;
            }}
            QPushButton#btnApply:hover {{
                background-color: {_COLORS['btn_hover_bg']};
                border-color: {_COLORS['btn_hover_bd']};
                color: {_COLORS['btn_hover_fg']};
            }}
            QPushButton#btnApply:pressed {{
                background-color: {_COLORS['btn_pressed']};
            }}

            QPushButton#btnReset {{
                background-color: transparent;
                color: {_COLORS['btn2_fg']};
                border: 1px solid {_COLORS['btn2_border']};
                border-radius: 5px;
                padding: 7px 16px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                letter-spacing: 1px;
            }}
            QPushButton#btnReset:hover {{
                background-color: {_COLORS['btn2_hover_bg']};
                border-color: {_COLORS['btn2_hover_bd']};
                color: {_COLORS['btn2_hover_fg']};
            }}
            """
        )

    # ------------------------------------------------------------------
    # Slots internos
    # ------------------------------------------------------------------
    def _on_text_changed(self) -> None:
        self._update_counter()
        self.prompt_changed.emit(self.get_prompt())

    def _on_apply(self) -> None:
        self.prompt_submitted.emit(self.get_prompt())

    def _update_counter(self) -> None:
        n = len(self._editor.toPlainText())
        self._char_counter.setText(f"{n} / {_MAX_CHARS}")
        color = _COLORS["char_warn"] if n > _MAX_CHARS else _COLORS["char_ok"]
        self._char_counter.setStyleSheet(
            f"font-family: 'Courier New', monospace; font-size: 9px; color: {color};"
        )

    # ------------------------------------------------------------------
    # API pública  (compatible con usos anteriores de ChartCanvas)
    # ------------------------------------------------------------------
    def get_prompt(self) -> str:
        """Retorna el texto actual del prompt."""
        return self._editor.toPlainText()

    def set_prompt(self, text: str) -> None:
        """Establece el texto del prompt programáticamente."""
        self._editor.setPlainText(text)

    def reset_prompt(self) -> None:
        """Restaura el prompt al texto por defecto."""
        self._editor.setPlainText(_DEFAULT_PROMPT)

    # Métodos stub para compatibilidad con código que llamaba a ChartCanvas
    def clear(self) -> None:
        """Limpia el editor de prompt."""
        self._editor.clear()

    def set_run_enabled(self, enabled: bool) -> None:
        self._btn_apply.setEnabled(enabled)