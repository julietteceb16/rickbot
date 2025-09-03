import os
from fastapi import FastAPI, HTTPException, Header
from dotenv import load_dotenv

from api.schemas import ConversationIn, ConversationOut, MessageItem
from api.storage_memory import InMemoryConversationStore
from api.services import ConversationService, ConversationNotFound

load_dotenv()
app = FastAPI()

_store = InMemoryConversationStore()
_llms = {}

# Gemini
gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY")
if gemini_key:
    from api.llm_gemini import GeminiLLM  
    _llms["gemini"] = GeminiLLM(
        api_key=gemini_key,
        model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
    )

# OpenAI
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    from api.llm_openai import OpenAILLM  
    _llms["openai"] = OpenAILLM(
        api_key=openai_key,
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )

# DeepSeek
deepseek_key = os.getenv("DEEPSEEK_API_KEY")
if deepseek_key:
    from api.llm_deepseek import DeepSeekLLM  
    _llms["deepseek"] = DeepSeekLLM(
        api_key=deepseek_key,
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    )

if not _llms:
    raise RuntimeError("No LLM providers configured. Set GEMINI_API_KEY, OPENAI_API_KEY or DEEPSEEK_API_KEY.")

default_provider = os.getenv("DEFAULT_PROVIDER") or ("gemini" if "gemini" in _llms else next(iter(_llms)))
_service = ConversationService(store=_store, llms=_llms, default_provider=default_provider)

@app.post("/conversation", response_model=ConversationOut)
def conversation(
    payload: ConversationIn,
    x_llm_provider: str | None = Header(default=None, alias="X-LLM-Provider"),
    x_stance: str | None = Header(default=None, alias="X-Stance"),
):
    provider = None
    stance_hint = None

    if payload.conversation_id is None:
        if x_llm_provider:
            provider = x_llm_provider.strip().lower()

        if x_stance:
            s = x_stance.strip().lower()
            if s not in {"pro", "contra"}:
                raise HTTPException(status_code=400, detail="invalid stance; must be 'pro' or 'contra'")
            stance_hint = s

    try:
        cid, hist = _service.handle(
            payload.conversation_id,
            payload.message,
            provider=provider,
            stance=stance_hint,
        )
    except ConversationNotFound:
        raise HTTPException(status_code=404, detail="conversation not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ConversationOut(conversation_id=cid, message=[MessageItem(**m) for m in hist])

@app.get("/health")
def health():
    return {"status": "ok", "providers": list(_llms.keys()), "default": default_provider}

@app.get("/conversation/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: str):
    state = _store.get(conversation_id)
    if not state:
        raise HTTPException(status_code=404, detail="conversation not found")
    hist = state["history"][-10:]  
    return ConversationOut(conversation_id=conversation_id, message=[MessageItem(**m) for m in hist])
