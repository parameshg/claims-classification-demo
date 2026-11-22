import json
import sqlite3
from models.policy_model import PolicyModel
from models.policy_record_model import PolicyRecordModel

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

    def record(self, policy_id: int) -> PolicyRecordModel | None:
        rows = self.all(policy_id=policy_id)
        return rows[0] if rows else None

    def all(
        self, customer_id: int | None = None, policy_id: int | None = None
    ) -> list[PolicyRecordModel]:
        sql = (
            "SELECT policy_id, customer_id, cover_type, excess, start_date, end_date, "
            "exclusions FROM policies"
        )
        clauses, args = [], []
        if customer_id is not None:
            clauses.append("customer_id = ?")
            args.append(customer_id)
        if policy_id is not None:
            clauses.append("policy_id = ?")
            args.append(policy_id)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY policy_id"
        out = []
        for row in self.link.execute(sql, args).fetchall():
            data = dict(row)
            data["exclusions"] = json.loads(data["exclusions"])
            out.append(PolicyRecordModel(**data))
        return out
