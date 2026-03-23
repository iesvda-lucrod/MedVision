"""
main_window.py
==============
Orquestador principal de la aplicación de análisis de radiografías.

No contiene lógica de negocio: únicamente conecta los paneles entre sí
y con los servicios del núcleo a través de señales/slots Qt.

Estructura
----------
  MainWindow (QMainWindow)
  └── QSplitter
      ├── ImagePanel      ← panel izquierdo  (image_panel.py)
      ├── ChartPanel      ← panel central    (prompt_panel.py)
      └── ResultsPanel    ← panel derecho    (results_panel.py)

  AnalysisWorker (QThread)
      Ejecuta preprocesado OpenCV + inferencia del modelo en hilo separado.
      Emite señales al hilo principal cuando termina o falla.

Dependencias:
    pip install PySide6 matplotlib numpy pandas opencv-python
"""

from __future__ import annotations

import time
import traceback
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QSettings, QSize, Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction, QCloseEvent,QColor, QPalette
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QMessageBox, QSizePolicy, QSplitter, QStatusBar, QToolBar, QWidget

from ui.prompt_panel import PromptPanel
from ui.image_panel import ImagePanel
from ui.results_panel import ResultsPanel

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
APP_TITLE   = "RayAI · Análisis de Radiografías"
APP_VERSION = "0.1.0"
WIN_MIN_W   = 1100
WIN_MIN_H   = 680
SPLIT_SIZES = [320, 340, 380]
SLOW_SECS   = 3.0

_STATUS_COLOR = {
    "idle":  "#3a6080",
    "busy":  "#4a8abf",
    "ok":    "#4aaa70",
    "error": "#c05060",
}


# ---------------------------------------------------------------------------
# Worker  —  inferencia en hilo separado
# ---------------------------------------------------------------------------
class AnalysisWorker(QThread):
    """
    Pipeline: carga → preprocesado OpenCV → inferencia del modelo.

    Señales
    -------
    progress(str)
        Mensaje de progreso para barra de estado y spinner.
    preprocessed(np.ndarray, np.ndarray)
        (gray original, gray CLAHE) emitido antes de la inferencia
        para que el histograma aparezca mientras el modelo trabaja.
    finished(dict, float)
        Resultado del modelo y tiempo de inferencia en segundos.
    failed(str)
        Descripción del error si el pipeline falla.
    """

    progress     = Signal(str)
    preprocessed = Signal(object, object)
    finished     = Signal(dict, float)
    failed       = Signal(str)

    def __init__(
        self,
        image_path: str,
        model_service: Any,
        prompt: str = "",
        parent: Optional[QThread] = None,
    ) -> None:
        super().__init__(parent)
        self._path    = image_path
        self._service = model_service
        self._prompt  = prompt

    def run(self) -> None:
        try:
            # 3 · Inferencia ──────────────────────────────────────────
            self.progress.emit("Analizando con el modelo de IA…")
            t0      = time.perf_counter()
            
            result  = self._service.predict(self._prompt, self._path, True)
            elapsed = time.perf_counter() - t0
            self.finished.emit(result, elapsed)

        except Exception as exc:  # noqa: BLE001
            self.failed.emit(
                f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}"
            )


# ---------------------------------------------------------------------------
# Ventana principal
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    """
    Ventana raíz de la aplicación.

    Parámetros
    ----------
    model_service
        Objeto con método ``predict(np.ndarray) -> dict``.
        Se inyecta desde el punto de entrada para facilitar el testing y
        la sustitución del modelo sin modificar la UI.
    """

    def __init__(
        self,
        model_service: Any,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._service  = model_service
        self._worker: Optional[AnalysisWorker] = None

        self._init_ui()
        self._init_toolbar()
        self._init_statusbar()
        self._wire_signals()
        self._apply_palette()
        self._restore_state()

        self._set_status("Listo.", "idle")

    # ══════════════════════════════════════════════════════════════════
    # UI
    # ══════════════════════════════════════════════════════════════════

    def _init_ui(self) -> None:
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(WIN_MIN_W, WIN_MIN_H)

        self._panel_image   = ImagePanel()
        self._panel_chart   = PromptPanel()
        self._panel_results = ResultsPanel()

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(5)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.addWidget(self._panel_image)
        self._splitter.addWidget(self._panel_chart)
        self._splitter.addWidget(self._panel_results)
        self._splitter.setSizes(SPLIT_SIZES)
        self._splitter.setStyleSheet("""
            QSplitter::handle         { background: #0d1c2e; }
            QSplitter::handle:hover   { background: #1e4470; }
            QSplitter::handle:pressed { background: #2a5a8a; }
        """)
        self.setCentralWidget(self._splitter)

    def _init_toolbar(self) -> None:
        tb = QToolBar("Principal")
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        tb.setStyleSheet("""
            QToolBar {
                background: #050c18;
                border-bottom: 1px solid #0d1c2e;
                spacing: 2px;
                padding: 3px 10px;
            }
            QToolButton {
                color: #4a8abf;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                padding: 5px 12px;
                border-radius: 4px;
                border: none;
                background: transparent;
            }
            QToolButton:hover    { background: #0f2a45; color: #8ac8f0; }
            QToolButton:pressed  { background: #071525; }
            QToolButton:disabled { color: #1a3050; }
            QToolBar::separator  { width: 1px; background: #0d1c2e; margin: 5px 8px; }
        """)

        def _act(label: str, shortcut: str, tip: str) -> QAction:
            a = QAction(label, self)
            a.setShortcut(shortcut)
            a.setToolTip(f"{tip}  [{shortcut}]")
            return a

        self._act_open    = _act("⬆  Abrir",    "Ctrl+O",      "Cargar radiografía")
        self._act_analyze = _act("▶  Analizar",  "Ctrl+Return", "Ejecutar análisis de IA")
        self._act_export  = _act("📄  Exportar", "Ctrl+E",      "Exportar informe")
        self._act_clear   = _act("✕  Limpiar",   "Ctrl+W",      "Limpiar todos los paneles")

        self._act_analyze.setEnabled(False)
        self._act_export.setEnabled(False)

        self._act_open.triggered.connect(self._panel_image._on_load_clicked)
        self._act_analyze.triggered.connect(self._start_analysis)
        self._act_export.triggered.connect(self._export_report)
        self._act_clear.triggered.connect(self._clear_all)

        for act in (self._act_open, self._act_analyze):
            tb.addAction(act)
        tb.addSeparator()
        for act in (self._act_export, self._act_clear):
            tb.addAction(act)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)

        lbl_ver = QLabel(f"v{APP_VERSION}")
        lbl_ver.setStyleSheet(
            "font-family:'Courier New'; font-size:9px; color:#1a3050; padding-right:6px;"
        )
        tb.addWidget(lbl_ver)
        self.addToolBar(tb)

    def _init_statusbar(self) -> None:
        sb = QStatusBar()
        sb.setStyleSheet("""
            QStatusBar {
                background: #050c18;
                border-top: 1px solid #0d1c2e;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                padding: 0 10px;
            }
            QStatusBar::item { border: none; }
        """)
        self.setStatusBar(sb)

        self._lbl_thread = QLabel("●")
        self._lbl_thread.setStyleSheet("color:#1a3050; font-size:11px; padding:0 8px;")
        self._lbl_thread.setToolTip("Hilo inactivo")
        sb.addPermanentWidget(self._lbl_thread)

        self._lbl_time = QLabel("")
        self._lbl_time.setStyleSheet(
            "font-family:'Courier New'; font-size:9px; color:#2a5070; padding-right:10px;"
        )
        sb.addPermanentWidget(self._lbl_time)

    # ══════════════════════════════════════════════════════════════════
    # Señales
    # ══════════════════════════════════════════════════════════════════

    def _wire_signals(self) -> None:
        self._panel_image.image_loaded.connect(self._on_image_loaded)
        self._panel_chart.prompt_submitted.connect(self._on_prompt_submitted)

    # ══════════════════════════════════════════════════════════════════
    # Slots
    # ══════════════════════════════════════════════════════════════════

    @Slot(str)
    def _on_image_loaded(self, path: str) -> None:
        """ImagePanel cargó una imagen → habilita Analizar y limpia sesión anterior."""
        self._act_analyze.setEnabled(True)
        self._act_export.setEnabled(False)
        self._panel_results.clear()
        self._set_status(f"Imagen cargada: {Path(path).name}", "idle")

    @Slot(str)
    def _on_prompt_submitted(self, prompt: str) -> None:
        """El panel de prompt disparó Analizar → lanzar análisis si hay imagen."""
        if not self._panel_image.current_path:
            self._set_status("Carga una imagen antes de analizar.", "error")
            return
        self._start_analysis(prompt=prompt)

    @Slot()
    def _start_analysis(self, prompt: Optional[str] = None) -> None:
        """Valida estado y lanza el AnalysisWorker."""
        path = self._panel_image.current_path
        if not path:
            self._set_status("No hay imagen cargada.", "error")
            return
        if self._worker and self._worker.isRunning():
            return  # análisis ya en marcha

        self._panel_results.show_loading(True, "Iniciando análisis…")
        self._act_analyze.setEnabled(False)
        self._act_export.setEnabled(False)
        self._panel_chart.set_run_enabled(False)
        self._lbl_time.setText("")
        self._set_status("Ejecutando análisis…", "busy")
        self._set_thread_active(True)

        active_prompt = prompt or self._panel_chart.get_prompt()
        self._worker = AnalysisWorker(path, self._service, prompt=active_prompt, parent=self)
        self._worker.progress.connect(self._on_progress)
        self._worker.preprocessed.connect(self._on_preprocessed)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    @Slot(str)
    def _on_progress(self, msg: str) -> None:
        self._set_status(msg, "busy")
        self._panel_results.show_loading(True, msg)

    @Slot(object, object)
    def _on_preprocessed(self, gray, clahe) -> None:
        pass  # preprocesado recibido; sin gráfica de histograma

    @Slot(dict, float)
    def _on_finished(self, result: dict, elapsed: float) -> None:
        """Worker terminó con éxito → actualizar paneles de resultado."""
        self._panel_results.show_loading(False)
        self._panel_results.display_result(result)

        self._act_analyze.setEnabled(True)
        self._act_export.setEnabled(True)
        self._panel_chart.set_run_enabled(True)

        slow  = elapsed >= SLOW_SECS
        color = "#c09040" if slow else "#4aaa70"
        tag   = "lenta" if slow else "OK"
        self._lbl_time.setStyleSheet(
            f"font-family:'Courier New'; font-size:9px; color:{color}; padding-right:10px;"
        )
        self._lbl_time.setText(f"{elapsed:.2f} s  [{tag}]")
        self._set_status(f"Análisis completado en {elapsed:.2f} s", "ok")
        self._set_thread_active(False)

    @Slot(str)
    def _on_failed(self, error: str) -> None:
        """Worker terminó con error → informar al usuario."""
        self._panel_results.show_loading(False)
        self._act_analyze.setEnabled(True)
        self._panel_chart.set_run_enabled(True)
        self._set_status("Error en el análisis.", "error")
        self._set_thread_active(False)
        QMessageBox.critical(
            self, "Error de análisis",
            f"El pipeline falló:\n\n{error[:900]}",
        )

    @Slot()
    def _export_report(self) -> None:
        """Hook para el generador de informes externo."""
        if not self._panel_results.has_result():
            self._set_status("Sin resultado para exportar.", "error")
            return
        # report_service.generate(
        #     result     = self._panel_results.current_result(),
        #     image_path = self._panel_image.current_path,
        # )
        name = Path(self._panel_image.current_path).name
        self._set_status(f"Exportación solicitada: {name}", "ok")

    @Slot()
    def _clear_all(self) -> None:
        """Resetea todos los paneles al estado vacío."""
        if self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(500)

        self._panel_image.clear()
        self._panel_results.clear()
        self._panel_chart.set_run_enabled(True)
        self._act_analyze.setEnabled(False)
        self._act_export.setEnabled(False)
        self._lbl_time.setText("")
        self._set_status("Listo.", "idle")
        self._set_thread_active(False)

    # ══════════════════════════════════════════════════════════════════
    # Helpers de UI
    # ══════════════════════════════════════════════════════════════════

    def _set_status(self, msg: str, level: str = "idle") -> None:
        color = _STATUS_COLOR.get(level, _STATUS_COLOR["idle"])
        self.statusBar().setStyleSheet(f"""
            QStatusBar {{
                background: #050c18;
                border-top: 1px solid #0d1c2e;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                color: {color};
                padding: 0 10px;
            }}
            QStatusBar::item {{ border: none; }}
        """)
        self.statusBar().showMessage(msg)

    def _set_thread_active(self, active: bool) -> None:
        if active:
            self._lbl_thread.setStyleSheet("color:#4a8abf; font-size:11px; padding:0 8px;")
            self._lbl_thread.setToolTip("Hilo activo")
        else:
            self._lbl_thread.setStyleSheet("color:#1a3050; font-size:11px; padding:0 8px;")
            self._lbl_thread.setToolTip("Hilo inactivo")

    def _apply_palette(self) -> None:
        p = QPalette()
        p.setColor(QPalette.ColorRole.Window,          QColor("#07101e"))
        p.setColor(QPalette.ColorRole.WindowText,      QColor("#a8c8e8"))
        p.setColor(QPalette.ColorRole.Base,            QColor("#050c18"))
        p.setColor(QPalette.ColorRole.AlternateBase,   QColor("#0a1525"))
        p.setColor(QPalette.ColorRole.Text,            QColor("#a8c8e8"))
        p.setColor(QPalette.ColorRole.Button,          QColor("#0f2035"))
        p.setColor(QPalette.ColorRole.ButtonText,      QColor("#4a8abf"))
        p.setColor(QPalette.ColorRole.Highlight,       QColor("#1a3f60"))
        p.setColor(QPalette.ColorRole.HighlightedText, QColor("#90d0ff"))
        self.setPalette(p)

    # ══════════════════════════════════════════════════════════════════
    # Persistencia de geometría y splitter
    # ══════════════════════════════════════════════════════════════════

    def _restore_state(self) -> None:
        s = QSettings("RayAI", "MainWindow")
        if geo := s.value("geometry"):
            self.restoreGeometry(geo)
        else:
            self.resize(WIN_MIN_W, WIN_MIN_H)
        if spl := s.value("splitter"):
            self._splitter.restoreState(spl)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        s = QSettings("RayAI", "MainWindow")
        s.setValue("geometry", self.saveGeometry())
        s.setValue("splitter", self._splitter.saveState())
        if self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(1500)
        super().closeEvent(event)


# ---------------------------------------------------------------------------
# Stub para desarrollo / pruebas sin modelo real
# ---------------------------------------------------------------------------
class _StubModelService:
    """
    Servicio de modelo mínimo para ejecutar la UI sin modelo real.
    Reemplazar por la implementación real en producción.
    """

    def predict(self, _: np.ndarray) -> dict:
        time.sleep(1.8)
        return {
            "paciente": {
                "Nombre":  "—",
                "Edad":    "—",
                "Estudio": "RX Tórax PA",
            },
            "hallazgos": [
                {
                    "region":      "Pulmón derecho",
                    "descripcion": "Sin alteraciones significativas.",
                    "severidad":   "normal",
                },
                {
                    "region":      "Pulmón izquierdo",
                    "descripcion": (
                        "Opacidad basal leve compatible con atelectasia laminar.\n"
                        "No se observan derrames ni masas."
                    ),
                    "severidad":   "leve",
                },
                {
                    "region":      "Mediastino",
                    "descripcion": "Silueta cardíaca dentro de límites normales.",
                    "severidad":   "normal",
                },
            ],
            "impresion": (
                "Estudio dentro de límites normales con mínima atelectasia "
                "basal izquierda de probable origen postural."
            ),
            "recomendaciones": [
                "Correlación clínica.",
                "Control radiológico en 4 semanas si persiste la sintomatología.",
                "Considerar espirometría si hay disnea asociada.",
            ],
            "nota":      "Resultado de modelo stub. No usar con fines diagnósticos.",
            "modelo":    "StubNet-v0",
            "confianza": 0.87,
        }


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from core.llm_client import LLMClient

    app = QApplication(sys.argv)
    app.setApplicationName("RayAI")
    app.setOrganizationName("RayAI")
    app.setStyle("Fusion")

    window = MainWindow(model_service=LLMClient())
    window.show()
    sys.exit(app.exec())