"""
chart_canvas.py
===============
Widget Matplotlib embebido en PySide6 (Qt6) mediante FigureCanvasQTAgg.

Muestra:
  · Histograma de niveles de gris de la imagen preprocesada por OpenCV.
  · Gráfica de tiempos de inferencia del historial.

Dependencias:
    pip install PySide6 matplotlib numpy pandas opencv-python
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

# ---------------------------------------------------------------------------
# Paleta visual (coherente con image_panel / results_panel)
# ---------------------------------------------------------------------------
_STYLE: dict = {
    "fig_bg":       "#07101e",
    "axes_bg":      "#050c18",
    "grid":         "#0f2035",
    "spine":        "#1a3050",
    "text":         "#4a8abf",
    "text_muted":   "#2a5070",
    "tick":         "#3a6080",

    # Histograma
    "hist_fill":    "#1a4a7a",
    "hist_edge":    "#2a6aaa",
    "hist_mean":    "#5ba0d0",
    "hist_median":  "#4aaa70",
    "clahe_fill":   "#0f3a2a",
    "clahe_edge":   "#2a8a5a",

    # Tiempos de inferencia
    "line_color":   "#4a8abf",
    "marker_color": "#5ba0d0",
    "area_color":   "#0f2a45",
    "dot_ok":       "#4aaa70",
    "dot_warn":     "#c09040",
    "dot_err":      "#c05060",
    "threshold":    "#c09040",
}

# Umbral (segundos) a partir del cual una inferencia se considera lenta
_SLOW_THRESHOLD: float = 3.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _style_axes(ax: Axes, title: str = "", xlabel: str = "", ylabel: str = "") -> None:
    """Aplica el estilo oscuro coherente a un Axes."""
    ax.set_facecolor(_STYLE["axes_bg"])
    for spine in ax.spines.values():
        spine.set_edgecolor(_STYLE["spine"])
        spine.set_linewidth(0.8)

    ax.tick_params(colors=_STYLE["tick"], labelsize=7, length=3)
    ax.xaxis.label.set_color(_STYLE["text_muted"])
    ax.yaxis.label.set_color(_STYLE["text_muted"])

    ax.set_xlabel(xlabel, fontsize=8, labelpad=6)
    ax.set_ylabel(ylabel, fontsize=8, labelpad=6)

    if title:
        ax.set_title(title, color=_STYLE["text"], fontsize=9,
                     fontfamily="monospace", pad=8, loc="left")

    ax.grid(True, color=_STYLE["grid"], linewidth=0.5, linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)


# ---------------------------------------------------------------------------
# Widget principal
# ---------------------------------------------------------------------------
class ChartCanvas(FigureCanvasQTAgg):
    """
    Widget Matplotlib embebido en PySide6.

    Uso
    ---
    canvas = ChartCanvas()

    # Histograma de imagen preprocesada (array uint8 o float32)
    canvas.plot_histogram(gray_array)

    # Histograma comparando original y tras CLAHE
    canvas.plot_histogram(gray_array, clahe_array=clahe_processed)

    # Gráfica de tiempos de inferencia
    canvas.plot_inference_times(df)   # df con columnas: timestamp, seconds, label

    canvas.clear()
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        width: int = 5,
        height: int = 4,
        dpi: int = 100,
    ) -> None:
        self._fig = Figure(
            figsize=(width, height),
            dpi=dpi,
            facecolor=_STYLE["fig_bg"],
            tight_layout=True,
        )
        super().__init__(self._fig)
        self.setParent(parent)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(220)
        self.setStyleSheet("background-color: #07101e; border-radius: 6px;")

        self._draw_placeholder()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def plot_histogram(
        self,
        data: np.ndarray,
        clahe_array: Optional[np.ndarray] = None,
        title: str = "Histograma de niveles de gris",
    ) -> None:
        """
        Dibuja el histograma de la imagen preprocesada.

        Parámetros
        ----------
        data : np.ndarray
            Array 2-D (imagen en escala de grises) o 1-D (píxeles aplanados).
            Tipo uint8 (0-255) o float32/64 normalizado (0-1).
        clahe_array : np.ndarray | None
            Si se proporciona, dibuja una segunda distribución (CLAHE)
            en el mismo eje para comparación visual.
        title : str
            Título del gráfico.
        """
        self._fig.clear()

        ax: Axes = self._fig.add_subplot(111)
        _style_axes(ax, title=title, xlabel="Nivel de gris", ylabel="Frecuencia")

        pixels = self._normalize_pixels(data)
        bins   = 256

        # Distribución original
        counts, edges = np.histogram(pixels, bins=bins, range=(0, 255))
        ax.fill_between(
            edges[:-1], counts,
            color=_STYLE["hist_fill"], alpha=0.85, linewidth=0, label="Preprocesada",
        )
        ax.step(
            edges[:-1], counts,
            color=_STYLE["hist_edge"], linewidth=0.8, alpha=0.9,
        )

        # Distribución CLAHE (opcional)
        if clahe_array is not None:
            clahe_pixels = self._normalize_pixels(clahe_array)
            c_counts, c_edges = np.histogram(clahe_pixels, bins=bins, range=(0, 255))
            ax.fill_between(
                c_edges[:-1], c_counts,
                color=_STYLE["clahe_fill"], alpha=0.70, linewidth=0, label="CLAHE",
            )
            ax.step(
                c_edges[:-1], c_counts,
                color=_STYLE["clahe_edge"], linewidth=0.8, alpha=0.9,
            )

        # Media y mediana
        mean_val   = float(np.mean(pixels))
        median_val = float(np.median(pixels))

        ax.axvline(mean_val, color=_STYLE["hist_mean"], linewidth=1.2,
                   linestyle="--", alpha=0.9, label=f"Media  {mean_val:.1f}")
        ax.axvline(median_val, color=_STYLE["hist_median"], linewidth=1.2,
                   linestyle=":", alpha=0.9, label=f"Mediana {median_val:.1f}")

        # Estadísticas textuales en el gráfico
        std_val = float(np.std(pixels))
        stats   = f"μ={mean_val:.1f}  σ={std_val:.1f}  n={pixels.size:,}"
        ax.text(
            0.98, 0.96, stats,
            transform=ax.transAxes, ha="right", va="top",
            fontsize=7, fontfamily="monospace", color=_STYLE["text_muted"],
        )

        self._add_legend(ax)
        self._fig.canvas.draw_idle()

    def plot_inference_times(
        self,
        df: pd.DataFrame,
        title: str = "Tiempos de inferencia",
    ) -> None:
        """
        Dibuja la gráfica de tiempos de inferencia del historial.

        Parámetros
        ----------
        df : pd.DataFrame
            Debe contener al menos:
              · 'seconds'   (float) — duración de la inferencia
            Columnas opcionales:
              · 'timestamp' (datetime-like) — eje X; si falta, usa índice
              · 'label'     (str)           — etiqueta del caso
        title : str
            Título del gráfico.
        """
        self._fig.clear()

        if df.empty:
            self._draw_placeholder("Sin datos de inferencia.")
            return

        ax: Axes = self._fig.add_subplot(111)
        _style_axes(ax, title=title, xlabel="Inferencia n.º", ylabel="Segundos")

        times  = df["seconds"].to_numpy(dtype=float)
        labels = df.get("label", pd.Series([""] * len(df))).tolist()

        # Eje X
        if "timestamp" in df.columns:
            x = np.arange(len(df))
            x_labels = pd.to_datetime(df["timestamp"]).dt.strftime("%H:%M:%S").tolist()
            ax.set_xticks(x)
            ax.set_xticklabels(x_labels, rotation=35, ha="right", fontsize=6)
        else:
            x = np.arange(len(df))

        # Área de relleno bajo la línea
        ax.fill_between(x, times, color=_STYLE["area_color"], alpha=0.6)

        # Línea principal
        ax.plot(x, times, color=_STYLE["line_color"], linewidth=1.4,
                zorder=3, solid_capstyle="round")

        # Umbral de lentitud
        ax.axhline(
            _SLOW_THRESHOLD, color=_STYLE["threshold"],
            linewidth=0.9, linestyle="--", alpha=0.7,
            label=f"Umbral {_SLOW_THRESHOLD} s",
        )

        # Puntos coloreados según rapidez
        for xi, (t, lbl) in enumerate(zip(times, labels)):
            color = _STYLE["dot_ok"] if t < _SLOW_THRESHOLD else _STYLE["dot_warn"]
            ax.scatter(xi, t, color=color, s=28, zorder=4)

        # Media móvil (ventana 3) si hay suficientes datos
        if len(times) >= 3:
            window  = min(5, len(times))
            rolling = pd.Series(times).rolling(window, center=True).mean()
            ax.plot(x, rolling, color=_STYLE["hist_median"],
                    linewidth=1.0, linestyle="--", alpha=0.7,
                    label=f"Media móvil ({window})")

        # Valor máximo anotado
        max_idx = int(np.argmax(times))
        ax.annotate(
            f"{times[max_idx]:.2f}s",
            xy=(x[max_idx], times[max_idx]),
            xytext=(8, 6), textcoords="offset points",
            color=_STYLE["hist_mean"], fontsize=7, fontfamily="monospace",
        )

        ax.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=False))
        self._add_legend(ax)
        self._fig.canvas.draw_idle()

    def clear(self) -> None:
        """Limpia el canvas y muestra el estado vacío."""
        self._fig.clear()
        self._draw_placeholder()
        self._fig.canvas.draw_idle()

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    def _draw_placeholder(self, message: str = "Sin datos para mostrar.") -> None:
        """Placeholder visual cuando no hay datos."""
        self._fig.clear()
        ax: Axes = self._fig.add_subplot(111)
        ax.set_facecolor(_STYLE["axes_bg"])
        for spine in ax.spines.values():
            spine.set_edgecolor(_STYLE["spine"])
        ax.set_xticks([])
        ax.set_yticks([])
        ax.text(
            0.5, 0.5, message,
            transform=ax.transAxes, ha="center", va="center",
            fontsize=10, fontfamily="monospace", color=_STYLE["text_muted"],
        )
        self._fig.canvas.draw_idle()

    @staticmethod
    def _normalize_pixels(data: np.ndarray) -> np.ndarray:
        """
        Convierte cualquier array de imagen a uint8 aplanado [0, 255].
        Acepta:
          · uint8  2-D/3-D (ya en rango correcto)
          · float  2-D/3-D normalizado [0, 1]  → escala a [0, 255]
          · float  2-D/3-D sin normalizar       → re-escala min-max
        """
        arr = np.asarray(data)

        # Convertir a escala de grises si es BGR/RGB
        if arr.ndim == 3:
            arr = arr.mean(axis=2)

        arr = arr.flatten().astype(np.float64)

        if arr.dtype == np.uint8 or arr.max() > 1.0:
            # Ya en [0, 255] o similar
            arr = np.clip(arr, 0, 255)
        else:
            # Normalizado [0, 1] → [0, 255]
            arr = arr * 255.0

        return arr.astype(np.float32)

    @staticmethod
    def _add_legend(ax: Axes) -> None:
        """Leyenda estilizada coherente con la paleta oscura."""
        legend = ax.legend(
            fontsize=7,
            framealpha=0.25,
            facecolor=_STYLE["axes_bg"],
            edgecolor=_STYLE["spine"],
            labelcolor=_STYLE["text"],
            loc="upper right",
        )
        for text in legend.get_texts():
            text.set_fontfamily("monospace")


# ---------------------------------------------------------------------------
# Wrapper QWidget opcional (para insertar en layouts con título)
# ---------------------------------------------------------------------------
class ChartPanel(QWidget):
    """
    Contenedor QWidget que envuelve ChartCanvas con un título
    y lo integra limpiamente en cualquier QLayout.

    Uso:
        panel = ChartPanel()
        panel.canvas.plot_histogram(gray_image)
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        from PySide6.QtWidgets import QLabel

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("ANÁLISIS DE IMAGEN")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            """
            QLabel {
                font-family: 'Courier New', monospace;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 3px;
                color: #4a8abf;
            }
            """
        )
        layout.addWidget(title)

        self.canvas = ChartCanvas(self)
        layout.addWidget(self.canvas)

        self.setStyleSheet("background-color: #07101e; border-radius: 6px;")