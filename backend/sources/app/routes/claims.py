import sqlite3
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, Query
from db import connection
from models.claim_model import ClaimModel
from models.claim_new_model import ClaimNewModel
from models.detail_model import DetailModel
from models.page_model import PageModel
from models.triage_model import TriageModel
from services.claim_service import ClaimService
from services.agent_service import AgentService

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

@router.get("/{claim_id}/triage", response_model=TriageModel)
def triage(claim_id: int, link: Link) -> TriageModel:
    return ClaimService(link).triage(claim_id)

@router.post("/{claim_id}/triage", response_model=TriageModel)
def triage(claim_id: int, link: Link) -> TriageModel:
    return AgentService(link).triage(claim_id)