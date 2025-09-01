from typing import List, Dict, Tuple
from .storage_memory import InMemoryConversationStore, ConversationState

HISTORY_CAP = 10  # 5 messages per side

class ConversationService:
    def __init__(self, store: InMemoryConversationStore, llm) -> None:
        self.store = store
        self.llm = llm

    def _bootstrap(self, opening_msg: str) -> Tuple[str, ConversationState]:
        cid = self.store.new_id()
        state: ConversationState = {
            "topic": opening_msg,
            "stance": "pro",
            "history": []
        }
        self.store.set(cid, state)
        return cid, state

    def handle(self, cid: str | None, user_msg: str) -> Tuple[str, List[Dict[str, str]]]:
        if cid:
            state = self.store.get(cid)
            if not state:
                # Deberia devolver 404 si no existe
                cid, state = self._bootstrap(user_msg)
        else:
            cid, state = self._bootstrap(user_msg)

        bot = self.llm.chat(
            topic=state["topic"],
            stance=state["stance"],
            history=state["history"],
            user_msg=user_msg
        )

        state["history"].append({"role": "user", "message": user_msg})
        state["history"].append({"role": "bot",  "message": bot})
        state["history"] = state["history"][-HISTORY_CAP:]
        self.store.set(cid, state)

        return cid, state["history"]
