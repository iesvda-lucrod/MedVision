from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QFont, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QFileDialog, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

ACCEPTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp")

class _DropZone(QLabel):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(300, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._show_placeholder()

    # API pública
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

        # Fondo
        painter.fillRect(self.rect(), QColor("#0a0f1a"))

        # Borde discontinuo
        pen = QPen(QColor("#2a4a6b"), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        margin = 12
        painter.drawRoundedRect(
            self.rect().adjusted(margin, margin, -margin, -margin), 8, 8
        )

        # Icono de radiografía
        cx = self.width() // 2
        cy = self.height() // 2 - 20

        icon_pen = QPen(QColor("#2a5a8b"), 2)
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

        # Texto de instrucción
        painter.setPen(QColor("#3a6a9b"))
        painter.setFont(QFont("Courier New", 10))
        painter.drawText(
            self.rect().adjusted(0, 0, 0, -16),
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            "Arrastra una radiografía o haz clic en Cargar",
        )

        painter.end()

    # Estilos internos
    def _show_placeholder(self) -> None:
        self.setStyleSheet(
            """
            QLabel {
                background-color: #0a0f1a;
                border-radius: 8px;
            }
            """
        )
        self.update()

    def _apply_image_style(self) -> None:
        self.setStyleSheet(
            """
            QLabel {
                background-color: #050a12;
                border: 1px solid #1a3a5a;
                border-radius: 8px;
            }
            """
        )


# Panel principal
class ImagePanel(QWidget):
    """
    Panel izquierdo de la aplicación de análisis de radiografías.

    Señales
    -------
    image_loaded(str)
        Se emite cuando se ha cargado una imagen correctamente.
        El argumento es la ruta absoluta del archivo.

    Uso
    ---
    panel = ImagePanel()
    panel.image_loaded.connect(on_image_ready)
    """

    # Señal pública
    image_loaded = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._current_path: Optional[str] = None
        self._original_pixmap: Optional[QPixmap] = None

        self._build_ui()
        self._apply_styles()

        # Habilitar drag & drop en el widget raíz
        self.setAcceptDrops(True)

    # Construcción de la UI
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Título del panel
        title = QLabel("VISOR DE RADIOGRAFÍA")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        # Zona de imagen / drop
        self._drop_zone = _DropZone()
        layout.addWidget(self._drop_zone, stretch=1)

        # Barra de información (nombre de archivo + resolución)
        self._info_label = QLabel("Sin imagen cargada")
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._info_label.setObjectName("infoLabel")
        layout.addWidget(self._info_label)

        # Botones de acción
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

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            ImagePanel {
                background-color: #07101e;
                border-right: 1px solid #1a3050;
            }

            QLabel#panelTitle {
                font-family: 'Courier New', monospace;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 3px;
                color: #4a8abf;
                padding: 4px 0;
            }

            QLabel#infoLabel {
                font-family: 'Courier New', monospace;
                font-size: 10px;
                color: #3a6080;
                padding: 2px 0;
            }

            QPushButton#btnLoad {
                background-color: #0f2a45;
                color: #6ab0e0;
                border: 1px solid #2a5a8a;
                border-radius: 5px;
                padding: 8px 16px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                letter-spacing: 1px;
            }
            QPushButton#btnLoad:hover {
                background-color: #1a3f60;
                border-color: #4a8abf;
                color: #90d0ff;
            }
            QPushButton#btnLoad:pressed {
                background-color: #0a1f35;
            }

            QPushButton#btnClear {
                background-color: transparent;
                color: #3a5a7a;
                border: 1px solid #1a3050;
                border-radius: 5px;
                padding: 6px 16px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                letter-spacing: 1px;
            }
            QPushButton#btnClear:hover {
                background-color: #1a1a2e;
                border-color: #8a3040;
                color: #c06070;
            }
            QPushButton#btnClear:disabled {
                color: #1a2a3a;
                border-color: #111e2e;
            }
            """
        )

    # API pública
    def load_image(self, path: str) -> bool:
        """
        Carga la imagen ubicada en *path*, la escala y la muestra.

        Parámetros
        ----------
        path : str
            Ruta absoluta o relativa al archivo de imagen.

        Retorna
        -------
        bool
            True si la imagen se cargó con éxito, False en caso contrario.
        """
        path = os.path.abspath(path)

        if not os.path.isfile(path):
            self._info_label.setText(
                f"⚠  Archivo no encontrado: {os.path.basename(path)}"
            )
            return False

        ext = os.path.splitext(path)[1].lower()
        if ext not in ACCEPTED_EXTENSIONS:
            self._info_label.setText(f"⚠  Formato no soportado: {ext}")
            return False

        pixmap = QPixmap(path)
        if pixmap.isNull():
            self._info_label.setText("⚠  No se pudo leer la imagen.")
            return False

        # Guardar referencia al pixmap original (sin escalar)
        self._original_pixmap = pixmap
        self._current_path = path

        # Mostrar en la zona de drop
        self._drop_zone.set_pixmap_scaled(pixmap)

        # Actualizar info
        filename = os.path.basename(path)
        w, h = pixmap.width(), pixmap.height()
        self._info_label.setText(f"{filename}  ·  {w} × {h} px")

        # Activar botón limpiar
        self._btn_clear.setEnabled(True)

        # Emitir señal
        self.image_loaded.emit(path)
        return True

    def clear(self) -> None:
        """Resetea el visor al estado inicial sin imagen."""
        self._current_path = None
        self._original_pixmap = None
        self._drop_zone.reset()
        self._info_label.setText("Sin imagen cargada")
        self._btn_clear.setEnabled(False)

    @property
    def current_path(self) -> Optional[str]:
        """Ruta del archivo actualmente cargado, o None."""
        return self._current_path

    @property
    def original_pixmap(self) -> Optional[QPixmap]:
        """QPixmap original (sin escalar) de la imagen cargada, o None."""
        return self._original_pixmap

    # Drag & Drop
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        """Acepta el evento si contiene URLs de archivos de imagen válidos."""
        mime = event.mimeData()
        if mime.hasUrls():
            urls = mime.urls()
            if urls and self._is_valid_image_url(urls[0].toLocalFile()):
                event.acceptProposedAction()
                # Feedback visual: resaltar borde
                self._drop_zone.setStyleSheet(
                    """
                    QLabel {
                        background-color: #0d1f35;
                        border: 2px dashed #4a9abf;
                        border-radius: 8px;
                    }
                    """
                )
                return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        """Restaura el estilo al salir del área de drop."""
        if self._original_pixmap:
            self._drop_zone._apply_image_style()
        else:
            self._drop_zone._show_placeholder()
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        """Carga la primera imagen válida que se suelta sobre el panel."""
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
        """Abre un diálogo de selección de archivo."""
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