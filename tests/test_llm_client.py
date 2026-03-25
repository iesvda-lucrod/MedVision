from core.llm_client import LLMClient
from unittest.mock import patch, MagicMock

@patch('ollama.chat')
def test_predict_success(mock_ollama, sample_context):
    # Simular respuesta de Ollama
    mock_response = MagicMock()
    mock_response.message.content = '{"paciente": {"nombre": "Juan", "edad": "45", "estudio": "RX"}, "descripcion_imagen": "Normal", "hallazgos": [], "impresion": "Sano", "recomendaciones": ["Nada"], "limitaciones": ["Ninguna"], "nota": "IA", "modelo": "test", "confianza": 0.9}'
    mock_ollama.return_value = mock_response

    client = LLMClient()
    result = client.predict(context=sample_context)

    assert result["paciente"]["nombre"] == "Juan"
    assert "hallazgos" in result
    mock_ollama.assert_called_once()