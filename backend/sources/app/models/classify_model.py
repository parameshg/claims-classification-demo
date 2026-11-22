from typing import Literal
from pydantic import BaseModel, Field

class ClassifyModel(BaseModel):
    claim_type: Literal["Collision", "Theft", "Glass", "Weather", "Vandalism"] | None = Field(None, description="Null when the FNOL text does not make the type clear.")
    severity: Literal["Low", "Medium", "High"] | None = Field(None, description="Null when claim_type is null.")
    confidence: float = Field(..., ge=0, le=1)