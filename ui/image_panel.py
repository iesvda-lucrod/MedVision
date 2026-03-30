from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QFont, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QFileDialog, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from ui.theme import COLORS, QSS

ACCEPTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp")


class _DropZone(QLabel):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(300, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._show_placeholder()

    def set_pixmap_scaled(self, pixmap: QPixmap) -> None:
        self._apply_image_style()
        self.setPixmap(
            pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def reset(self) -> None:
        self.clear()
        self._show_placeholder()



    # Eventos
    def resizeEvent(self, event) -> None:  # noqa: N802
        pix = self.pixmap()
        if pix and not pix.isNull():
            self.setPixmap(
                pix.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        super().resizeEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        if self.pixmap() and not self.pixmap().isNull():
            super().paintEvent(event)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), QColor(COLORS["bg_xdeep"]))

        pen = QPen(QColor(COLORS["accent_deep"]), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        margin = 12
        painter.drawRoundedRect(
            self.rect().adjusted(margin, margin, -margin, -margin), 8, 8
        )

        cx = self.width() // 2
        cy = self.height() // 2 - 20

        icon_pen = QPen(QColor(COLORS["accent_deep"]), 2)
        painter.setPen(icon_pen)

        # Cabeza
        painter.drawEllipse(cx - 14, cy - 44, 28, 28)
        # Columna vertebral
        for i in range(5):
            y = cy - 12 + i * 14
            painter.drawRect(cx - 5, y, 10, 10)
        # Costillas
        for side in (-1, 1):
            for i in range(3):
                y = cy - 10 + i * 14
                path = QPainterPath()
                path.moveTo(cx + side * 5, y + 5)
                path.cubicTo(
                    cx + side * 20, y,
                    cx + side * 30, y + 8,
                    cx + side * 28, y + 14,
                )
                painter.drawPath(path)

        painter.setPen(QColor(COLORS["accent"]))
        painter.setFont(QFont("Courier New", 10))
        painter.drawText(
            self.rect().adjusted(0, 0, 0, -16),
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            "Arrastra una radiografía\no haz clic en Cargar",
        )

        painter.end()

    # Estilos internos
    def _show_placeholder(self) -> None:
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg_xdeep']};
                border-radius: 8px;
            }}
            """)
        self.update()

    def _apply_image_style(self) -> None:
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
            """)


# Panel principal
class ImagePanel(QWidget):

    image_loaded = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._current_path: Optional[str] = None
        self._original_pixmap: Optional[QPixmap] = None

        self._build_ui()
        self.setStyleSheet(QSS["image_panel"])
        self.setAcceptDrops(True)

    # Construcción de la UI
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel("VISOR DE RADIOGRAFÍA")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        self._drop_zone = _DropZone()
        layout.addWidget(self._drop_zone, stretch=1)

        self._info_label = QLabel("Sin imagen cargada")
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._info_label.setObjectName("infoLabel")
        layout.addWidget(self._info_label)

        self._btn_load = QPushButton("⬆  Cargar imagen")
        self._btn_load.setObjectName("btnLoad")
        self._btn_load.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_load.clicked.connect(self._on_load_clicked)

        self._btn_clear = QPushButton("✕  Limpiar")
        self._btn_clear.setObjectName("btnClear")
        self._btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_clear.clicked.connect(self.clear)
        self._btn_clear.setEnabled(False)

        layout.addWidget(self._btn_load)
        layout.addWidget(self._btn_clear)

    # API pública
    def load_image(self, path: str) -> bool:
        path = os.path.abspath(path)

        if not os.path.isfile(path):
            self._info_label.setText(f"⚠  Archivo no encontrado: {os.path.basename(path)}")
            return False

        ext = os.path.splitext(path)[1].lower()
        if ext not in ACCEPTED_EXTENSIONS:
            self._info_label.setText(f"⚠  Formato no soportado: {ext}")
            return False

        pixmap = QPixmap(path)
        if pixmap.isNull():
            self._info_label.setText("⚠  No se pudo leer la imagen.")
            return False

        self._original_pixmap = pixmap
        self._current_path = path
        self._drop_zone.set_pixmap_scaled(pixmap)

        filename = os.path.basename(path)
        w, h = pixmap.width(), pixmap.height()
        self._info_label.setText(f"{filename} - {w} × {h} px")

        self._btn_clear.setEnabled(True)
        self.image_loaded.emit(path)
        return True

    def clear(self) -> None:
        self._current_path = None
        self._original_pixmap = None
        self._drop_zone.reset()
        self._info_label.setText("Sin imagen cargada")
        self._btn_clear.setEnabled(False)

    @property
    def current_path(self) -> Optional[str]:
        return self._current_path

    @property
    def original_pixmap(self) -> Optional[QPixmap]:
        return self._original_pixmap

    # Drag & Drop
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        mime = event.mimeData()
        if mime.hasUrls():
            urls = mime.urls()
            if urls and self._is_valid_image_url(urls[0].toLocalFile()):
                event.acceptProposedAction()
                self._drop_zone.setStyleSheet(f"""
                    QLabel {{
                        background-color: {COLORS['accent_hover']};
                        border: 2px dashed {COLORS['border_focus']};
                        border-radius: 8px;
                    }}
                    """)
                return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        if self._original_pixmap: self._drop_zone._apply_image_style()
        else: self._drop_zone._show_placeholder()
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        mime = event.mimeData()
        if mime.hasUrls():
            for url in mime.urls():
                local_path = url.toLocalFile()
                if self._is_valid_image_url(local_path):
                    self.load_image(local_path)
                    event.acceptProposedAction()
                    return
        event.ignore()

    # Helpers privados
    def _on_load_clicked(self) -> None:
        filters = (
            "Imágenes médicas (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp);;"
            "Todos los archivos (*)"
        )
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar radiografía", "", filters
        )
        if path:
            self.load_image(path)

    @staticmethod
    def _is_valid_image_url(path: str) -> bool:
        ext = os.path.splitext(path)[1].lower()
        return ext in ACCEPTED_EXTENSIONS
