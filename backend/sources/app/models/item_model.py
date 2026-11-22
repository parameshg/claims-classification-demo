from pydantic import BaseModel


class ItemModel(BaseModel):
    claim_id: int
    customer_id: int
    filing_date: str
    claim_type: str | None
    severity: str | None
    route: str | None
