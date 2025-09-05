from typing import List, Dict, Tuple, Optional
import re
from .storage_memory import InMemoryConversationStore, ConversationState

HISTORY_CAP = 10


class ConversationNotFound(Exception):
    pass

 

def _normalize_marker(text: str, stance: str) -> str:
    """
    Asegura que la respuesta empiece con [[STANCE:pro|contra]] y que
    coincida con la postura fija de la conversación.
    """
    t = (text or "").strip()

    # Fix if the wrong marker came from the model
    if re.match(r"^\s*\[\[STANCE\s*:\s*contra\]\]\s*", t, re.I) and stance == "pro":
        t = re.sub(r"^\s*\[\[STANCE\s*:\s*contra\]\]\s*", f"[[STANCE:{stance}]] ", t, flags=re.I)
        return t.strip()
    if re.match(r"^\s*\[\[STANCE\s*:\s*pro\]\]\s*", t, re.I) and stance == "contra":
        t = re.sub(r"^\s*\[\[STANCE\s*:\s*pro\]\]\s*", f"[[STANCE:{stance}]] ", t, flags=re.I)
        return t.strip()

     # Add it if missing
    if not re.match(r"^\s*\[\[STANCE\s*:\s*(pro|contra)\]\]\s*", t, re.I):
        t = f"[[STANCE:{stance}]] " + t

    return t.strip()


def _truncate_words(text: str, limit: int = 180) -> str:
    """Corta a 180 palabras máx (la regla del reto)."""
    words = (text or "").split()
    return " ".join(words[:limit]).strip()


def _opening_banner(topic: str, stance: str) -> str:
    """Banner informativo del primer turno (tema/postura)."""
    stance_word = "pro" if stance == "pro" else "contra"
    return f"Fixed topic: {topic}. Fixed stance: {stance_word}."


def _seems_english(text: str) -> bool:
    """
    Heurística simple para detectar si la salida parece inglés.
    No es perfecto, pero funciona para bloquear español accidental.
    """
    low = (text or "").lower()
    if re.search(r"[áéíóúñ¡¿]", low):
        return False
    es_hits = sum(w in low for w in [" el ", " la ", " los ", " las ", " que ", " de ", " y ", " en ", " por ", " para ", " con "])
    en_hits = sum(w in low for w in [" the ", " and ", " of ", " to ", " in ", " for ", " with ", " on "])
    return en_hits >= es_hits




class ConversationService:
    def __init__(self, store: InMemoryConversationStore, llms: Dict[str, object], default_provider: str = "gemini") -> None:
        self.store = store
        self.llms = llms
         # If the given default provider is invalid, pick the first available one
        self.default_provider = default_provider if default_provider in llms else next(iter(llms))

    def _bootstrap(self, opening_msg: str, provider: Optional[str], stance: Optional[str]) -> Tuple[str, ConversationState]:
        prov = provider or self.default_provider
        if prov not in self.llms:
            raise ValueError(f"unsupported provider: {prov}")
        st = stance if stance in {"pro", "contra"} else "pro"

        # First message defines the topic and stance
        cid = self.store.new_id()
        state: ConversationState = {
            "topic": opening_msg,   # el primer mensaje define el tema
            "stance": st,           # postura fija
            "provider": prov,       # proveedor fijo
            "history": []
        }
        self.store.set(cid, state)
        return cid, state

    def handle(
        self,
        cid: Optional[str],
        user_msg: str,
        provider: Optional[str] = None,
        stance: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, str]]]:

        if cid is not None:
            state = self.store.get(cid)
            if not state:
                raise ConversationNotFound(cid)
            first_turn = False
        else:
            cid, state = self._bootstrap(opening_msg=user_msg, provider=provider, stance=stance)
            first_turn = True

        llm = self.llms[state["provider"]]

        #Ask the LLM for a reply
        bot_raw = llm.chat(
            topic=state["topic"],
            stance=state["stance"],
            history=state["history"],
            user_msg=user_msg
        )

        #Normalize stance marker and enforce word limit
        bot_norm = _normalize_marker(bot_raw, state["stance"])
        bot_norm = _truncate_words(bot_norm, 180)

        # Ensure response is English, retry if needed
        if not _seems_english(bot_norm):
            hard_user_msg = (
                user_msg
                + "\n\nIMPORTANT: Answer ONLY in ENGLISH. "
                  f"Start with [[STANCE:{state['stance']}]], keep it under 180 words, "
                  "and do not change topic or stance."
            )
            bot_retry = llm.chat(
                topic=state["topic"],
                stance=state["stance"],
                history=state["history"],
                user_msg=hard_user_msg,
            )
            bot_norm = _normalize_marker(bot_retry, state["stance"])
            bot_norm = _truncate_words(bot_norm, 180)

            #  Fallback if still not English
            if not _seems_english(bot_norm):
                bot_norm = (
                    f"[[STANCE:{state['stance']}]] I must reply in English and keep the fixed stance on "
                    f"'{state['topic']}'. Could you share your strongest objection so I can address it directly?"
                )
                bot_norm = _truncate_words(bot_norm, 180)

        # Add banner only on the first turn
        if first_turn:
            banner = _opening_banner(state["topic"], state["stance"])
            if banner.lower() not in bot_norm.lower():
                bot_norm = re.sub(
                    r"^\s*\[\[STANCE:[^\]]+\]\]\s*",
                    lambda m: m.group(0) + " " + banner + " ",
                    bot_norm,
                )
            bot_norm = _truncate_words(bot_norm, 180)  # re-trunca por si creció

        #Save history (keep only last 10 entries)
        state["history"].extend([
            {"role": "user", "message": user_msg},
            {"role": "bot",  "message": bot_norm},
        ])
        state["history"] = state["history"][-HISTORY_CAP:]
        self.store.set(cid, state)

        return cid, state["history"]
