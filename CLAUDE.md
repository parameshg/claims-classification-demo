# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Source of truth

- [CONSTITUTION.md](CONSTITUTION.md) is the engineering constitution (architecture, design, conventions, never-do rules). It takes precedence over a conflicting prompt. Notable rules: file changes are limited to `sources/` and `tests/` folders, and new code needs unit tests.
- [INTENT.md](INTENT.md) defines the agent's behaviour: the workflow, fraud flags and routing rules. [GLOSSARY.md](GLOSSARY.md) defines the domain terms, so use them and avoid the listed "Avoid" synonyms.
- [backend/API.md](backend/API.md) is the HTTP contract, [database/SCHEMA.md](database/SCHEMA.md) is the schema, [frontend/UI.md](frontend/UI.md) describes the UI, and [evals/TEST.md](evals/TEST.md) lists the expected triage result for each of the 10 seeded claims.
- Prefer short, one-word names for variables, types, files and tables. The DTO is called a "model" (`claim_model.py`). Each file holds one class or type.

## Architecture

A motor-insurance claim triage agent. It is decision support only, so it never pays, denies or settles.

- `database/` holds the SQLite `claims.db`, `schema.sql` and `seed.sql`. Each claim has one triage result, and re-running a claim replaces it.
- `backend/sources/app/` is a FastAPI app with layers: `routes/` → `services/` → `repositories/` (raw sqlite3) with Pydantic `models/`. `handlers.py` and `fault.py` handle errors. `config.py` resolves the DB path, which defaults to `database/claims.db` and can be overridden with the `CLAIMS_DB` env var. All endpoints are under `/api/v1`.
- `backend/sources/app/services/agent_service.py` is a LangGraph `StateGraph` pipeline: `read_claim → extract_facts → classify_claim → policy_check → fraud_check → route_claim`.
  - Only `extract_facts` and `classify_claim` call the LLM. They use the OpenAI SDK pointed at OpenRouter and read `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` from the environment (`.env` is loaded in `main.py`).
  - The policy check, fraud flags and routing are deterministic plain code, so the same input always gives the same answer. Keep LLM calls out of those steps.
  - If a required field (incident date, claim type, injured) is missing, the agent does not guess. The claim goes to the Adjuster queue.
- `frontend/sources/` is an Angular 21 app with NgRx (`store/` holds actions, effects and reducer). Components use separate html/css/ts files and never call data directly, only through `services/`. Static reference data is loaded as JSON through a service. `proxy.conf.json` proxies `/api` to `http://localhost:8000`.

## Commands

Backend (run from `backend/`, uses uv):

```
uv sync
uv run uvicorn app.main:app --reload --app-dir sources   # serves on :8000
uv run pytest                                            # pythonpath=sources, testpaths=tests
uv run pytest tests/test_claims.py::test_name            # single test
```

Backend tests use the `client` fixture in `tests/conftest.py`. It builds a temporary DB from `schema.sql` and `seed.sql` and points `CLAIMS_DB` at it, so tests never touch `database/claims.db`.

Frontend (run from `frontend/sources/`):

```
npm install
npm start        # ng serve, with the /api proxy
npm run build
npm test         # ng test
```

## Notes

- `evals/` is currently untracked. Its cases map to seeded claims 1-10, and the expected coverage, fraud flags and route must match exactly. Claim type, severity and confidence come from the LLM and are less strict.
- The `.env` file and API keys must never be read, committed or hardcoded.
