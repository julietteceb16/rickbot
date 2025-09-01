# api/llm_gemini.py
from typing import List, Dict
import google.generativeai as genai

SYSTEM_TEMPLATE = (
    "You are a debate bot. The topic is: '{topic}'. "
    "You MUST argue the '{stance}' side consistently and persuasively. "
    "Be civil, avoid insults, use evidence, analogies and questions. "
    "Keep each reply under 180 words. Stay strictly on topic."
)

class GeminiLLM:
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def chat(self, topic: str, stance: str, history: List[Dict[str, str]], user_msg: str) -> str:
        system = SYSTEM_TEMPLATE.format(topic=topic, stance=stance)

        contents = [{"role": "user", "parts": [system]}]
        for m in history:
            role = "model" if m["role"] == "bot" else "user"
            contents.append({"role": role, "parts": [m["message"]]})
        contents.append({"role": "user", "parts": [user_msg]})

        resp = self.model.generate_content(
            contents,
            generation_config=genai.GenerationConfig(
                temperature=0.5,
                max_output_tokens=256,
            ),
        )
        return (resp.text or "").strip()
