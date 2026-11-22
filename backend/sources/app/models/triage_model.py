from pydantic import BaseModel


class TriageModel(BaseModel):
    claim_id: int
    incident_date: str | None
    incident_place: str | None
    parties: str | None
    injured: bool | None
    description: str | None
    missing_fields: list[str]
    claim_type: str | None
    severity: str | None
    confidence: float | None
    coverage_outcome: str | None
    coverage_reason: str | None
    fraud_flags: list[str]
    route: str
    explanation: str
    created_at: str
