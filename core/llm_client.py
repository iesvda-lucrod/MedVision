from models.prompts import build_prompt, FORMAT
from models import config
from core import image_processor
import ollama
import re
import time
import json

class LLMClient:
    def __init__(self):
        self.model = config.MODEL_NAME
    
    def predict(self,
        context: str,
        image_path: str = None,
        stream: bool = False,
    ) -> str:

        image_b64 = image_processor.preprocess_image(image_path)['base64'] if image_path else None
        
        payload = build_prompt(context=context)

        user_content = {"role": "user",   "content": payload["prompt"]}
        if image_b64 is not None:
            user_content['images'] = [image_b64]

        t_start = time.perf_counter()

        print("Analizando...", "prompt: ")
        print(user_content["content"])
        response = ollama.chat(
            model=self.model,
            stream=stream,
            options = {
                "temperature": config.TEMPERATURE,
                "num_ctx":     config.NUM_CTX,
            },
            messages=[
                {"role": "system", "content": payload["system"]},
                user_content
            ],
            format = FORMAT,
        )
        print("2")

        if stream:
            full_response = ""
            for chunk in response:
                content = chunk.message.content
                print(content, end="", flush=True)
                full_response += content
            raw = full_response
        else:
            raw = response.message.content

        inference_time = time.perf_counter() - t_start
        result = json.loads(raw)
        return result

        
    def _parse_response(self, raw: str, inference_time: float = 0.0) -> dict:
        """
        Extrae hallazgos del texto crudo del modelo.

        Estrategia:
        1. Busca una sección etiquetada como 'hallazgos' / 'findings' (case-insensitive).
        2. Si no existe, trata todo el texto como hallazgo único.
        3. Normaliza cada hallazgo eliminando viñetas, numeración y espacios extra.

        Retorna:
            {
                "findings":       list[str],   # lista de hallazgos individuales
                "inference_time": float,        # segundos de inferencia
                "model":          str,          # nombre del modelo usado
            }
        """
        findings: list[str] = []

        # --- 1. Intentar extraer bloque de hallazgos estructurado ---
        section_pattern = re.compile(
            r"(?:hallazgos?|findings?)\s*[:\-]?\s*\n(.*?)(?=\n[A-ZÁÉÍÓÚÑ]{2,}|\Z)",
            re.IGNORECASE | re.DOTALL,
        )
        match = section_pattern.search(raw)
        block = match.group(1) if match else raw

        # --- 2. Partir en líneas / ítems ---
        # Soporta viñetas (-, *, •), numeración (1. / 1)) y líneas planas
        item_pattern = re.compile(r"^[\s\-\*\•]*(?:\d+[\.\)]?\s+)?(.+)", re.MULTILINE)
        candidates = item_pattern.findall(block)

        for item in candidates:
            clean = item.strip()
            if clean:
                findings.append(clean)

        # Fallback: si todo quedó vacío, devolver el texto completo como un hallazgo
        if not findings:
            stripped = raw.strip()
            if stripped:
                findings = [stripped]

        return {
            "findings": findings,
            "inference_time": round(inference_time, 3),
            "model": self.model,
        }