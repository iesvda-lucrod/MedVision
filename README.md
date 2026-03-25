# RayAI

Aplicación de escritorio para el análisis asistido por IA de radiografías médicas. Combina un modelo de visión local (vía Ollama) con una interfaz gráfica en PySide6 para generar informes radiológicos estructurados en español.

**Aviso clínico:** Los resultados generados por RayAI son orientativos y nunca reemplazan el criterio de un profesional médico cualificado.

---

## Características

- Carga de imágenes por explorador de archivos o arrastrar y soltar (drag & drop)
- Preprocesado automático de imágenes: escala de grises + ecualización CLAHE
- Generación de informes en JSON estructurado con hallazgos, impresión clínica, recomendaciones y nivel de confianza
- Prompt de análisis editable directamente desde la interfaz
- Panel de resultados integrado en la propia ventana
- Compatible con modelos de visión locales a través de Ollama

---

## Estructura del proyecto

```
RayAI/
├── main.py                    # Punto de entrada de la aplicación
├── requirements.txt           # Dependencias Python
│
├── core/
│   ├── llm_client.py          # Cliente del modelo (Ollama)
│   ├── image_processor.py     # Preprocesado de imágenes con OpenCV
│   └── test.py
│
├── models/
│   ├── config.py              # Configuración del modelo y parámetros
│   ├── prompts.py             # System prompt, plantilla de usuario y schema JSON
│   └── test.py
│
├── ui/
│   ├── main_window.py         # Ventana principal de la aplicación
│   ├── image_panel.py         # Panel de carga y visualización de radiografías
│   ├── prompt_panel.py        # Editor de prompt personalizable
│   └── results_panel.py       # Visualización de resultados del informe
│
├── tests/
│   ├── main_test_pipeline.py  # Pipeline principal de tests
│   ├── test_image_processor.py
│   ├── test_prompt_building.py
│   └── test_llm_client.py
│
└── assets/
    └── imagen_test.webp       # Imagen de prueba
```

---

## Requisitos previos

- Python 3.10 o superior
- [Ollama](https://ollama.com/) instalado y en ejecución en `http://localhost:11434`
- Modelo de visión descargado (por defecto `qwen2.5vl:latest`)

```bash
ollama pull qwen2.5vl:latest
```

---

## Instalación

```bash
# Clonar el repositorio
git clone <url-del-repositorio>
cd RayAI

# Instalar dependencias
pip install -r requirements.txt
```

---

## Uso

```bash
python main.py
```

Al arrancar la aplicación:

1. **Cargar imagen** — Haz clic en "Cargar imagen" o arrastra un archivo directamente al panel izquierdo. Se aceptan `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff` y `.webp`.
2. **Ajustar el prompt** (opcional) — Edita el prompt de análisis en el panel central y pulsa "Aplicar prompt".
3. **Analizar** — Inicia el análisis. El modelo procesará la imagen y devolverá un informe estructurado.
4. **Ver resultados** — El panel de resultados mostrará hallazgos, impresión clínica, recomendaciones y nivel de confianza.

---

## Configuración

Edita `models/config.py` para ajustar el comportamiento del modelo:

| Parámetro    | Valor por defecto          | Descripción                              |
|--------------|----------------------------|------------------------------------------|
| `OLLAMA_URL` | `http://localhost:11434`   | Endpoint del servidor Ollama             |
| `MODEL_NAME` | `qwen2.5vl:latest`         | Modelo de visión a utilizar              |
| `TEMPERATURE`| `0.2`                      | Determinismo de las respuestas (0–1)     |
| `NUM_CTX`    | `4096`                     | Tamaño de la ventana de contexto         |
| `TIMEOUT`    | `120`                      | Tiempo máximo de inferencia en segundos  |

---

## Formato del informe

El modelo devuelve un objeto JSON con los siguientes campos:

```json
{
  "paciente": { "nombre": "...", "edad": "...", "estudio": "..." },
  "descripcion_imagen": "...",
  "hallazgos": [
    { "region": "...", "descripcion": "...", "severidad": "leve|moderado|severo|normal" }
  ],
  "impresion": "...",
  "recomendaciones": ["..."],
  "limitaciones": ["..."],
  "confianza": 0.85,
  "modelo": "qwen2.5vl:latest",
  "nota": "Resultado de modelo IA. Acudir siempre a un profesional para verificar el diagnóstico."
}
```

---

## Dependencias principales

| Paquete          | Uso                                      |
|------------------|------------------------------------------|
| `PySide6`        | Interfaz gráfica                         |
| `opencv-python`  | Preprocesado de imágenes                 |
| `ollama`         | Cliente para modelos locales             |
| `llama-index`    | Utilidades de indexación y contexto      |
| `pandas`         | Manejo de datos                          |
| `matplotlib`     | Visualización                            |
| `reportlab`      | Generación de informes en PDF            |

---