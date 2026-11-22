from pydantic import BaseModel

from app.models.claim_model import ClaimModel
from app.models.history_model import HistoryModel
from app.models.policy_model import PolicyModel


class DetailModel(BaseModel):
    claim: ClaimModel
    policy: PolicyModel
    history: list[HistoryModel]
