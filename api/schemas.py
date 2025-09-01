from pydantic import BaseModel, Field
from typing import Literal, Optional, List

class ConversationIn(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(min_length=1)

class MessageItem(BaseModel):
    role: Literal["user", "bot"]
    message: str

class ConversationOut(BaseModel):
    conversation_id: str
    message: List[MessageItem]
