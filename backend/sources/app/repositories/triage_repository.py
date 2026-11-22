import json
import sqlite3
from app.models.triage_model import TriageModel

COLUMNS = (
    "claim_id, incident_date, incident_place, parties, injured, description, "
    "missing_fields, claim_type, severity, confidence, coverage_outcome, "
    "coverage_reason, route, explanation, created_at"
)

class TriageRepository:
    def __init__(self, link: sqlite3.Connection) -> None:
        self.link = link

    def get(self, claim_id: int) -> TriageModel | None:
        row = self.link.execute(
            f"SELECT {COLUMNS} FROM triage_results WHERE claim_id = ?", (claim_id,)
        ).fetchone()
        if row is None:
            return None
        flags = self.link.execute(
            "SELECT flag FROM triage_fraud_flags WHERE claim_id = ? ORDER BY flag",
            (claim_id,),
        ).fetchall()
        data = dict(row)
        data["injured"] = None if data["injured"] is None else bool(data["injured"])
        data["missing_fields"] = json.loads(data["missing_fields"])
        return TriageModel(**data, fraud_flags=[f["flag"] for f in flags])
