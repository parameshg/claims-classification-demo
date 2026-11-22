from pydantic import BaseModel, Field

class ExtractModel(BaseModel):
    incident_date: str | None = Field(None, description="Date of the incident as YYYY-MM-DD. Null when not stated.")
    incident_place: str | None = Field(None, description="Where the incident happened. Null when not stated.")
    parties: str | None = Field(None, description="Other people, vehicles or organisations involved. Null when none or not stated.")
    injured: bool | None = Field(None, description="True if anyone was injured, false if the text says no one was. Null when not stated.")
    description: str | None = Field(None, description="One or two sentence factual summary of what happened. Null when the text has no usable account.")
