import sqlite3
from collections.abc import Iterator
from app.config import db_path

def connection() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency: one connection per request."""
    link = sqlite3.connect(db_path(), check_same_thread=False)
    link.row_factory = sqlite3.Row
    link.execute("PRAGMA foreign_keys = ON")
    try:
        yield link
    finally:
        link.close()