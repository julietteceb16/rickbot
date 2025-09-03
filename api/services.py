from typing import List, Dict, Tuple, Optional
from .storage_memory import InMemoryConversationStore, ConversationState

HISTORY_CAP = 10  # 5 messages per side

class ConversationNotFound(Exception):
    pass

class ConversationService:
    def __init__(self, store: InMemoryConversationStore, llms: Dict[str, object], default_provider: str = "gemini") -> None:
        self.store = store
        self.llms = llms
        self.default_provider = default_provider if default_provider in llms else next(iter(llms))
    

    def _bootstrap(self, opening_msg: str, provider: Optional[str]) -> Tuple[str, ConversationState]:
        prov = provider or self.default_provider
        if prov not in self.llms:
            raise ValueError(f"unsupported provider: {prov}")
        cid = self.store.new_id()
        state: ConversationState = {
            "topic": opening_msg,
            "stance": "pro",
            "provider":prov,
            "history": []
        }
        self.store.set(cid, state)
        return cid, state


    def handle(self, cid: Optional[str], user_msg: str, provider: Optional[str] = None) -> Tuple[str, List[Dict[str, str]]]:
        if cid is not None:
            state = self.store.get(cid)
            if not state:
                raise ConversationNotFound(cid)
        else:
            cid, state = self._bootstrap(user_msg, provider)

        llm = self.llms[state["provider"]]
        bot = llm.chat(topic=state["topic"], stance=state["stance"], history=state["history"], user_msg=user_msg)

        state["history"].extend([
            {"role": "user", "message": user_msg},
            {"role": "bot",  "message": bot},
        ])
        state["history"] = state["history"][-HISTORY_CAP:]
        self.store.set(cid, state)
        return cid, state["history"]
