from __future__ import annotations
from typing import Optional
import textwrap
from models import config

#  JSON Schema de salida
FORMAT = {
    "type": "object",
    "required": [
        "paciente",
        "descripcion_imagen",
        "hallazgos",
        "impresion",
        "recomendaciones",
        "limitaciones",
        "nota",
        "modelo",
        "confianza",
    ],
    "properties": {
        "paciente": {
            "type": "object",
            "required": ["nombre", "edad", "estudio"],
            "properties": {
                "nombre":  {"type": "string"},
                "edad":    {"type": "string"},
                "estudio": {"type": "string"},
            },
        },
        "descripcion_imagen": {
            "type": "string",
            "description": "Descripción breve de la imagen proporcionada (máx. 3 líneas). Si no hay imagen: 'No se ha proporcionado imagen'.",
        },
        "hallazgos": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["region", "descripcion", "severidad"],
                "properties": {
                    "region":      {"type": "string"},
                    "descripcion": {"type": "string"},
                    "severidad":   {
                        "type": "string",
                        "enum": ["normal", "leve", "moderado", "severo"],
                    },
                },
            },
        },
        "impresion": {
            "type": "string",
            "description": "Resumen clínico conciso (1–3 oraciones). Indica si el estudio es globalmente normal o presenta alteraciones.",
        },
        "recomendaciones": {
            "type": "array",
            "minItems": 1,
            "maxItems": 5,
            "items": {"type": "string"},
        },
        "nota":  {"type": "string"},
        "modelo": {"type": "string"},
        "confianza": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Valor conservador ante hallazgos ambiguos o imagen de baja calidad.",
        },
    },
}
#  SYSTEM PROMPT
SYSTEM_PROMPT = f"""\
Eres un radiólogo asistente experto en interpretación de imágenes médicas.
Generas informes radiológicos estructurados en español con precisión clínica.

## ROL Y ALCANCE
Actúas como apoyo al radiólogo humano. Tus análisis son orientativos y nunca
reemplazan el criterio clínico ni el diagnóstico médico formal.

## IDIOMA Y TERMINOLOGÍA
Responde exclusivamente en español. Emplea terminología radiológica estándar:
opacidad, consolidación, derrame pleural, atelectasia, silueta cardíaca,
mediastino, hiperinsuflación, etc.

## FORMATO DE SALIDA — MUY IMPORTANTE
Responde ÚNICAMENTE con un objeto JSON válido que cumpla el schema proporcionado.
No incluyas texto antes ni después del JSON, ni bloques de código Markdown.

## REGLAS DE CONTENIDO

### descripcion_imagen
- Describe brevemente la imagen recibida (modalidad, proyección, calidad técnica).
- Máximo 3 líneas.
- Si no se proporcionó imagen: "No se ha proporcionado imagen".

### hallazgos
- Incluye todas las regiones anatómicas relevantes para el tipo de estudio.
- Si una región es normal: "Sin alteraciones significativas."
- Separa múltiples observaciones de una misma región con \\n.
- `severidad` refleja el hallazgo más relevante de esa región.

### impresion
- Resume los hallazgos más relevantes en lenguaje clínico conciso (1–3 oraciones).
- Indica siempre si el estudio es globalmente normal o presenta alteraciones.
- Usa lenguaje probabilístico: "compatible con", "sugestivo de", "no se puede descartar".

### recomendaciones
- Solo incluye recomendaciones justificadas por los hallazgos (mín. 1, máx. 5).
- Si el estudio es normal: ["Correlación clínica."]

### confianza
- Valor entre 0.0 y 1.0. Sé conservador ante hallazgos ambiguos o imagen de baja calidad.

## RESTRICCIONES
- Nunca afirmes diagnósticos definitivos.
- `nota` debe ser siempre: "Resultado de modelo IA. Acudir siempre a un profesional para verificar el diagnóstico."
- `modelo` debe ser: {config.MODEL_NAME}
"""

#  USER PROMPT TEMPLATE
ANALYSIS_TEMPLATE: str = textwrap.dedent("""\
    ## Contexto clínico
    {context}

    ---
    Analiza la imagen médica adjunta (si se ha proporcionado) y genera un informe
    radiológico estructurado como objeto JSON válido con los siguientes campos:

    1. **paciente** — Datos del paciente extraídos del contexto clínico.
       Si no se dispone de nombre o edad, usa "No disponible".

    2. **nota**, **modelo**, **confianza** — Rellena según las instrucciones del sistema.

    Responde ÚNICAMENTE con el JSON. Sin texto adicional, sin bloques de código.
""")


#  build_prompt() — Construye el prompt final
def build_prompt(context: str) -> dict[str, str]:
    return {
        "system": SYSTEM_PROMPT,
        "prompt": ANALYSIS_TEMPLATE.format(
            context=context.strip() or "Sin contexto clínico aportado.",
        ),
    }

"""
# Ejemplo, ejecutar como módulo para probar
if __name__ == "__main__":
    import json
    import ollama
    from models import config

    payload = build_prompt(
        context="Varón 58 años. Disnea de esfuerzo. Fumador 30 paquetes/año."
    )

    response = ollama.chat(
        model=config.MODEL_NAME,
        messages=[
            {"role": "system",  "content": payload["system"]},
            {"role": "user",    "content": payload["prompt"]},
        ],
        format=FORMAT,   # structured output nativo de ollama
    )

    raw = response["message"]["content"]

    try:
        report = json.loads(raw)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except json.JSONDecodeError as e:
        print(f"[ERROR] La respuesta no es JSON válido: {e}")
        print(raw)
"""
