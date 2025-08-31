from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class ConversationIn(BaseModel):
    conversation_id: Optional[str] = None
    message: str

@app.post("/conversation")
def conversation(_payload: ConversationIn):
    return {"message": "hello world"}

@app.get("/health")
def health():
    return {"status": "ok"}
