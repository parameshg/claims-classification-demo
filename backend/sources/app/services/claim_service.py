import sqlite3
from app.fault import Fault
from app.models.claim_model import ClaimModel
from app.models.claim_new_model import ClaimNewModel
from app.models.detail_model import DetailModel
from app.models.page_model import PageModel
from app.models.triage_model import TriageModel
from app.repositories.triage_repository import TriageRepository
from app.repositories.claim_repository import ClaimRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.policy_repository import PolicyRepository

class ClaimService:
    def __init__(self, link: sqlite3.Connection) -> None:
        self.claims = ClaimRepository(link)
        self.customers = CustomerRepository(link)
        self.policies = PolicyRepository(link)
        self.history = HistoryRepository(link)
        self.triages = TriageRepository(link)

    def submit(self, new: ClaimNewModel) -> ClaimModel:
        if not self.customers.exists(new.customer_id):
            raise Fault(404, "customer_not_found", f"Customer {new.customer_id} does not exist.")
        owner = self.policies.owner(new.policy_id)
        if owner is None:
            raise Fault(404, "policy_not_found", f"Policy {new.policy_id} does not exist.")
        if owner != new.customer_id:
            raise Fault(
                400,
                "invalid_request",
                f"Policy {new.policy_id} does not belong to customer {new.customer_id}.",
            )
        return self.claims.add(new)

    def listing(
        self, route: str | None, triaged: bool | None, limit: int, offset: int
    ) -> PageModel:
        items, total = self.claims.page(route, triaged, limit, offset)
        return PageModel(items=items, total=total)

    def triage(self, claim_id: int) -> TriageModel:
        if self.claims.get(claim_id) is None:
            raise Fault(404, "claim_not_found", f"Claim {claim_id} does not exist.")
        result = self.triages.get(claim_id)
        if result is None:
            raise Fault(404, "claim_not_found", f"Claim {claim_id} has not been triaged.")
        return result

    def detail(self, claim_id: int) -> DetailModel:
        claim = self.claims.get(claim_id)
        if claim is None:
            raise Fault(404, "claim_not_found", f"Claim {claim_id} does not exist.")
        policy = self.policies.get(claim.policy_id)
        assert policy is not None  # guaranteed by the claims.policy_id foreign key
        return DetailModel(
            claim=claim,
            policy=policy,
            history=self.history.for_customer(claim.customer_id),
        )