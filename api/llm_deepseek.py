import os, re
from typing import List, Dict, Tuple
from openai import OpenAI

SYSTEM_TEMPLATE = (
    "Role: debate bot.\n"
    "Fixed topic: '{topic}'.\n"
    "Your FIXED stance: '{stance}'. NEVER change it.\n"
    "Mandatory rules:\n"
    "1) Always start with the exact line: [[STANCE:{stance}]]\n"
    "2) Consistently defend that stance in every turn.\n"
    "3) Be respectful and persuasive; use evidence, analogies, and questions.\n"
    "4) Max 180 words. Stay strictly on topic.\n"
    "Write the answer in Spanish."
)

GUARD_TEMPLATE = (
    "Critical guard: The stance marker MUST be exactly one of: [[STANCE:pro]] or [[STANCE:contra]]. "
    "Any other token (e.g., [[STANCE:st]]) is invalid and you must rewrite immediately."
)

def _strip_tag_and_check(text: str, stance: str) -> Tuple[str, bool]:
    t = (text or "").strip()
    m = re.match(r"\s*\[\[STANCE\s*:\s*([^\]]+)\]\]\s*", t, re.I)  
    declared = m.group(1).lower().strip() if m else None
    body = t[m.end():].lstrip() if m else t
    ok = declared in {"pro", "contra"} and declared == stance
    return body, ok

class DeepSeekLLM:
    def __init__(self, api_key: str, model: str = "deepseek-chat", base_url: str | None = None):
        base = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.client = OpenAI(api_key=api_key, base_url=base)
        self.model = model

    def chat(self, topic: str, stance: str, history: List[Dict[str, str]], user_msg: str) -> str:
        msgs = [
            {"role": "system", "content": SYSTEM_TEMPLATE.format(topic=topic, stance=stance)},
            {"role": "system", "content": GUARD_TEMPLATE},
        ]
        for m in history:
            role = "assistant" if m["role"] == "bot" else "user"
            msgs.append({"role": role, "content": m["message"]})
        msgs.append({"role": "user", "content": user_msg})

        body = ""
        for _ in range(2):  
            comp = self.client.chat.completions.create(
                model=self.model,
                messages=msgs,
                temperature=0.2,
                max_tokens=256,
                timeout=30,
            )
            text = (comp.choices[0].message.content or "").strip()
            body, ok = _strip_tag_and_check(text, stance)
            if ok:
                return body.strip()

            msgs.append({
                "role": "user",
                "content": (
                    f"Your previous reply used an invalid or wrong marker. "
                    f"Rewrite starting with [[STANCE:{stance}]] and keep it under 180 words, in Spanish."
                ),
            })

        return body.strip()
