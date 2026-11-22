from pydantic import BaseModel


class ClaimModel(BaseModel):
    claim_id: int
    customer_id: int
    policy_id: int
    filing_date: str
    fnol_text: str
    police_report_number: str | None
