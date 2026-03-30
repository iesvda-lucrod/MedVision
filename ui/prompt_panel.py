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

from ui.theme import QSS, char_counter_style

# Prompt por defecto
_DEFAULT_PROMPT: str = (
    "Analiza esta radiografía e identifica los hallazgos más relevantes. "
    "Describe la región afectada, la severidad y cualquier recomendación clínica."
)

_MAX_CHARS: int = 1000


class PromptPanel(QWidget):
    prompt_changed   = Signal(str)
    prompt_submitted = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(220)
        self.setStyleSheet(QSS["prompt_panel"])
        self._build_ui()

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

        self._update_counter()

    def _on_text_changed(self) -> None:
        self._update_counter()
        self.prompt_changed.emit(self.get_prompt())

    def _on_apply(self) -> None:
        self.prompt_submitted.emit(self.get_prompt())

    def _update_counter(self) -> None:
        n = len(self._editor.toPlainText())
        self._char_counter.setText(f"{n} / {_MAX_CHARS}")
        self._char_counter.setStyleSheet(char_counter_style(over_limit=n > _MAX_CHARS))

    def get_prompt(self) -> str:
        return self._editor.toPlainText()

    def set_prompt(self, text: str) -> None:
        self._editor.setPlainText(text)

    def reset_prompt(self) -> None:
        self._editor.setPlainText(_DEFAULT_PROMPT)

    def clear(self) -> None:
        self._editor.clear()

    def set_run_enabled(self, enabled: bool) -> None:
        self._btn_apply.setEnabled(enabled)
