# tests/test_llm_client.py

import pytest
import time
from unittest.mock import patch, MagicMock, mock_open
from models.llm_client import LLMClient
from models.prompts import RadiologiaConfig


# ─────────────────────────────────────────────
#  Helpers / fixtures
# ─────────────────────────────────────────────

FAKE_RAW_RESPONSE = """
HALLAZGOS:
- Opacidad en lóbulo inferior derecho compatible con consolidación.
- Leve derrame pleural bilateral.
- No se observan masas ni nódulos adicionales.

CONCLUSIÓN:
Patrón radiológico sugestivo de neumonía lobar derecha.
"""

FAKE_MODEL_NAME = "llava:13b"


def make_mock_config(model=FAKE_MODEL_NAME, temperature=0.2, num_ctx=4096):
    cfg = MagicMock()
    cfg.MODEL_NAME   = model
    cfg.TEMPERATURE  = temperature
    cfg.NUM_CTX      = num_ctx
    return cfg


def make_chunk(text: str):
    chunk = MagicMock()
    chunk.message.content = text
    return chunk


# ─────────────────────────────────────────────
#  Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def client(monkeypatch):
    """LLMClient con config mockeada."""
    mock_cfg = make_mock_config()
    monkeypatch.setattr("models.llm_client.config", mock_cfg)
    return LLMClient()


@pytest.fixture
def mock_build_prompt():
    with patch("models.llm_client.build_prompt") as m:
        m.return_value = {
            "system": "Eres un radiólogo experto.",
            "prompt": "Analiza el siguiente contexto clínico.",
        }
        yield m


@pytest.fixture
def mock_ollama_stream():
    """Simula ollama.chat en modo stream."""
    chunks = [make_chunk(t) for t in ["HALLAZGOS:\n", "- Consolidación lobar.\n", "- Derrame pleural.\n"]]
    with patch("models.llm_client.ollama.chat", return_value=iter(chunks)) as m:
        yield m


@pytest.fixture
def mock_ollama_no_stream():
    """Simula ollama.chat en modo no-stream."""
    response = MagicMock()
    response.message.content = FAKE_RAW_RESPONSE
    with patch("models.llm_client.ollama.chat", return_value=response) as m:
        yield m


@pytest.fixture
def mock_image_processor():
    with patch("models.llm_client.image_processor.preprocess") as m:
        m.return_value = {"base64": "iVBORw0KGgoAAAANSUhEUgAAAAUA"}
        yield m


# ─────────────────────────────────────────────
#  TEST 1 — Sin imagen (stream=False)
# ─────────────────────────────────────────────

class TestAnalyzeSinImagen:

    def test_retorna_dict_con_claves_requeridas(
        self, client, mock_build_prompt, mock_ollama_no_stream
    ):
        result = client.analyze(
            context="Paciente con fiebre y tos productiva.",
            stream=False,
        )

        assert isinstance(result, dict), "El resultado debe ser un dict"
        assert "findings"        in result
        assert "inference_time"  in result
        assert "model"           in result

    def test_findings_es_lista_no_vacia(
        self, client, mock_build_prompt, mock_ollama_no_stream
    ):
        result = client.analyze(context="Disnea progresiva.", stream=False)

        assert isinstance(result["findings"], list)
        assert len(result["findings"]) > 0, "Debe haber al menos un hallazgo"

    def test_findings_contiene_texto_limpio(
        self, client, mock_build_prompt, mock_ollama_no_stream
    ):
        result = client.analyze(context="Dolor torácico.", stream=False)

        for f in result["findings"]:
            assert f == f.strip(), f"Hallazgo con espacios extra: '{f}'"
            assert not f.startswith("-"),  "No deben quedar viñetas"
            assert not f.startswith("*"),  "No deben quedar asteriscos"

    def test_model_coincide_con_config(
        self, client, mock_build_prompt, mock_ollama_no_stream
    ):
        result = client.analyze(context="Control rutinario.", stream=False)
        assert result["model"] == FAKE_MODEL_NAME

    def test_inference_time_es_positivo(
        self, client, mock_build_prompt, mock_ollama_no_stream
    ):
        result = client.analyze(context="Hemoptisis.", stream=False)
        assert result["inference_time"] >= 0

    def test_no_llama_image_processor_sin_imagen(
        self, client, mock_build_prompt, mock_ollama_no_stream, mock_image_processor
    ):
        client.analyze(context="Sin imagen adjunta.", stream=False)
        mock_image_processor.assert_not_called()

    def test_ollama_recibe_system_y_user_messages(
        self, client, mock_build_prompt, mock_ollama_no_stream
    ):
        client.analyze(context="Contexto clínico.", stream=False)

        call_kwargs = mock_ollama_no_stream.call_args.kwargs
        messages    = call_kwargs["messages"]

        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "images" not in messages[1], "No debe incluir 'images' sin imagen"


# ─────────────────────────────────────────────
#  TEST 2 — Con imagen (stream=True)
# ─────────────────────────────────────────────

class TestAnalyzeConImagen:

    def test_retorna_dict_con_claves_requeridas(
        self, client, mock_build_prompt, mock_ollama_stream, mock_image_processor
    ):
        result = client.analyze(
            context="Radiografía de tórax PA.",
            image_path="/fake/radiografia.png",
            stream=True,
        )

        assert "findings"        in result
        assert "inference_time"  in result
        assert "model"           in result

    def test_findings_extraidos_del_stream(
        self, client, mock_build_prompt, mock_ollama_stream, mock_image_processor
    ):
        result = client.analyze(
            context="Paciente con disnea.",
            image_path="/fake/rx.jpg",
            stream=True,
        )

        assert isinstance(result["findings"], list)
        assert len(result["findings"]) > 0

    def test_image_processor_llamado_con_ruta(
        self, client, mock_build_prompt, mock_ollama_stream, mock_image_processor
    ):
        image_path = "/fake/chest_xray.png"
        client.analyze(
            context="Disnea aguda.",
            image_path=image_path,
            stream=True,
        )
        mock_image_processor.assert_called_once_with(image_path)

    def test_ollama_recibe_imagen_en_base64(
        self, client, mock_build_prompt, mock_ollama_stream, mock_image_processor
    ):
        client.analyze(
            context="Fiebre y tos.",
            image_path="/fake/img.png",
            stream=True,
        )

        call_kwargs = mock_ollama_stream.call_args.kwargs
        user_msg    = call_kwargs["messages"][1]

        assert "images" in user_msg, "El mensaje de usuario debe incluir 'images'"
        assert len(user_msg["images"]) == 1
        assert user_msg["images"][0] == "iVBORw0KGgoAAAANSUhEUgAAAAUA"

    def test_model_correcto_con_imagen(
        self, client, mock_build_prompt, mock_ollama_stream, mock_image_processor
    ):
        result = client.analyze(
            context="TC de tórax.",
            image_path="/fake/tc.dcm",
            stream=True,
        )
        assert result["model"] == FAKE_MODEL_NAME

    def test_inference_time_mayor_que_cero_con_stream(
        self, client, mock_build_prompt, mock_ollama_stream, mock_image_processor
    ):
        """Con stream real habría latencia; aquí verificamos que el campo existe y es >= 0."""
        result = client.analyze(
            context="Control anual.",
            image_path="/fake/img.png",
            stream=True,
        )
        assert result["inference_time"] >= 0


# ─────────────────────────────────────────────
#  TEST 3 — _parse_response unitario
# ─────────────────────────────────────────────

class TestParseResponse:

    def test_extrae_hallazgos_de_seccion_etiquetada(self, client):
        raw = "HALLAZGOS:\n- Opacidad basal derecha.\n- Sin derrame pleural.\n"
        result = client._parse_response(raw)
        assert "Opacidad basal derecha." in result["findings"]
        assert "Sin derrame pleural."    in result["findings"]

    def test_fallback_texto_plano(self, client):
        raw = "No se observan alteraciones significativas."
        result = client._parse_response(raw)
        assert len(result["findings"]) == 1
        assert "No se observan alteraciones significativas." in result["findings"][0]

    def test_inference_time_pasado_directamente(self, client):
        result = client._parse_response("Hallazgo de prueba.", inference_time=1.234)
        assert result["inference_time"] == pytest.approx(1.234, abs=0.001)

    def test_raw_vacio_devuelve_lista_vacia(self, client):
        result = client._parse_response("")
        assert result["findings"] == []

    def test_no_quedan_vinietas_en_findings(self, client):
        raw = "FINDINGS:\n* Masa hiliar izquierda.\n• Adenopatías mediastínicas.\n"
        result = client._parse_response(raw)
        for f in result["findings"]:
            assert not f.startswith(("*", "•", "-"))
