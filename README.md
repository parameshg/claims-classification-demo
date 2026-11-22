# Claims Classification Agent (Demo)

A decision-support agent for motor insurance. It reads a newly reported claim (the customer's FNOL text), classifies it, checks it against the policy, raises fraud flags and recommends a route. It never pays, denies or settles a claim.

## How it works

Each triage run is a LangGraph pipeline. An LLM handles steps 1 and 2. Plain code handles steps 3 to 5, so the same input always gives the same answer.

1. **Intake**: extract the incident date, place, parties, injuries and description from the FNOL text.
2. **Classify**: assign a claim type (Collision, Theft, Glass, Weather, Vandalism), a severity (Low, Medium, High) and a confidence score.
3. **Policy check**: compare the incident date and event with the policy dates and exclusions to set the coverage outcome.
4. **Fraud raise**: rule-based flags (`NEW_POLICY`, `FREQUENT_CLAIMS`, `THEFT_NO_POLICE_REPORT`).
5. **Route and explain**: pick Auto-approve, Adjuster queue or Investigation, and build a short explanation.

If a required field (incident date, claim type, injured) is missing, the agent does not guess. The claim goes to the adjuster queue and the explanation names the missing field. The full rules are in [INTENT.md](INTENT.md).

## Stack

| Layer | Technology |
|---|---|
| Frontend | Angular 21, NgRx, Tailwind CSS |
| Backend | Python 3.12+, FastAPI, Pydantic, LangGraph |
| LLM | OpenAI SDK pointed at OpenRouter |
| Database | SQLite |

```
backend/     FastAPI app (sources/) and pytest tests (tests/)
frontend/    Angular app (sources/)
database/    claims.db, schema.sql, seed.sql
evals/       Expected triage results for the 10 seeded claims
docs/        Agent diagram (agent.drawio)
```

## Setup

### Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Node.js and npm (the frontend pins npm 11.12.1)
- An [OpenRouter](https://openrouter.ai) API key

### Backend

Create `backend/.env`:

```
OPENROUTER_API_KEY=<your key>
OPENROUTER_MODEL=<model id, for example anthropic/claude-sonnet-4.5>
```

Optionally set `CLAIMS_DB` to use a database other than `database/claims.db`.

```
cd backend/sources/app
uv sync
uv run uvicorn main:app --reload
```

The API serves on http://localhost:8000 under `/api/v1`. FastAPI's interactive docs are at `/docs`.

### Frontend

```
cd frontend/sources
npm install
npm start
```

The dev server proxies `/api` to http://localhost:8000, so start the backend first.

### Database

`database/claims.db` is checked in with seed data. To rebuild it:

```
sqlite3 database/claims.db < database/schema.sql
sqlite3 database/claims.db < database/seed.sql
```

Delete the existing file first, because the seed data would otherwise collide with existing rows.

## Tests

```
cd backend
uv run pytest
uv run pytest tests/test_claims.py::test_name   # one test
```

Tests build a temporary database from `schema.sql` and `seed.sql`, so they never touch `database/claims.db` and need no LLM key.

```
cd frontend/sources
npm test
```

[evals/TEST.md](evals/TEST.md) lists the expected result for each seeded claim. Coverage, fraud flags and route must match exactly. Claim type, severity and confidence come from the LLM.

## API

Base path `/api/v1`. JSON bodies, no authentication in v1.

| Method | Path | Purpose |
|---|---|---|
| POST | `/claims` | Submit a new claim (FNOL text). |
| GET | `/claims` | List claims with their current route. Filters: `route`, `triaged`, `limit`, `offset`. |
| GET | `/claims/{claim_id}` | Get a claim with its policy and claim history. |
| POST | `/claims/{claim_id}/triage` | Run the agent. Replaces any existing triage result. |
| GET | `/claims/{claim_id}/triage` | Get the stored triage result. |
| GET | `/customers` | List customers. |
| GET | `/customers/{customer_id}` | Get one customer. |
| GET | `/policies` | List policies. Optional `customer_id` filter. |
| GET | `/policies/{policy_id}` | Get one policy. |

Request and response shapes, error format and allowed values are in [backend/API.md](backend/API.md).

## Database schema

```
customers 1──* policies 1──* claims 1──1 triage_results 1──* triage_fraud_flags
    └──────────────────────* claim_history
```

`customers`, `policies`, `claims` and `claim_history` are inputs. `triage_results` and `triage_fraud_flags` are outputs, with one result per claim. Column definitions are in [database/SCHEMA.md](database/SCHEMA.md).

## Further reading

- [INTENT.md](INTENT.md): scope, workflow, fraud flags and routing rules
- [GLOSSARY.md](GLOSSARY.md): domain terms
- [CONSTITUTION.md](CONSTITUTION.md): architecture, design and code conventions
- [frontend/UI.md](frontend/UI.md): UI description
