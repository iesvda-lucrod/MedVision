from __future__ import annotations

import time
import traceback
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QSettings, QSize, Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction, QCloseEvent, QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QToolBar,
    QWidget,
)

from ui.image_panel import ImagePanel
from ui.prompt_panel import PromptPanel
from ui.results_panel import ResultsPanel
from ui.theme import COLORS, FONT_MONO, QSS, inference_time_style, statusbar_style, thread_indicator_style

APP_TITLE   = "RayAI · Análisis de Radiografías"
APP_VERSION = "0.1.0"
WIN_MIN_W   = 1100
WIN_MIN_H   = 680
SPLIT_SIZES = [320, 340, 380]
SLOW_SECS   = 3.0


class AnalysisWorker(QThread):

    progress     = Signal(str)
    preprocessed = Signal(object, object)
    finished     = Signal(dict, float)
    failed       = Signal(str)

    def __init__(self, image_path: str,model_service, prompt: str = "", parent: Optional[QThread] = None,) -> None:
        super().__init__(parent)
        self._path    = image_path
        self._service = model_service
        self._prompt  = prompt

    def run(self) -> None:
        try:
            self.progress.emit("Analizando con el modelo de IA…")
            t0      = time.perf_counter()
            result  = self._service.predict(self._prompt, self._path, True)
            elapsed = time.perf_counter() - t0
            self.finished.emit(result, elapsed)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}")


class MainWindow(QMainWindow):

    def __init__(self, model_service: Any, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._service = model_service
        self._worker: Optional[AnalysisWorker] = None

        self._init_ui()
        self._init_toolbar()
        self._init_statusbar()
        self._wire_signals()
        self._apply_palette()
        self._restore_state()

        self._set_status("Listo.", "idle")

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
        self._splitter.setStyleSheet(QSS["splitter"])
        self.setCentralWidget(self._splitter)

    def _init_toolbar(self) -> None:
        tb = QToolBar("Principal")
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        tb.setStyleSheet(QSS["toolbar"])

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
            f"font-family: {FONT_MONO}; font-size: 9px;"
            f" color: {COLORS['border']}; padding-right: 6px;"
        )
        tb.addWidget(lbl_ver)
        self.addToolBar(tb)

    def _init_statusbar(self) -> None:
        sb = QStatusBar()
        sb.setStyleSheet(QSS["statusbar"])
        self.setStatusBar(sb)

        self._lbl_thread = QLabel("●")
        self._lbl_thread.setStyleSheet(thread_indicator_style(active=False))
        self._lbl_thread.setToolTip("Hilo inactivo")
        sb.addPermanentWidget(self._lbl_thread)

        self._lbl_time = QLabel("")
        self._lbl_time.setStyleSheet(inference_time_style(slow=False))
        sb.addPermanentWidget(self._lbl_time)


    def _wire_signals(self) -> None:
        self._panel_image.image_loaded.connect(self._on_image_loaded)
        self._panel_chart.prompt_submitted.connect(self._on_prompt_submitted)

    @Slot(str)
    def _on_image_loaded(self, path: str) -> None:
        self._act_analyze.setEnabled(True)
        self._act_export.setEnabled(False)
        self._panel_results.clear()
        self._set_status(f"Imagen cargada: {Path(path).name}", "idle")

    @Slot(str)
    def _on_prompt_submitted(self, prompt: str) -> None:
        if not self._panel_image.current_path:
            self._set_status("Carga una imagen antes de analizar.", "error")
            return
        self._start_analysis(prompt=prompt)

    @Slot()
    def _start_analysis(self, prompt: Optional[str] = None) -> None:
        path = self._panel_image.current_path
        if not path:
            self._set_status("No hay imagen cargada.", "error")
            return
        if self._worker and self._worker.isRunning(): return

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
        pass  # sin gráfica de histograma

    @Slot(dict, float)
    def _on_finished(self, result: dict, elapsed: float) -> None:
        self._panel_results.show_loading(False)
        self._panel_results.display_result(result)

        self._act_analyze.setEnabled(True)
        self._act_export.setEnabled(True)
        self._panel_chart.set_run_enabled(True)

        slow = elapsed >= SLOW_SECS
        self._lbl_time.setStyleSheet(inference_time_style(slow=slow))
        self._lbl_time.setText(f"{elapsed:.2f} s  [{'lenta' if slow else 'OK'}]")
        self._set_status(f"Análisis completado en {elapsed:.2f} s", "ok")
        self._set_thread_active(False)

    @Slot(str)
    def _on_failed(self, error: str) -> None:
        self._panel_results.show_loading(False)
        self._act_analyze.setEnabled(True)
        self._panel_chart.set_run_enabled(True)
        self._set_status("Error en el análisis.", "error")
        self._set_thread_active(False)
        QMessageBox.critical(self, "Error de análisis", f"El pipeline falló:\n\n{error[:900]}",)

    @Slot()
    def _export_report(self) -> None:
        if not self._panel_results.has_result():
            self._set_status("Sin resultado para exportar.", "error")
            return
        name = Path(self._panel_image.current_path).name
        self._set_status(f"Exportación solicitada: {name}", "ok")

    @Slot()
    def _clear_all(self) -> None:
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


    def _set_status(self, msg: str, level: str = "idle") -> None:
        self.statusBar().setStyleSheet(statusbar_style(level))
        self.statusBar().showMessage(msg)

    def _set_thread_active(self, active: bool) -> None:
        self._lbl_thread.setStyleSheet(thread_indicator_style(active))
        self._lbl_thread.setToolTip("Hilo activo" if active else "Hilo inactivo")

    def _apply_palette(self) -> None:
        p = QPalette()
        p.setColor(QPalette.ColorRole.Window,          QColor(COLORS["bg"]))
        p.setColor(QPalette.ColorRole.WindowText,      QColor(COLORS["text"]))
        p.setColor(QPalette.ColorRole.Base,            QColor(COLORS["bg_deep"]))
        p.setColor(QPalette.ColorRole.AlternateBase,   QColor("#0a1525"))
        p.setColor(QPalette.ColorRole.Text,            QColor(COLORS["text"]))
        p.setColor(QPalette.ColorRole.Button,          QColor("#0f2035"))
        p.setColor(QPalette.ColorRole.ButtonText,      QColor(COLORS["accent"]))
        p.setColor(QPalette.ColorRole.Highlight,       QColor(COLORS["accent_hover"]))
        p.setColor(QPalette.ColorRole.HighlightedText, QColor(COLORS["accent_bright"]))
        self.setPalette(p)

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

"""
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
"""