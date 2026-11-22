import sqlite3
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, Query
from app.db import connection
from app.models.claim_model import ClaimModel
from app.models.claim_new_model import ClaimNewModel
from app.models.detail_model import DetailModel
from app.models.page_model import PageModel
from app.services.claim_service import ClaimService

router = APIRouter(prefix="/claims", tags=["claims"])

Link = Annotated[sqlite3.Connection, Depends(connection)]

Route = Literal["Auto-Approve", "Adjuster-Queue", "Investigation"]

@router.post("", status_code=201, response_model=ClaimModel)
def submit(new: ClaimNewModel, link: Link) -> ClaimModel:
    return ClaimService(link).submit(new)

@router.get("", response_model=PageModel)
def listing(
    link: Link,
    route: Route | None = None,
    triaged: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PageModel:
    return ClaimService(link).listing(route, triaged, limit, offset)

@router.get("/{claim_id}", response_model=DetailModel)
def detail(claim_id: int, link: Link) -> DetailModel:
    return ClaimService(link).detail(claim_id)