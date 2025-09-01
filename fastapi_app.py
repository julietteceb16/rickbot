import os
from fastapi import FastAPI

from api.schemas import ConversationIn, ConversationOut, MessageItem
from api.storage_memory import InMemoryConversationStore
from api.llm_dummy import DummyLLM
from api.llm_gemini import GeminiLLM
from api.services import ConversationService

app = FastAPI()

_store = InMemoryConversationStore()
api_key = os.environ.get("API_KEY")
if not api_key:
    raise RuntimeError("Missing environment variable: API_KEY")
_llm = GeminiLLM(api_key=api_key)
_service = ConversationService(store=_store, llm=_llm)



@app.post("/conversation", response_model=ConversationOut)
def conversation(payload: ConversationIn):
    cid, hist = _service.handle(payload.conversation_id, payload.message)
    return ConversationOut(
        conversation_id=cid,
        message=[MessageItem(**m) for m in hist]
    )

@app.get("/health")
def health():
    return {"status": "ok"}
