import uuid
from typing import Dict, List, Optional, TypedDict

class ConversationState(TypedDict):
    topic: str
    stance: str 
    provider: str
    history: List[Dict]

class InMemoryConversationStore:
    def __init__(self) -> None:
        self._db: Dict[str, ConversationState] = {}

    def new_id(self) -> str:
        return uuid.uuid4().hex

    def get(self, cid: str) -> Optional[ConversationState]:
        return self._db.get(cid)

    def set(self, cid: str, state: ConversationState) -> None:
        self._db[cid] = state
