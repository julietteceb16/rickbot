from typing import List, Dict, Tuple, Optional
from .storage_memory import InMemoryConversationStore, ConversationState
import re


HISTORY_CAP = 10 

class ConversationNotFound(Exception):
    pass


def _expected_thesis(topic: str, stance: str) -> str:
    return f"Tesis: Estoy a favor de {topic}." if stance == "pro" else f"Tesis: Estoy en contra de {topic}."

def _strip_marker(text: str) -> str:
    t = (text or "").strip()
    m = re.match(r"\s*\[\[STANCE\s*:\s*[^\]]+\]\]\s*", t, re.I)
    return t[m.end():].lstrip() if m else t

def _ensure_thesis(text: str, topic: str, stance: str) -> str:
    body = _strip_marker(text)
    expected = _expected_thesis(topic, stance)
    if re.match(rf"^\s*{re.escape(expected)}", body, re.IGNORECASE):
        return body.strip()
    return f"{expected}\n{body.strip()}"

class ConversationService:
    def __init__(self, store: InMemoryConversationStore, llms: Dict[str, object], default_provider: str = "gemini") -> None:
        self.store = store
        self.llms = llms
        self.default_provider = default_provider if default_provider in llms else next(iter(llms))
    

    def _bootstrap(self, opening_msg: str, provider: Optional[str],stance: Optional[str]) -> Tuple[str, ConversationState]:
        prov = provider or self.default_provider
        if prov not in self.llms:
            raise ValueError(f"unsupported provider: {prov}")
        st = stance if stance in {"pro","contra"} else "pro"
        cid = self.store.new_id()
        state: ConversationState = {
            "topic": opening_msg,
            "stance": st,
            "provider":prov,
            "history": []
        }
        self.store.set(cid, state)
        return cid, state


    def handle(self, cid: Optional[str], user_msg: str, provider: Optional[str] = None, stance: Optional[str] = None) -> Tuple[str, List[Dict[str, str]]]:
        if cid is not None:
            state = self.store.get(cid)
            if not state:
                raise ConversationNotFound(cid)
        else:
            cid, state = self._bootstrap(opening_msg=user_msg, provider=provider, stance=stance)

        llm = self.llms[state["provider"]]
        bot_raw = llm.chat(topic=state["topic"], stance=state["stance"], history=state["history"], user_msg=user_msg)
        bot = _strip_marker(bot_raw)

        state["history"].extend([
            {"role": "user", "message": user_msg},
            {"role": "bot",  "message": bot},
        ])
        state["history"] = state["history"][-HISTORY_CAP:]
        self.store.set(cid, state)
        return cid, state["history"]
