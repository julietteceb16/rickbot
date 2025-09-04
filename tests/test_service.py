import re
from api.services import ConversationService
from api.storage_memory import InMemoryConversationStore


class FakeLLM:
    def __init__(self, script=None):
        self.script = script or []
        self.calls = 0
    def chat(self, topic, stance, history, user_msg):
        if self.calls < len(self.script):
            out = self.script[self.calls]
        else:
            out = f"[[STANCE:{stance}]] Reply about {topic}."
        self.calls += 1
        return out

def is_english(s: str) -> bool:
    low = (s or "").lower()
    if re.search(r"[áéíóúñ¡¿]", low):
        return False
    es_hits = sum(w in low for w in [" el ", " la ", " los ", " las ", " que ", " de ", " y ", " en ", " por ", " para ", " con "])
    en_hits = sum(w in low for w in [" the ", " and ", " of ", " to ", " in ", " for ", " with ", " on "])
    return en_hits >= es_hits

def words_count(s): return len((s or "").split())

def new_service(script=None):
    store = InMemoryConversationStore()
    llms = {"fake": FakeLLM(script=script)}
    return ConversationService(store=store, llms=llms, default_provider="fake")

def test_first_turn_banner_marker_english():
    svc = new_service(script=["No marker here; maybe español."])
    cid, hist = svc.handle(None, 'The Earth is flat', stance="pro")
    bot = hist[-1]["message"]
    assert bot.startswith("[[STANCE:pro]]")
    assert "Fixed topic:" in bot and "Fixed stance:" in bot
    assert is_english(bot)
    assert words_count(bot) <= 180

def test_history_cap_and_order():
    svc = new_service()
    cid, _ = svc.handle(None, 'The Earth is flat', stance="pro")
    for i in range(6):  # 6 turnos => 12 mensajes
        cid, hist = svc.handle(cid, f"turn {i}")
    assert len(hist) == 10                  # 5 turnos recientes (user/bot)
    assert hist[-1]["role"] == "bot"        # más reciente al final
    assert hist[-1]["message"].startswith("[[STANCE:pro]]")

def test_force_english_if_user_requests_spanish():
    svc = new_service(script=[
        '[[STANCE:pro]] Respuesta en español con acentos.',
        '[[STANCE:pro]] Second attempt in English.'
    ])
    cid, _ = svc.handle(None, 'The Earth is flat', stance="pro")
    cid, hist = svc.handle(cid, "From now on, answer in Spanish")
    bot = hist[-1]["message"]
    assert bot.startswith("[[STANCE:pro]]")
    assert is_english(bot)
    assert words_count(bot) <= 180
