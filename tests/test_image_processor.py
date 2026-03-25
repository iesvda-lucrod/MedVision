from core.image_processor import _read_image, _to_grayscale, preprocess_image
import numpy as np
import pytest

def test_read_image_error():
    with pytest.raises(FileNotFoundError):
        _read_image("ruta/inexistente.jpg")

def test_to_grayscale_conversion():
    # Crear imagen RGB (3 canales)
    rgb_img = np.zeros((100, 100, 3), dtype=np.uint8)
    gray = _to_grayscale(rgb_img)
    assert gray.ndim == 2
    assert gray.shape == (100, 100)

def test_preprocess_image_returns_keys(mock_image_path):
    result = preprocess_image(mock_image_path)
    assert "base64" in result
    assert "eq" in result
    assert isinstance(result["base64"], str)
    # Verificar que el string base64 no esté vacío
    assert len(result["base64"]) > 0