import sqlite3
from models.customer_model import CustomerModel

class CustomerRepository:
    def __init__(self, link: sqlite3.Connection) -> None:
        self.link = link

    def exists(self, customer_id: int) -> bool:
        row = self.link.execute(
            "SELECT 1 FROM customers WHERE customer_id = ?", (customer_id,)
        ).fetchone()
        return row is not None


    def get(self, customer_id: int) -> CustomerModel | None:
        row = self.link.execute(
            "SELECT customer_id, full_name FROM customers WHERE customer_id = ?",
            (customer_id,),
        ).fetchone()
        return CustomerModel(**dict(row)) if row else None

    def all(self) -> list[CustomerModel]:
        rows = self.link.execute(
            "SELECT customer_id, full_name FROM customers ORDER BY customer_id"
        ).fetchall()
        return [CustomerModel(**dict(r)) for r in rows]
