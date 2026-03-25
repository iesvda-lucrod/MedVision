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
