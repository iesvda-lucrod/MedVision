import pytest
import numpy as np
import cv2
import os

@pytest.fixture
def mock_image_path(tmp_path):
    """Crea una imagen de prueba temporal (512x512 px)."""
    img_path = tmp_path / "test_lung.png"
    # Crear una imagen sintética (un círculo blanco sobre fondo negro)
    img = np.zeros((512, 512), dtype=np.uint8)
    cv2.circle(img, (256, 256), 100, (255), -1)
    cv2.imwrite(str(img_path), img)
    return str(img_path)

@pytest.fixture
def sample_context():
    return "Paciente: Juan Pérez, 45 años. Tos persistente."