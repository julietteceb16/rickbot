from typing import List, Dict

class DummyLLM:
    def chat(self, topic: str, stance: str, history: List[Dict[str, str]], user_msg: str) -> str:
        return (
            f"I’m firmly {stance} on “{topic}.” "
            f"Consider this: {user_msg} — but the evidence and logic still "
            f"support my side. What part would you challenge specifically?"
        )
