"""
results_panel.py
================
Panel derecho de la ventana principal.
Muestra un spinner mientras el modelo analiza y formatea
los hallazgos con secciones claras en un QTextEdit.

Dependencias:
    pip install PySide6
"""

from __future__ import annotations

import math
from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen,QTextCharFormat, QTextCursor, QTextDocument
from PySide6.QtWidgets import QLabel, QSizePolicy, QStackedWidget, QTextEdit, QVBoxLayout, QWidget

# Paleta de colores del panel
_COLORS = {
    "bg":           "#07101e",
    "bg_edit":      "#050c18",
    "border":       "#1a3050",
    "title":        "#4a8abf",
    "section_head": "#5ba0d0",
    "normal":       "#a8c8e8",
    "muted":        "#3a6080",
    "accent_ok":    "#4aaa70",
    "accent_warn":  "#c09040",
    "accent_err":   "#c05060",
    "spinner_arc":  "#4a8abf",
    "spinner_bg":   "#0f2035",
}

# Mapeo de severidad → color hex
_SEVERITY_COLOR: dict[str, str] = {
    "normal":    _COLORS["accent_ok"],
    "leve":      _COLORS["accent_warn"],
    "moderado":  _COLORS["accent_warn"],
    "severo":    _COLORS["accent_err"],
    "crítico":   _COLORS["accent_err"],
}

# Secciones esperadas en el dict de resultado (orden de renderizado)
_SECTION_ORDER: list[str] = [
    "paciente",
    "hallazgos",
    "impresion",
    "recomendaciones",
    "nota",
]

_SECTION_LABELS: dict[str, str] = {
    "paciente":        "DATOS DEL PACIENTE",
    "hallazgos":       "HALLAZGOS RADIOLÓGICOS",
    "impresion":       "IMPRESIÓN DIAGNÓSTICA",
    "recomendaciones": "RECOMENDACIONES",
    "nota":            "NOTA DEL SISTEMA",
}


# Widget del spinner
class _SpinnerWidget(QWidget):

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedSize(72, 72)
        self._angle: float = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    # Control
    def start(self) -> None:
        self._angle = 0.0
        self._timer.start(16)          # ~60 fps

    def stop(self) -> None:
        self._timer.stop()
        self.update()

    # Eventos
    def _tick(self) -> None:
        self._angle = (self._angle + 4.0) % 360.0
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy, r = self.width() / 2, self.height() / 2, 28

        # Pista de fondo
        bg_pen = QPen(QColor(_COLORS["spinner_bg"]), 6)
        bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawEllipse(
            int(cx - r), int(cy - r), int(r * 2), int(r * 2)
        )

        # Arco animado
        arc_pen = QPen(QColor(_COLORS["spinner_arc"]), 6)
        arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(arc_pen)

        start_angle = int((90 - self._angle) * 16)
        span_angle  = int(-260 * 16)
        painter.drawArc(
            int(cx - r), int(cy - r), int(r * 2), int(r * 2),
            start_angle, span_angle,
        )

        # Punto interior pulsante
        pulse = 0.5 + 0.5 * math.sin(math.radians(self._angle * 3))
        dot_r = 4 + int(pulse * 2)
        dot_color = QColor(_COLORS["spinner_arc"])
        dot_color.setAlphaF(0.6 + 0.4 * pulse)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(dot_color)
        painter.drawEllipse(
            int(cx - dot_r), int(cy - dot_r), dot_r * 2, dot_r * 2
        )

        painter.end()


# Página de carga (spinner + mensaje)
class _LoadingPage(QWidget):
    """Página del QStackedWidget visible mientras el modelo analiza."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        self._spinner = _SpinnerWidget()

        self._label = QLabel("Analizando radiografía…")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(
            f"""
            QLabel {{
                font-family: 'Courier New', monospace;
                font-size: 12px;
                letter-spacing: 2px;
                color: {_COLORS['muted']};
            }}
            """
        )

        # Centrar el spinner horizontalmente
        from PySide6.QtWidgets import QHBoxLayout
        spinner_row = QHBoxLayout()
        spinner_row.addStretch()
        spinner_row.addWidget(self._spinner)
        spinner_row.addStretch()

        layout.addLayout(spinner_row)
        layout.addWidget(self._label)

    def start(self) -> None:
        self._spinner.start()

    def stop(self) -> None:
        self._spinner.stop()

    def set_message(self, text: str) -> None:
        self._label.setText(text)


# Página vacía / placeholder
class _PlaceholderPage(QWidget):
    """Página visible cuando aún no hay resultado ni análisis en curso."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        msg = QLabel("Los hallazgos del modelo\naparecerán aquí.")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet(
            f"""
            QLabel {{
                font-family: 'Courier New', monospace;
                font-size: 11px;
                letter-spacing: 1px;
                color: {_COLORS['muted']};
                line-height: 1.8;
            }}
            """
        )
        layout.addWidget(msg)


# Panel principal
class ResultsPanel(QWidget):
    """
    Panel derecho de la aplicación de análisis de radiografías.

    Señales
    -------
    (ninguna pública; el panel es receptor, no emisor)

    Uso
    ---
    panel = ResultsPanel()
    panel.show_loading(True)           # mientras el modelo trabaja
    panel.display_result(result_dict)  # al recibir la respuesta
    if panel.has_result():
        data = panel.current_result()  # para el generador de informes
    """

    # Índices de páginas en el QStackedWidget
    _PAGE_PLACEHOLDER = 0
    _PAGE_LOADING     = 1
    _PAGE_RESULTS     = 2

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._result: Optional[dict] = None

        self._build_ui()
        self._apply_styles()

    # Construcción de la UI
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # Título
        title = QLabel("ANÁLISIS DE IA")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("panelTitle")
        root.addWidget(title)

        # Stack de páginas
        self._stack = QStackedWidget()
        self._stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self._placeholder_page = _PlaceholderPage()
        self._loading_page     = _LoadingPage()
        self._results_page     = self._build_results_page()

        self._stack.addWidget(self._placeholder_page)    # 0
        self._stack.addWidget(self._loading_page)        # 1
        self._stack.addWidget(self._results_page)        # 2

        self._stack.setCurrentIndex(self._PAGE_PLACEHOLDER)
        root.addWidget(self._stack, stretch=1)

        # Pie: modelo + confianza (se rellena en display_result)
        self._footer = QLabel("")
        self._footer.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._footer.setObjectName("footerLabel")
        root.addWidget(self._footer)

    def _build_results_page(self) -> QWidget:
        """Crea el QTextEdit donde se renderiza el resultado."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setObjectName("resultsEdit")
        self._text_edit.setFrameShape(QTextEdit.Shape.NoFrame)
        layout.addWidget(self._text_edit)
        return page

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            f"""
            ResultsPanel {{
                background-color: {_COLORS['bg']};
            }}

            QLabel#panelTitle {{
                font-family: 'Courier New', monospace;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 3px;
                color: {_COLORS['title']};
                padding: 4px 0;
            }}

            QLabel#footerLabel {{
                font-family: 'Courier New', monospace;
                font-size: 9px;
                color: {_COLORS['muted']};
                padding: 2px 4px;
            }}

            QTextEdit#resultsEdit {{
                background-color: {_COLORS['bg_edit']};
                border: 1px solid {_COLORS['border']};
                border-radius: 6px;
                padding: 12px;
                color: {_COLORS['normal']};
                font-family: 'Courier New', monospace;
                font-size: 11px;
                selection-background-color: #1a3f60;
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

            QStackedWidget {{
                background-color: {_COLORS['bg']};
            }}
            """
        )

    # API pública
    def show_loading(self, active: bool, message: str = "Analizando radiografía…") -> None:
        """
        Activa o desactiva el spinner de análisis.

        Parámetros
        ----------
        active : bool
            True  → muestra el spinner y oculta el resultado anterior.
            False → vuelve a la página de resultados (o placeholder si no hay).
        message : str
            Texto descriptivo mostrado bajo el spinner.
        """
        if active:
            self._loading_page.set_message(message)
            self._loading_page.start()
            self._stack.setCurrentIndex(self._PAGE_LOADING)
        else:
            self._loading_page.stop()
            if self._result is not None:
                self._stack.setCurrentIndex(self._PAGE_RESULTS)
            else:
                self._stack.setCurrentIndex(self._PAGE_PLACEHOLDER)

    def display_result(self, result: dict) -> None:
        self._result = result
        modelo    = result.pop("modelo", "")
        confianza = result.pop("confianza")

        self._render_document(result)

        # Pie de página con metadatos del modelo
        parts: list[str] = []
        if modelo:
            parts.append(f"Modelo: {modelo}")
        if confianza is not None:
            parts.append(f"Confianza: {confianza * 100:.1f} %")
        self._footer.setText("  ·  ".join(parts))

        self._stack.setCurrentIndex(self._PAGE_RESULTS)

    def current_result(self) -> Optional[dict]:
        """
        Retorna el dict del último resultado renderizado.
        Útil para el generador de informes.
        """
        return self._result

    def has_result(self) -> bool:
        """True si hay un resultado disponible para exportar."""
        return self._result is not None

    def clear(self) -> None:
        """Resetea el panel al estado inicial."""
        self._result = None
        self._text_edit.clear()
        self._footer.setText("")
        self._stack.setCurrentIndex(self._PAGE_PLACEHOLDER)

    # Renderizado interno
    def _render_document(self, result: dict) -> None:
        """Construye el documento formateado en el QTextEdit."""
        doc = QTextDocument()
        doc.setDefaultFont(QFont("Courier New", 11))
        cursor = QTextCursor(doc)

        print(result)
        
        for key in _SECTION_ORDER:
            value = result.pop(key)
            if value is None:
                continue

            label = _SECTION_LABELS.get(key, key.upper())
            self._write_section_header(cursor, label)

            if key == "hallazgos":
                self._write_hallazgos(cursor, value)
            elif key == "recomendaciones":
                self._write_lista(cursor, value)
            elif key == "paciente" and isinstance(value, dict):
                self._write_kv(cursor, value)
            else:
                self._write_paragraph(cursor, str(value))

            self._write_spacer(cursor)

        for key in result:
            self._write_section_header(cursor, key.upper())
            value = result.get(key)
            self._write_paragraph(cursor, str(value))

        self._text_edit.setDocument(doc)
        # Scroll al inicio
        self._text_edit.moveCursor(QTextCursor.MoveOperation.Start)

    # Helpers de escritura
    @staticmethod
    def _fmt(color: str, bold: bool = False, size: int = 11) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        fmt.setFontWeight(700 if bold else 400)
        fmt.setFontPointSize(size)
        fmt.setFontFamilies(["Courier New", "Courier", "monospace"])
        return fmt

    def _write_section_header(self, cursor: QTextCursor, text: str) -> None:
        """Encabezado de sección con línea separadora."""
        # Línea decorativa
        cursor.insertText("─" * 42 + "\n", self._fmt(_COLORS["border"]))
        # Título de sección
        cursor.insertText(f"  {text}\n", self._fmt(_COLORS["section_head"], bold=True, size=10))
        cursor.insertText("─" * 42 + "\n", self._fmt(_COLORS["border"]))

    def _write_paragraph(self, cursor: QTextCursor, text: str) -> None:
        for line in text.splitlines():
            cursor.insertText(f"  {line}\n", self._fmt(_COLORS["normal"]))

    def _write_spacer(self, cursor: QTextCursor) -> None:
        cursor.insertText("\n", self._fmt(_COLORS["bg_edit"]))

    def _write_hallazgos(self, cursor: QTextCursor, value) -> None:
        if isinstance(value, str):
            self._write_paragraph(cursor, value)
            return

        if not isinstance(value, list):
            self._write_paragraph(cursor, str(value))
            return

        for item in value:
            if isinstance(item, dict):
                region      = item.get("region", "")
                descripcion = item.get("descripcion", "")
                severidad   = item.get("severidad", "").lower()
                sev_color   = _SEVERITY_COLOR.get(severidad, _COLORS["normal"])

                # Región en azul claro
                if region:
                    cursor.insertText(f"  ▸ {region}", self._fmt(_COLORS["title"], bold=True))
                    if severidad:
                        cursor.insertText(
                            f"  [{severidad.upper()}]",
                            self._fmt(sev_color, bold=True, size=9),
                        )
                    cursor.insertText("\n", self._fmt(_COLORS["normal"]))

                # Descripción
                if descripcion:
                    for line in descripcion.splitlines():
                        cursor.insertText(f"    {line}\n", self._fmt(_COLORS["normal"]))
                cursor.insertText("\n", self._fmt(_COLORS["normal"]))
            else:
                cursor.insertText(f"  • {item}\n", self._fmt(_COLORS["normal"]))

    def _write_lista(self, cursor: QTextCursor, value) -> None:
        """Renderiza una lista de strings con viñetas."""
        if isinstance(value, str):
            self._write_paragraph(cursor, value)
            return

        if isinstance(value, list):
            for item in value:
                cursor.insertText(f"  →  {item}\n", self._fmt(_COLORS["normal"]))
        else:
            self._write_paragraph(cursor, str(value))

    def _write_kv(self, cursor: QTextCursor, data: dict) -> None:
        """Renderiza un dict como tabla clave: valor."""
        for k, v in data.items():
            key_fmt = self._fmt(_COLORS["muted"], bold=True)
            val_fmt = self._fmt(_COLORS["normal"])
            cursor.insertText(f"  {k:<18}", key_fmt)
            cursor.insertText(f"{v}\n", val_fmt)