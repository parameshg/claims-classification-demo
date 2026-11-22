from pydantic import BaseModel
from models.claim_model import ClaimModel
from models.history_model import HistoryModel
from models.policy_model import PolicyModel

class DetailModel(BaseModel):
    claim: ClaimModel
    policy: PolicyModel
    history: list[HistoryModel]
