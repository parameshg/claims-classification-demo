import sqlite3

class CustomerRepository:
    def __init__(self, link: sqlite3.Connection) -> None:
        self.link = link

    def exists(self, customer_id: int) -> bool:
        row = self.link.execute(
            "SELECT 1 FROM customers WHERE customer_id = ?", (customer_id,)
        ).fetchone()
        return row is not None
