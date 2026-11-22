import sqlite3
from typing import Annotated
from fastapi import APIRouter, Depends
from app.db import connection
from app.fault import Fault
from app.models.customer_model import CustomerModel
from app.repositories.customer_repository import CustomerRepository

router = APIRouter(prefix="/customers", tags=["customers"])

Link = Annotated[sqlite3.Connection, Depends(connection)]

@router.get("", response_model=list[CustomerModel])
def listing(link: Link) -> list[CustomerModel]:
    return CustomerRepository(link).all()

@router.get("/{customer_id}", response_model=CustomerModel)
def detail(customer_id: int, link: Link) -> CustomerModel:
    customer = CustomerRepository(link).get(customer_id)
    if customer is None:
        raise Fault(404, "customer_not_found", f"Customer {customer_id} does not exist.")
    return customer
