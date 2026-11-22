import sqlite3
from models.history_model import HistoryModel

class HistoryRepository:
    def __init__(self, link: sqlite3.Connection) -> None:
        self.link = link

    def for_customer(self, customer_id: int) -> list[HistoryModel]:
        rows = self.link.execute(
            "SELECT history_id, filing_date, claim_type FROM claim_history "
            "WHERE customer_id = ? ORDER BY filing_date DESC, history_id DESC",
            (customer_id,),
        ).fetchall()        
        return [HistoryModel(**dict(row)) for row in rows]