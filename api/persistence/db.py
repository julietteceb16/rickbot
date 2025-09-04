import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base

DB_URL = os.getenv("DB_URL", "sqlite:///./conversations.db")

connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
engine = create_engine(
    DB_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True))
Base = declarative_base()
