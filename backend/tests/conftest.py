import sqlite3
from pathlib import Path
import pytest

from fastapi.testclient import TestClient

DB = Path(__file__).resolve().parents[2] / "database"

@pytest.fixture
def client(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    link = sqlite3.connect(path)
    link.executescript((DB / "schema.sql").read_text(encoding="utf-8"))
    link.executescript((DB / "seed.sql").read_text(encoding="utf-8"))
    link.close()
    monkeypatch.setenv("CLAIMS_DB", str(path))
    from app.main import app

    return TestClient(app)