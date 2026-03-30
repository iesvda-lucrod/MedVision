from models.prompts import build_prompt, FORMAT

def test_build_prompt_content():
    ctx = "Mujer 30 años, chequeo de rutina."
    payload = build_prompt(ctx)
    
    assert "system" in payload
    assert "prompt" in payload
    assert ctx in payload["prompt"]
    assert "radiólogo asistente" in payload["system"]

def test_format_schema_structure():
    required_fields = ["paciente", "hallazgos", "impresion", "confianza"]
    for field in required_fields:
        assert field in FORMAT["required"]