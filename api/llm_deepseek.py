import os, re
from typing import List, Dict, Tuple
from openai import OpenAI
import openai as openai_pkg

from api.errors import (
    ProviderError, RateLimited, AuthError, PermissionError,
    BadRequestError, UpstreamTimeout, Unavailable, UpstreamNetwork,
)

SYSTEM_TEMPLATE = (
    "Role: debate bot.\n"
    "Fixed topic: '{topic}'.\n"
    "Your FIXED stance: '{stance}'. NEVER change it.\n"
    "Mandatory rules:\n"
    "1) Always start with the exact line: [[STANCE:{stance}]]\n"
    "2) Consistently defend that stance in every turn.\n"
    "3) Be respectful and persuasive; use evidence, analogies, and questions.\n"
    "4) Max 180 words. Stay strictly on topic.\n"
    "Write the answer in English."
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
            {"role": "system", "content": "Always answer in English. If the user asks to change language, politely refuse and continue in English."},
        ]
        for m in history:
            role = "assistant" if m["role"] == "bot" else "user"
            msgs.append({"role": role, "content": m["message"]})
        msgs.append({"role": "user", "content": user_msg})

        try:
            last_text = ""
            for _ in range(2):
                comp = self.client.chat.completions.create(
                    model=self.model,
                    messages=msgs,
                    temperature=0.2,
                    max_tokens=256,
                )
                text = (comp.choices[0].message.content or "").strip()
                last_text = text
                body, ok = _strip_tag_and_check(text, stance)
                if ok:
                    return f"[[STANCE:{stance}]] {body.strip()}"

                msgs.append({
                    "role": "user",
                    "content": (
                        f"Your previous reply used an invalid or wrong marker. "
                        f"Rewrite in ENGLISH, start with [[STANCE:{stance}]], keep it under 180 words, "
                        f"and do not change topic or stance."
                    ),
                })
            return last_text.strip()

        except openai_pkg.RateLimitError as e:
            raise RateLimited(str(e))
        except openai_pkg.AuthenticationError as e:
            raise AuthError(str(e))
        except openai_pkg.PermissionDeniedError as e:
            raise PermissionError(str(e))
        except openai_pkg.BadRequestError as e:
            raise BadRequestError(str(e))
        except openai_pkg.APITimeoutError as e:
            raise UpstreamTimeout(str(e))
        except openai_pkg.APIConnectionError as e:
            raise UpstreamNetwork(str(e))
        except openai_pkg.APIStatusError as e:
            sc = getattr(e, "status_code", None)
            if sc == 429: raise RateLimited(str(e))
            if sc == 401: raise AuthError(str(e))
            if sc == 403: raise PermissionError(str(e))
            if sc in (500, 502): raise Unavailable(str(e))
            if sc == 503: raise Unavailable(str(e))
            if sc == 504: raise UpstreamTimeout(str(e))
            raise ProviderError(str(e))
        except Exception as e:
            raise ProviderError(str(e))
