from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import textwrap

SYSTEM_PROMPT: str = textwrap.dedent("""\
    Eres un radiólogo asistente especializado en el análisis de imágenes
    médicas y radiológicas. Tu función es apoyar a profesionales de la salud
    —médicos, radiólogos y residentes— con descripciones estructuradas,
    hallazgos preliminares y orientación diagnóstica.

    IDIOMA: Responde siempre en español (castellano), empleando terminología
    radiológica estándar. Si el profesional escribe en otro idioma, adáptate.

    ROL Y LÍMITES:
    - Eres una herramienta de apoyo clínico, NO un diagnóstico definitivo.
    - Nunca recomiendes tratamientos farmacológicos específicos.
    - Siempre indica la necesidad de correlación clínico-radiológica.
    - Si detectas un hallazgo crítico o urgente, indícalo AL INICIO con:
      [HALLAZGO CRÍTICO — REQUIERE EVALUACIÓN MÉDICA INMEDIATA]

    CAPACIDADES:
    - Radiografías (RX): tórax, columna, extremidades, abdomen, cráneo.
    - Tomografía computarizada (TC/CT): todos los segmentos, con/sin contraste.
    - Resonancia magnética (RM): secuencias T1, T2, FLAIR, DWI, gadolinio.
    - Ecografía, mamografía, densitometría ósea, medicina nuclear.
    - Imágenes endoscópicas e histopatológicas.

    TONO: Profesional, preciso y conciso. Usa viñetas para listas de hallazgos
    y numeración para diagnósticos diferenciales ordenados por probabilidad.\
""")

ANALYSIS_TEMPLATE: str = textwrap.dedent("""\
    ## Contexto clínico
    {context}

    ---
    Proporciona un informe radiológico estructurado con los siguientes
    apartados, en este orden:

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


@dataclass
class RadiologiaConfig:
    especialidad: str = "radiología general"
    urgente: bool = False
    estudios_previos: bool = False
    notas_extra: Optional[str] = None


# ─────────────────────────────────────────────
#  build_prompt() — Construye el prompt final
# ─────────────────────────────────────────────
def build_prompt(
    context: str,
    radio_config: RadiologiaConfig = None,
) -> dict[str, str]:

    # SYSTEM prompt
    cfg = radio_config or RadiologiaConfig()

    system_parts = [SYSTEM_PROMPT]

    if cfg.especialidad != "radiología general":
        system_parts.append(
            f"\nESPECIALIDAD ACTIVA: {cfg.especialidad}. "
            "Adapta el análisis a esta subespecialidad."
        )

    if cfg.urgente:
        system_parts.append(
            "\nMODO URGENTE: Resume hallazgos críticos en las primeras "
            "3 líneas antes del informe completo."
        )

    if not cfg.estudios_previos:
        system_parts.append(
            "\nNOTA: No hay estudios previos disponibles para comparación."
        )

    if cfg.notas_extra:
        system_parts.append(f"\nINSTRUCCIONES ADICIONALES:\n{cfg.notas_extra}")

    system_final = "\n".join(system_parts)

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

    payload = build_prompt(
        context="Varón 58 años. Disnea de esfuerzo. Fumador 30 paquetes/año.",
        radio_config=RadiologiaConfig(urgente=False, estudios_previos=False),
    )

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