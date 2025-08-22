"""Database helpers using SQLAlchemy."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DB_PATH = os.getenv("TRADER_DB", "trader.sqlite")
engine = create_engine(f"sqlite:///{DB_PATH}", future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session() -> Generator[Session, None, None]:
    """Yield a new session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


__all__ = ["engine", "get_session"]
