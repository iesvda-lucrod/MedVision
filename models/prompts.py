from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import textwrap

FORMAT = {
  "type": "object",
  "required": ["paciente", "hallazgos", "impresion", "recomendaciones", "nota", "modelo", "confianza", "descripcion de la imagen"],
  "properties": {
    "paciente": {
      "type": "object",
      "required": ["Nombre", "Edad", "Estudio"],
      "properties": {
        "Nombre":  { "type": "string" },
        "Edad":    { "type": "string" },
        "Estudio": { "type": "string" }
      }
    },
    "hallazgos": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["region", "descripcion", "severidad"],
        "properties": {
          "region":      { "type": "string" },
          "descripcion": { "type": "string" },
          "severidad":   { "type": "string", "enum": ["normal", "leve", "moderado", "severo"] }
        }
      }
    },
    "descripcion de la imagen":      { "type": "string" },
    "impresion":        { "type": "string" },
    "recomendaciones":  { "type": "array", "minItems": 1, "items": { "type": "string" } },
    "nota":             { "type": "string" },
    "modelo":           { "type": "string" },
    "confianza":        { "type": "number", "minimum": 0.0, "maximum": 1.0 },
  }
}

SYSTEM_PROMPT = """
Eres un radiólogo asistente experto en interpretación de imágenes médicas. Analiza estudios radiológicos y genera informes estructurados en español con precisión clínica.

## ROL Y ALCANCE
Actúas como apoyo al radiólogo humano. Tus análisis son orientativos y nunca reemplazan el criterio clínico ni el diagnóstico médico formal.

## IDIOMA
Responde exclusivamente en español. Usa terminología radiológica estándar: opacidad, consolidación, derrame pleural, atelectasia, silueta cardíaca, mediastino, etc.

## REGLAS DE CONTENIDO

**descripcion de la imagen**:
Breve descripción de la imagen proporcionada, no más de tres líneas.

**hallazgos:**
- Incluye todas las regiones anatómicas relevantes para el tipo de estudio.
- Si una región es normal: "Sin alteraciones significativas."
- Separa múltiples observaciones de una misma región con \n.
- severidad debe reflejar el hallazgo más relevante de esa región.

**impresion:**
- Resume los hallazgos más relevantes en lenguaje clínico conciso (1-3 oraciones).
- Indica siempre si el estudio es globalmente normal o presenta alteraciones.

**recomendaciones:**
- Solo incluye recomendaciones justificadas por los hallazgos (mínimo 1, máximo 5).
- Si el estudio es normal: "Correlación clínica." es suficiente.

**confianza:**
- Valor entre 0.0 y 1.0. Sé conservador ante hallazgos ambiguos o imagen de baja calidad.

## RESTRICCIONES
- Nunca afirmes diagnósticos definitivos; usa lenguaje como "compatible con", "sugestivo de", "no se puede descartar".
- nota siempre debe ser: "Resultado de modelo IA. Acudir siempre a un profesional para verificar el diagnóstico."
"""
ANALYSIS_TEMPLATE: str = textwrap.dedent("""\
    ## Contexto clínico
    {context}

    ---
    Proporciona un informe radiológico estructurado con los siguientes
    apartados, en este orden:

    1. **IMAGEN**
        Descripción breve de la imagen proporcionada, si no hay imagen debe ser "No se ha porporcionado imagen"

    1. **TIPO DE ESTUDIO**
       Modalidad, proyección/secuencia, región anatómica y calidad técnica
       (adecuada / limitada / no diagnóstica).

    2. **HALLAZGOS DESCRIPTIVOS**
       Describe de forma objetiva sólo si se presentan las características de anatómicas anormales y hallazgos patológicos de la imagen.

    3. **IMPRESIÓN DIAGNÓSTICA**
       Diagnósticos diferenciales ordenados por probabilidad.
       Indica grado de certeza: probable / posible / a descartar.

    4. **RECOMENDACIONES**
       Estudios complementarios, correlación clínica o seguimiento sugerido.

    5. **LIMITACIONES DEL ANÁLISIS**
       Factores que condicionan la interpretación (calidad, ausencia de
       estudios previos, falta de datos clínicos, etc.).
""")


# ─────────────────────────────────────────────
#  build_prompt() — Construye el prompt final
# ─────────────────────────────────────────────
def build_prompt(
    context: str,
) -> dict[str, str]:

    # SYSTEM prompt

    system_final = SYSTEM_PROMPT

    # USER Prompt
    prompt_final = ANALYSIS_TEMPLATE.format(
        context = context.strip() or "Sin contexto clínico aportado.",
    )

    return {
        "system": system_final,
        "prompt": prompt_final,
    }


# ─────────────────────────────────────────────
#  Uso de ejemplo
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import ollama, config

    payload = build_prompt(context="Varón 58 años. Disnea de esfuerzo. Fumador 30 paquetes/año.")

    stream = ollama.chat(
        model=config.MODEL_NAME,
        messages=[
            {"role": "system", "content": payload["system"]},
            {"role": "user", "content": payload["prompt"]},
        ],
        stream=True,
    )

    for chunk in stream:
        print(chunk["message"]["content"], end="", flush=True)

    print()