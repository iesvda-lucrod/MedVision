import cv2
import numpy as np
import base64
from pathlib import Path

class ImageProcessor():
    def __init__(self):
        pass

    def _read_image(self, path: str) -> str:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"No se encontró la imagen {path}")
        
        raw_bytes = np.fromfile(path, dtype=np.uint8)
        img = cv2.imdecode(raw_bytes, cv2.IMREAD_UNCHANGED)

        if img is None:
            raise ValueError(f"OpenCV no pudo decodificar la imagen: {path}")
        
        return img

    def _to_grayscale(self, img: np.ndarray) -> np.ndarray:
        if img.ndim == 2:
            return img
        
        if img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def _equalize(self, gray: np.ndarray) -> np.ndarray:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray)

    def _to_base64(self, img: np.ndarray) -> str:
        ok, buffer = cv2.imencode(".png", img)
        if not ok:
            raise RuntimeError("cv2.imencode falló al codificar PNG")

        return base64.b64encode(buffer).decode("utf-8")

    def preprocess(self, path: str | Path) -> dict:
        raw   = self._read_image(path)
        gray  = self._to_grayscale(raw)
        eq    = self._equalize(gray)
        b64   = self._to_base64(eq)

        return {
            "image":  eq,
            "base64": b64,
            "shape":  eq.shape[:2],
        }