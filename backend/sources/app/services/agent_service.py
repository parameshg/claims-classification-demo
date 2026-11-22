import os
import sqlite3
from datetime import datetime
from openai import OpenAI, OpenAIError
from pydantic import ValidationError
from app.models.classify_model import ClassifyModel
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from app.fault import Fault
from app.models.claim_model import ClaimModel
from app.models.claim_new_model import ClaimNewModel
from app.models.triage_model import TriageModel
from app.repositories.claim_repository import ClaimRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.policy_repository import PolicyRepository
from app.repositories.triage_repository import TriageRepository
from app.models.policy_model import PolicyModel

CLASSIFY_PROMPT = """You classify motor insurance claims from the customer's FNOL text.

Claim types:
- Collision: vehicle hits another vehicle or object.
- Theft: vehicle or contents stolen.
- Glass: windscreen or window damage only.
- Weather: hail, flood, storm, falling tree.
- Vandalism: deliberate damage by a third party.

Severity:
- Low: cosmetic damage, no injury, no third party.
- Medium: drivable or repairable, no injury, no third party.
- High: not drivable, injury reported, a third party involved, or any theft.
- Glass is Low unless an injury is reported. Hitting a fixed object alone does not involve a third party.

Do not guess. If the text does not make the claim type clear, return claim_type null and severity null.
Confidence is your certainty from 0 to 1."""

class ClaimState(BaseModel):    
    claim_id: int = Field(..., description="The ID of the claim being triaged.")
    claim: ClaimModel | None = Field(None, description="The claim being triaged.")
    policy: PolicyModel | None = Field(None, description="The policy associated with the claim.")
    history: list[ClaimModel] = Field([], description="The customer's claim history.")
    claim_type: str | None = Field(None, description="The classified claim type, if clear.")
    severity: str | None = Field(None, description="The classified severity, if clear.")
    confidence: float | None = Field(None, description="Classification confidence from 0 to 1.")
    coverage_outcome: str | None = Field(None, description="The outcome of the coverage check, if any.")
    coverage_reason: str | None = Field(None, description="The reason for the coverage outcome, if any.")
    route: str | None = Field(None, description="The route taken through the triage process.")
    fraud_flags: list[str] = Field([], description="List of fraud flags associated with the claim.") 
    explanation: str | None = Field(None, description="Explanation of the triage process and results.")
    incident_date: str | None = Field(None, description="The date of the incident, if known.")
    incident_place: str | None = Field(None, description="The place of the incident, if known.")
    parties: str | None = Field(None, description="The parties involved in the incident, if known.")
    injured: bool | None = Field(None, description="Whether anyone was injured in the incident, if known.")
    description: str | None = Field(None, description="Description of the incident, if known.")
    missing_fields: list[str] = Field([], description="List of missing fields in the claim that are required for processing.")

class AgentService:
    graph: CompiledStateGraph

    def __init__(self, link: sqlite3.Connection) -> None:
        self.claims = ClaimRepository(link)
        self.customers = CustomerRepository(link)
        self.policies = PolicyRepository(link)        
        self.history = HistoryRepository(link)
        self.triages = TriageRepository(link)
        builder = StateGraph(ClaimState)
        builder.add_node("read_claim", self.read_claim)
        builder.add_node("extract_facts", self.extract_facts)
        builder.add_node("classify_claim", self.classify_claim)
        builder.add_node("policy_check", self.policy_check)
        builder.add_node("generate_outcome", self.generate_outcome)
        builder.add_node("generate_explanation", self.generate_explanation)
        builder.add_edge(START, "read_claim")
        builder.add_edge("read_claim", "extract_facts")
        builder.add_edge("extract_facts", "classify_claim")
        builder.add_edge("classify_claim", "policy_check")
        builder.add_edge("policy_check", "generate_outcome")
        builder.add_edge("generate_outcome", "generate_explanation")
        builder.add_edge("generate_explanation", END)
        self.graph = builder.compile()

    def claim_input(self, state: ClaimState) -> str:
        claim = state.claim
        police_report = f"Police report number: {claim.police_report_number or 'none'}"
        return f"Filing date: {claim.filing_date}\n{police_report}\nFNOL text:\n{claim.fnol_text}"
    
    def read_claim(self, state: ClaimState):
        claim = self.claims.get(state.claim_id)
        policy = self.policies.get(claim.policy_id)
        history = self.history.list_by_customer(claim.customer_id)
        return { "claim": claim, "policy": policy, "history": history }

    def extract_facts(self, state: ClaimState):
        return { "incident_date": None, "incident_place": None, "parties": None, "injured": False, "description": None }
    
    def classify_claim(self, state: ClaimState):
        try:
            client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ["OPENROUTER_API_KEY"])
            response = client.chat.completions.create(model=os.environ["OPENROUTER_MODEL"], max_tokens=1024,
            messages=[
                {"role": "system", "content": CLASSIFY_PROMPT},
                {"role": "user", "content": self.claim_input(state)},
            ],
            tools=[{
                "type": "function",
                "function": {
                    "name": "classify",
                    "description": "Record the claim type, severity and confidence.",
                    "parameters": ClassifyModel.model_json_schema(),
                }}],
            tool_choice={"type": "function", "function": {"name": "classify"}})
            tool_calls = response.choices[0].message.tool_calls
            if not tool_calls:
                raise ValueError("The model did not call the classify tool.")
            result = ClassifyModel.model_validate_json(tool_calls[0].function.arguments)
        except (ValidationError, ValueError, IndexError, OpenAIError) as err:
            raise Fault(502, "llm_failed", "The LLM could not classify the claim.") from err
        return { "claim_type": result.claim_type, "severity": result.severity, "confidence": result.confidence }

    def policy_check(self, state: ClaimState):
        return { "coverage_outcome": None, "coverage_reason": None }

    def generate_outcome(self, state: ClaimState):
        return { "route": None }

    def generate_explanation(self, state: ClaimState):
        return { "explanation": None }

    def triage(self, claim_id: int) -> TriageModel:
        result = self.graph.invoke({"claim_id": claim_id})       
        triage = TriageModel(
            claim_id=claim_id,
            claim_type=result["claim_type"],
            severity=result["severity"],
            confidence=result["confidence"],
            coverage_outcome=result["coverage_outcome"],
            coverage_reason=result["coverage_reason"],
            route=result["route"],
            fraud_flags=result["fraud_flags"],
            missing_fields=result["missing_fields"],
            explanation=result["explanation"],
            description=result["description"],
            incident_date=result["incident_date"],
            incident_place=result["incident_place"],
            parties=result["parties"],
            injured=result["injured"],
            created_at=datetime.now().isoformat(),
        )
        self.triages.save(triage)
        return triage