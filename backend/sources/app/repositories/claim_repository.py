import sqlite3
from app.models.claim_model import ClaimModel
from app.models.claim_new_model import ClaimNewModel
from app.models.item_model import ItemModel

COLUMNS = "claim_id, customer_id, policy_id, filing_date, fnol_text, police_report_number"

class ClaimRepository:
    def __init__(self, link: sqlite3.Connection) -> None:
        self.link = link

    def add(self, new: ClaimNewModel) -> ClaimModel:
        with self.link:
            cur = self.link.execute(
                "INSERT INTO claims (customer_id, policy_id, filing_date, fnol_text, "
                "police_report_number) VALUES (?, ?, ?, ?, ?)",
                (
                    new.customer_id,
                    new.policy_id,
                    new.filing_date.isoformat(),
                    new.fnol_text,
                    new.police_report_number,
                ),
            )
        claim = self.get(cur.lastrowid)
        assert claim is not None
        return claim

    def get(self, claim_id: int) -> ClaimModel | None:
        row = self.link.execute(
            f"SELECT {COLUMNS} FROM claims WHERE claim_id = ?", (claim_id,)
        ).fetchone()
        return ClaimModel(**dict(row)) if row else None

    def page(
        self, route: str | None, triaged: bool | None, limit: int, offset: int
    ) -> tuple[list[ItemModel], int]:
        where: list[str] = []
        args: list = []
        if route is not None:
            where.append("t.route = ?")
            args.append(route)
        if triaged is not None:
            where.append("t.claim_id IS NOT NULL" if triaged else "t.claim_id IS NULL")
        clause = f"WHERE {' AND '.join(where)}" if where else ""
        base = "FROM claims c LEFT JOIN triage_results t ON t.claim_id = c.claim_id"

        total = self.link.execute(f"SELECT COUNT(*) {base} {clause}", args).fetchone()[0]
        rows = self.link.execute(
            "SELECT c.claim_id, c.customer_id, c.filing_date, "
            "t.claim_type, t.severity, t.route "
            f"{base} {clause} ORDER BY c.claim_id LIMIT ? OFFSET ?",
            [*args, limit, offset],
        ).fetchall()
        return [ItemModel(**dict(row)) for row in rows], total