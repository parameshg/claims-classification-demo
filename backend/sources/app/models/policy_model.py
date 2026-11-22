from pydantic import BaseModel


class PolicyModel(BaseModel):
    policy_id: int
    cover_type: str
    excess: float
    start_date: str
    end_date: str
    exclusions: list[str]
