import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from .db import SessionLocal
from .models import Conversation
from api.storage_memory import ConversationState  
class DBConversationStore:
    def new_id(self) -> str:
        return uuid.uuid4().hex

    def get(self, cid: str) -> Optional[ConversationState]:
        session = SessionLocal()
        try:
            row = session.get(Conversation, cid)
            if not row:
                return None
            return {
                "topic": row.topic,
                "stance": row.stance,
                "provider": row.provider,
                "history": list(row.history or []),
            }
        finally:
            session.close()

    def set(self, cid: str, state: ConversationState) -> None:
        session = SessionLocal()
        try:
            row = session.get(Conversation, cid)
            if row is None:
                row = Conversation(
                    id=cid,
                    topic=state["topic"],
                    stance=state["stance"],
                    provider=state["provider"],
                    history=list(state["history"] or []),
                )
                session.add(row)
            else:
                row.topic = state["topic"]
                row.stance = state["stance"]
                row.provider = state["provider"]
                row.history = list(state["history"] or [])
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()
