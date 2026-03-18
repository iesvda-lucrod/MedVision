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
    ## Imagen a analizar
    {image}

    ## Contexto clínico
    {context}

    ---
    Proporciona un informe radiológico estructurado con los siguientes
    apartados, en este orden:

    1. **TIPO DE ESTUDIO**
       Modalidad, proyección/secuencia, región anatómica y calidad técnica
       (adecuada / limitada / no diagnóstica).

    2. **HALLAZGOS DESCRIPTIVOS**
       Descripción objetiva y sistemática: localización, densidad o señal,
       morfología, bordes, tamaño estimado (si aplicable).
       Distingue: hallazgos normales · variantes anatómicas · hallazgos patológicos.

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
    """Parámetros opcionales para personalizar el análisis."""
    especialidad: str = "radiología general"
    urgente: bool = False
    estudios_previos: bool = False
    notas_extra: Optional[str] = None
    etiquetas_adicionales: list[str] = field(default_factory=list)


# ─────────────────────────────────────────────
#  build_prompt() — Construye el prompt final
# ─────────────────────────────────────────────
def build_prompt(
    context: str,
    image: str = "[imagen adjunta]",
    config: Optional[RadiologiaConfig] = None,
) -> dict[str, str]:
    """
    Construye el payload de prompt listo para Ollama / API.

    Args:
        context:  Contexto clínico aportado por el profesional.
                  Ej: "Varón 62 años, disnea progresiva, febre 38.5°C"
        image:    Descripción de la imagen o ruta/URL de referencia.
                  Si se envía como archivo, mantener "[imagen adjunta]".
        config:   Ajustes opcionales (especialidad, urgencia, etc.).

    Returns:
        dict con claves 'system' y 'prompt', listos para pasar a Ollama.
    """
    cfg = config or RadiologiaConfig()

    # Construir system prompt enriquecido con config
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

    # Rellenar template con image y context
    prompt_final = ANALYSIS_TEMPLATE.format(
        image=image.strip() or "[imagen adjunta]",
        context=context.strip() or "Sin contexto clínico aportado.",
    )

    return {
        "system": system_final,
        "prompt": prompt_final,
    }


# ─────────────────────────────────────────────
#  Uso de ejemplo
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import json, ollama

    payload = build_prompt(
        context="Varón 58 años. Disnea de esfuerzo. Fumador 30 paquetes/año.",
        image="[imagen adjunta]",
        config=RadiologiaConfig(urgente=False, estudios_previos=False),
    )

    response = ollama.generate(
        model="qwen2.5vl",
        system=payload["system"],
        prompt=payload["prompt"],
        images=["rx_torax.jpg"],
    )

    print(response["response"])