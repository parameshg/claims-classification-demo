from datetime import date

from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ClaimNewModel(BaseModel):
    customer_id: int
    policy_id: int
    filing_date: date
    fnol_text: Text
    police_report_number: str | None = Field(default=None)
