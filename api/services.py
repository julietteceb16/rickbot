from typing import List, Dict, Tuple, Optional
from .storage_memory import InMemoryConversationStore, ConversationState
import re

HISTORY_CAP = 10

class ConversationNotFound(Exception):
    pass


def _normalize_marker(text: str, stance: str) -> str:
    t = (text or "").strip()
    if re.match(r"^\s*\[\[STANCE\s*:\s*contra\]\]\s*", t, re.I) and stance == "pro":
        t = re.sub(r"^\s*\[\[STANCE\s*:\s*contra\]\]\s*", f"[[STANCE:{stance}]] ", t, flags=re.I)
        return t.strip()
    if re.match(r"^\s*\[\[STANCE\s*:\s*pro\]\]\s*", t, re.I) and stance == "contra":
        t = re.sub(r"^\s*\[\[STANCE\s*:\s*pro\]\]\s*", f"[[STANCE:{stance}]] ", t, flags=re.I)
        return t.strip()
    if not re.match(r"^\s*\[\[STANCE\s*:\s*(pro|contra)\]\]\s*", t, re.I):
        t = f"[[STANCE:{stance}]] " + t
    return t.strip()

def _truncate_words(text: str, limit: int = 180) -> str:
    words = (text or "").split()
    return " ".join(words[:limit]).strip()

def _opening_banner(topic: str, stance: str) -> str:
    stance_word = "pro" if stance == "pro" else "contra"
    return f"Fixed topic: {topic}. Fixed stance: {stance_word}."

class ConversationService:
    def __init__(self, store: InMemoryConversationStore, llms: Dict[str, object], default_provider: str = "gemini") -> None:
        self.store = store
        self.llms = llms
        self.default_provider = default_provider if default_provider in llms else next(iter(llms))

    def _bootstrap(self, opening_msg: str, provider: Optional[str], stance: Optional[str]) -> Tuple[str, ConversationState]:
        prov = provider or self.default_provider
        if prov not in self.llms:
            raise ValueError(f"unsupported provider: {prov}")
        st = stance if stance in {"pro","contra"} else "pro"
        cid = self.store.new_id()
        state: ConversationState = {
            "topic": opening_msg,
            "stance": st,
            "provider": prov,
            "history": []
        }
        self.store.set(cid, state)
        return cid, state

    def handle(self, cid: Optional[str], user_msg: str, provider: Optional[str] = None, stance: Optional[str] = None) -> Tuple[str, List[Dict[str, str]]]:
        if cid is not None:
            state = self.store.get(cid)
            if not state:
                raise ConversationNotFound(cid)
            first_turn = False
        else:
            cid, state = self._bootstrap(opening_msg=user_msg, provider=provider, stance=stance)
            first_turn = True

        llm = self.llms[state["provider"]]
        bot_raw = llm.chat(topic=state["topic"], stance=state["stance"], history=state["history"], user_msg=user_msg)

        
        bot_norm = _normalize_marker(bot_raw, state["stance"])
        bot_norm = _truncate_words(bot_norm, 180)

        if first_turn:
            banner = _opening_banner(state["topic"], state["stance"])
            if banner.lower() not in bot_norm.lower():
                bot_norm = re.sub(r"^\s*\[\[STANCE:[^\]]+\]\]\s*", lambda m: m.group(0) + " " + banner + " ", bot_norm)

        state["history"].extend([
            {"role": "user", "message": user_msg},
            {"role": "bot",  "message": bot_norm},
        ])
        state["history"] = state["history"][-HISTORY_CAP:]
        self.store.set(cid, state)
        return cid, state["history"]
