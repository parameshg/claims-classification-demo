import os
import sqlite3
from datetime import date, datetime, timedelta
from openai import OpenAI, OpenAIError
from pydantic import ValidationError
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from models.classify_model import ClassifyModel
from models.extract_model import ExtractModel
from fault import Fault
from models.claim_model import ClaimModel
from models.history_model import HistoryModel
from models.triage_model import TriageModel
from repositories.claim_repository import ClaimRepository
from repositories.customer_repository import CustomerRepository
from repositories.history_repository import HistoryRepository
from repositories.policy_repository import PolicyRepository
from repositories.triage_repository import TriageRepository
from models.policy_model import PolicyModel

EXTRACT_PROMPT = """You extract facts from a motor insurance customer's FNOL text.

Extract only what the text states. Do not guess or infer missing details; return null for anything not stated.
- incident_date: the date the incident happened as YYYY-MM-DD. Resolve relative dates ("yesterday") against the filing date.
- incident_place: where it happened.
- parties: other people, vehicles or organisations involved.
- injured: true if anyone was injured, false only if the text says no one was, otherwise null.
- description: a one or two sentence factual summary."""

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

AUTO_APPROVE_CONFIDENCE = 0.88

CLAIM_TYPE_EXCLUSIONS = {
    "Collision": [],
    "Theft": ["theft"],
    "Glass": ["glass damage"],
    "Weather": ["weather damage"],
    "Vandalism": ["vandalism"],
}

class ClaimState(BaseModel):
    claim_id: int = Field(..., description="The ID of the claim being triaged.")
    claim: ClaimModel | None = Field(None, description="The claim being triaged.")
    policy: PolicyModel | None = Field(None, description="The policy associated with the claim.")
    history: list[HistoryModel] = Field([], description="The customer's claim history.")
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
        builder.add_node("fraud_check", self.fraud_check)
        builder.add_node("route_claim", self.route_claim)
        builder.add_edge(START, "read_claim")
        builder.add_edge("read_claim", "extract_facts")
        builder.add_edge("extract_facts", "classify_claim")
        builder.add_edge("classify_claim", "policy_check")
        builder.add_edge("policy_check", "fraud_check")
        builder.add_edge("fraud_check", "route_claim")
        builder.add_edge("route_claim", END)
        self.graph = builder.compile()

    def claim_input(self, state: ClaimState) -> str:
        claim = state.claim
        police_report = f"Police report number: {claim.police_report_number or 'none'}"
        return f"Filing date: {claim.filing_date}\n{police_report}\nFNOL text:\n{claim.fnol_text}"
    
    def read_claim(self, state: ClaimState):
        claim = self.claims.get(state.claim_id)
        policy = self.policies.get(claim.policy_id)
        history = self.history.for_customer(claim.customer_id)
        return { "claim": claim, "policy": policy, "history": history }

    def extract_facts(self, state: ClaimState):
        try:
            client = OpenAI(base_url="https://openrouter.ai/api/v1",  api_key=os.environ["OPENROUTER_API_KEY"])
            response = client.chat.completions.create(model=os.environ["OPENROUTER_MODEL"], max_tokens=1024,
            messages=[
                {"role": "system", "content": EXTRACT_PROMPT},
                {"role": "user", "content": self.claim_input(state)},
            ],
            tools=[{
                "type": "function",
                "function": {
                    "name": "extract",
                    "description": "Record the facts stated in the FNOL text.",
                    "parameters": ExtractModel.model_json_schema(),
                }}],
            tool_choice={"type": "function", "function": {"name": "extract"}})
            tool_calls = response.choices[0].message.tool_calls
            if not tool_calls:
                raise ValueError("The model did not call the extract tool.")
            result = ExtractModel.model_validate_json(tool_calls[0].function.arguments)
        except (ValidationError, ValueError, IndexError, OpenAIError) as err:
            print(f"Error extracting facts: {err}")
            raise Fault(502, "llm_failed", "The LLM could not extract facts from the claim.") from err
        return {
            "incident_date": result.incident_date,
            "incident_place": result.incident_place,
            "parties": result.parties,
            "injured": result.injured,
            "description": result.description,
        }
    
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
        policy = state.policy
        if not state.incident_date:
            return { "coverage_outcome": None, "coverage_reason": None }
        if not policy.start_date <= state.incident_date <= policy.end_date:
            reason = f"The policy was not active on the incident date {state.incident_date} (active {policy.start_date} to {policy.end_date})."
            return { "coverage_outcome": "Not covered", "coverage_reason": reason }
        if state.claim_type is None:
            return { "coverage_outcome": None, "coverage_reason": None }
        excluded = {exclusion.lower() for exclusion in policy.exclusions}
        for exclusion in CLAIM_TYPE_EXCLUSIONS[state.claim_type]:
            if exclusion in excluded:
                return { "coverage_outcome": "Not covered", "coverage_reason": f"The policy excludes {exclusion}." }
        return { "coverage_outcome": "Covered", "coverage_reason": None }

    def fraud_check(self, state: ClaimState):
        claim = state.claim
        filed = date.fromisoformat(claim.filing_date)
        flags = []
        days_since_start = (filed - date.fromisoformat(state.policy.start_date)).days
        if 0 <= days_since_start <= 30:
            flags.append("NEW_POLICY")
        window_start = filed - timedelta(days=365)
        prior = [h for h in state.history if window_start <= date.fromisoformat(h.filing_date) <= filed]
        if len(prior) + 1 >= 3:
            flags.append("FREQUENT_CLAIMS")
        if state.claim_type == "Theft" and not claim.police_report_number:
            flags.append("THEFT_NO_POLICE_REPORT")
        return { "fraud_flags": flags }
    
    def route_claim(self, state: ClaimState):
        missing = [name for name, value in (
            ("incident_date", state.incident_date),
            ("claim_type", state.claim_type),
            ("injured", state.injured),
        ) if value is None]
        if state.fraud_flags:
            route = "Investigation"
        elif missing:
            route = "Adjuster-Queue"
        elif state.coverage_outcome == "Not covered":
            route = "Adjuster-Queue"
        elif state.severity == "Low" and state.coverage_outcome == "Covered" and state.confidence is not None and state.confidence > AUTO_APPROVE_CONFIDENCE:
            route = "Auto-Approve"
        else:
            route = "Adjuster-Queue"

        parts = []
        if state.claim_type:
            parts.append(f"{state.claim_type} claim, {(state.severity or 'unknown').lower()} severity (confidence {state.confidence:.2f}).")
        else:
            parts.append("The claim type is unclear.")
        if state.coverage_outcome == "Not covered":
            parts.append(f"Not covered: {state.coverage_reason}")
        elif state.coverage_outcome == "Covered":
            parts.append("Covered by the policy.")
        else:
            parts.append("Coverage could not be determined.")
        if state.fraud_flags:
            parts.append(f"Fraud flags: {', '.join(state.fraud_flags)}.")
        if missing:
            parts.append(f"Missing required fields: {', '.join(missing)}.")
        if route == "Investigation":
            parts.append("Sent to investigation because a fraud flag was raised.")
        elif route == "Auto-Approve":
            parts.append(f"Auto-approved: low severity, covered and confidence above {AUTO_APPROVE_CONFIDENCE}.")
        else:
            parts.append("Sent to the adjuster queue for review.")
        return { "route": route, "missing_fields": missing, "explanation": " ".join(parts) }

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
            description=result["description"],###########
            incident_date=result["incident_date"],
            incident_place=result["incident_place"],
            parties=result["parties"],
            injured=result["injured"],
            created_at=datetime.now().isoformat(),
        )
        self.triages.save(triage)
        return triage