from __future__ import annotations
from typing import Iterator
import os
from sqlmodel import SQLModel, Session, create_engine


# Read from env, default to local SQLite similar to previous implementation
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./events.db")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)


def init_db() -> None:
    """Create database tables for all SQLModel models."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
