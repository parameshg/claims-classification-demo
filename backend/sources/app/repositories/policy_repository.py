import json
import sqlite3
from app.models.policy_model import PolicyModel

class PolicyRepository:
    def __init__(self, link: sqlite3.Connection) -> None:
        self.link = link

    def owner(self, policy_id: int) -> int | None:
        """Customer id owning the policy, or None when the policy is missing."""
        row = self.link.execute(
            "SELECT customer_id FROM policies WHERE policy_id = ?", (policy_id,)
        ).fetchone()
        return row["customer_id"] if row else None

    def get(self, policy_id: int) -> PolicyModel | None:
        row = self.link.execute(
            "SELECT policy_id, cover_type, excess, start_date, end_date, exclusions "
            "FROM policies WHERE policy_id = ?",
            (policy_id,),
        ).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["exclusions"] = json.loads(data["exclusions"])
        return PolicyModel(**data)