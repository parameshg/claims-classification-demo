import sqlite3
from typing import Annotated
from fastapi import APIRouter, Depends
from db import connection
from fault import Fault
from models.policy_record_model import PolicyRecordModel
from repositories.policy_repository import PolicyRepository

router = APIRouter(prefix="/policies", tags=["policies"])

Link = Annotated[sqlite3.Connection, Depends(connection)]

@router.get("", response_model=list[PolicyRecordModel])
def listing(link: Link, customer_id: int | None = None) -> list[PolicyRecordModel]:
    return PolicyRepository(link).all(customer_id=customer_id)

@router.get("/{policy_id}", response_model=PolicyRecordModel)
def detail(policy_id: int, link: Link) -> PolicyRecordModel:
    policy = PolicyRepository(link).record(policy_id)
    if policy is None:
        raise Fault(404, "policy_not_found", f"Policy {policy_id} does not exist.")
    return policy
