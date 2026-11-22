import os
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[3] / "database" / "claims.db"

def db_path() -> str:
    return os.environ.get("CLAIMS_DB", str(DEFAULT_DB))