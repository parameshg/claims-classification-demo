from pydantic import BaseModel


class HistoryModel(BaseModel):
    history_id: int
    filing_date: str
    claim_type: str
