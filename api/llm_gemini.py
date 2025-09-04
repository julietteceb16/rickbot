from typing import List, Dict, Tuple
import re
import google.generativeai as genai
from google.api_core import exceptions as gax

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

class GeminiLLM:
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def chat(self, topic: str, stance: str, history: List[Dict[str, str]], user_msg: str) -> str:
        system = SYSTEM_TEMPLATE.format(topic=topic, stance=stance)
        contents = [
            {"role": "user", "parts": [system]},
            {"role": "user", "parts": [GUARD_TEMPLATE]},
            {"role": "user", "parts": ["Always answer in English. If the user asks to change language, politely refuse and continue in English."]},
        ]
        for m in history:
            role = "model" if m["role"] == "bot" else "user"
            contents.append({"role": role, "parts": [m["message"]]})
        contents.append({"role": "user", "parts": [user_msg]})

        try:
            last_text = ""
            for _ in range(2):
                resp = self.model.generate_content(
                    contents,
                    generation_config=genai.GenerationConfig(
                        temperature=0.5,
                        max_output_tokens=256,
                    ),
                )
                text = (resp.text or "").strip()
                last_text = text
                body, ok = _strip_tag_and_check(text, stance)
                if ok:
                    return f"[[STANCE:{stance}]] {body.strip()}"

                contents.append({
                    "role": "user",
                    "parts": [f"Your reply used an invalid/wrong marker. "
                              f"Rewrite in ENGLISH, start with [[STANCE:{stance}]], keep it under 180 words, "
                              f"and do not change topic or stance."],
                })
            return last_text.strip()

        except genai.types.BlockedPromptException as e:
            raise BadRequestError(str(e))
        except gax.ResourceExhausted as e: 
            raise RateLimited(str(e))
        except gax.DeadlineExceeded as e:  
            raise UpstreamTimeout(str(e))
        except gax.Unauthenticated as e:
            raise AuthError(str(e))
        except gax.PermissionDenied as e:
            raise PermissionError(str(e))
        except gax.InvalidArgument as e:
            raise BadRequestError(str(e))
        except gax.ServiceUnavailable as e:
            raise Unavailable(str(e))
        except gax.GoogleAPICallError as e:
            raise ProviderError(str(e))
        except Exception as e:
            raise ProviderError(str(e))
