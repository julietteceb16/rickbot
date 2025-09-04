# api/persistence/models.py
from datetime import datetime
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, Text, DateTime

try:
    from sqlalchemy import JSON
except Exception:
    from sqlalchemy import Text as JSON  

from .db import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)

    topic: Mapped[str] = mapped_column(Text, nullable=False)
    stance: Mapped[str] = mapped_column(String(10), nullable=False)     
    provider: Mapped[str] = mapped_column(String(20), nullable=False)

    history: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
