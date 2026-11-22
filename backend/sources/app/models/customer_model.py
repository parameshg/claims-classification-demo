from pydantic import BaseModel


class CustomerModel(BaseModel):
    customer_id: int
    full_name: str
