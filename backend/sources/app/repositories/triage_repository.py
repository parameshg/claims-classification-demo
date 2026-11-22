import json
import sqlite3
from models.triage_model import TriageModel

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

    def save(self, triage: TriageModel) -> None:
        """Insert or replace the triage result and its fraud flags for a claim."""
        injured = None if triage.injured is None else int(triage.injured)
        with self.link:  # one transaction: commits on success, rolls back on error
            # Deleting the row cascades to triage_fraud_flags (foreign_keys = ON).
            self.link.execute(
                "DELETE FROM triage_results WHERE claim_id = ?", (triage.claim_id,)
            )
            self.link.execute(
                f"INSERT INTO triage_results ({COLUMNS}) "
                f"VALUES ({', '.join('?' * 15)})",
                (
                    triage.claim_id,
                    triage.incident_date,
                    triage.incident_place,
                    triage.parties,
                    injured,
                    triage.description,
                    json.dumps(triage.missing_fields),
                    triage.claim_type,
                    triage.severity,
                    triage.confidence,
                    triage.coverage_outcome,
                    triage.coverage_reason,
                    triage.route,
                    triage.explanation,
                    triage.created_at,
                ),
            )
            self.link.executemany(
                "INSERT INTO triage_fraud_flags (claim_id, flag) VALUES (?, ?)",
                [(triage.claim_id, flag) for flag in set(triage.fraud_flags)],
            )
