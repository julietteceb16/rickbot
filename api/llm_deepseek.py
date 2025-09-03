import os
from typing import List, Dict
from openai import OpenAI

SYSTEM_TEMPLATE = (
    "You are a debate bot. The topic is: '{topic}'. "
    "You MUST argue the '{stance}' side consistently and persuasively. "
    "Be civil, avoid insults, use evidence, analogies and questions. "
    "Keep each reply under 180 words. Stay strictly on topic."
)

class DeepSeekLLM:
    def __init__(self, api_key: str, model: str = "deepseek-chat", base_url: str | None = None):
        base = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.client = OpenAI(api_key=api_key, base_url=base)
        self.model = model

    def chat(self, topic: str, stance: str, history: List[Dict[str, str]], user_msg: str) -> str:
        msgs = [{"role": "system", "content": SYSTEM_TEMPLATE.format(topic=topic, stance=stance)}]
        for m in history:
            role = "assistant" if m["role"] == "bot" else "user"
            msgs.append({"role": role, "content": m["message"]})
        msgs.append({"role": "user", "content": user_msg})
        comp = self.client.chat.completions.create(model=self.model, messages=msgs, temperature=0.5, max_tokens=256)
        return comp.choices[0].message.content.strip()
