# Backend API

HTTP API for the motor claim agent. Derived from [INTENT.md](../INTENT.md) and [database/SCHEMA.md](../database/SCHEMA.md); terms are defined in [GLOSSARY.md](../GLOSSARY.md).

The API is decision support only. It has no endpoint to pay, deny or settle a claim, and none for adjuster feedback or override (out of scope for v1).

## Conventions

- Base path: `/api/v1`. Request and response bodies are JSON (`Content-Type: application/json`).
- Dates are `YYYY-MM-DD`. Timestamps are UTC ISO 8601.
- Field names match the database columns in SCHEMA.md. JSON columns (`exclusions`, `missing_fields`) are returned as arrays.
- No authentication in v1 (demo).

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/claims` | Submit a new claim (FNOL text). |
| GET | `/claims` | List claims with their current route. |
| GET | `/claims/{claim_id}` | Get a claim with its policy and claim history. |
| POST | `/claims/{claim_id}/triage` | Run the agent. Replaces any existing triage result. |
| GET | `/claims/{claim_id}/triage` | Get the stored triage result. |
| GET | `/customers` | List customers. |
| GET | `/customers/{customer_id}` | Get one customer. `404 customer_not_found` if missing. |
| GET | `/policies` | List policies. Optional `customer_id` filter. |
| GET | `/policies/{policy_id}` | Get one policy. `404 policy_not_found` if missing. |

### POST /claims

Creates a claim. Does not run triage.

Request:

```json
{
  "customer_id": 1,
  "policy_id": 1,
  "filing_date": "2026-11-20",
  "fnol_text": "Someone smashed my passenger window overnight...",
  "police_report_number": null
}
```

| Field | Required | Notes |
|---|---|---|
| `customer_id` | yes | Must exist. |
| `policy_id` | yes | Must exist and belong to the customer. |
| `filing_date` | yes | |
| `fnol_text` | yes | Non-empty. |
| `police_report_number` | no | |

Response `201`: the claim object (see [Claim](#claim)).

### GET /claims

Query parameters (all optional):

| Param | Notes |
|---|---|
| `route` | Filter on the stored triage route. Allowed values below. |
| `triaged` | `true` or `false`. |
| `limit`, `offset` | Paging. Default limit 50, max 200. |

Response `200`:

```json
{
  "items": [
    {
      "claim_id": 12,
      "customer_id": 1,
      "filing_date": "2026-11-20",
      "claim_type": "Glass",
      "severity": "Low",
      "route": "Auto-Approve"
    }
  ],
  "total": 1
}
```

`claim_type`, `severity` and `route` are `null` for a claim that has not been triaged.

### GET /claims/{claim_id}

Response `200`: the claim, its policy summary and the customer's claim history.

```json
{
  "claim": { "...": "see Claim" },
  "policy": {
    "policy_id": 1,
    "cover_type": "comprehensive",
    "excess": 250,
    "start_date": "2026-01-01",
    "end_date": "2026-12-31",
    "exclusions": ["racing"]
  },
  "history": [
    { "history_id": 4, "filing_date": "2026-03-02", "claim_type": "Collision" }
  ]
}
```

### POST /claims/{claim_id}/triage

Runs the six workflow steps (intake, classify, policy check, fraud raise, route, explain) and stores the result. Steps 1, 2 and 6 use the LLM. Steps 3, 4 and 5 are plain code, so the same extracted fields always give the same coverage outcome, fraud flags and route.

No request body. Running a claim again deletes the old result and its fraud flags and writes a new one in one transaction. The response is the new [Triage result](#triage-result).

Response `200` for every completed run, including a claim with missing required fields. Missing fields are not an error: the result has `route: "Adjuster-Queue"` (or `"Investigation"` when a fraud flag is raised), the field names are in `missing_fields`, and the explanation names them.

If the LLM call fails, the endpoint returns `502` and leaves any existing result unchanged.

### GET /claims/{claim_id}/triage

Response `200`: the stored [Triage result](#triage-result). Returns `404` if the claim has not been triaged.

## Objects

### Customer

`{ "customer_id": 1, "full_name": "..." }`

### Policy

The policy summary shown under `GET /claims/{claim_id}`, plus `customer_id`.

### Claim

| Field | Type | Notes |
|---|---|---|
| `claim_id` | integer | |
| `customer_id` | integer | |
| `policy_id` | integer | |
| `filing_date` | string | |
| `fnol_text` | string | |
| `police_report_number` | string or null | |

### Triage result

| Field | Type | Notes |
|---|---|---|
| `claim_id` | integer | |
| `incident_date` | string or null | Null when missing. |
| `incident_place` | string or null | |
| `parties` | string or null | |
| `injured` | boolean or null | Stored as 0/1 in the database. |
| `description` | string or null | |
| `missing_fields` | string[] | Any of `incident_date`, `claim_type`, `injured`. |
| `claim_type` | string or null | |
| `severity` | string or null | |
| `confidence` | number or null | 0 to 1. |
| `coverage_outcome` | string or null | |
| `coverage_reason` | string or null | Names the exclusion or inactive policy when not covered. |
| `fraud_flags` | string[] | Empty when none. |
| `route` | string | |
| `explanation` | string | Short enough for an adjuster to read in ten seconds. |
| `created_at` | string | |

Example:

```json
{
  "claim_id": 12,
  "incident_date": "2026-11-19",
  "incident_place": "Oak Street car park",
  "parties": "Policyholder only",
  "injured": false,
  "description": "Passenger window smashed overnight.",
  "missing_fields": [],
  "claim_type": "Vandalism",
  "severity": "Medium",
  "confidence": 0.82,
  "coverage_outcome": "Covered",
  "coverage_reason": null,
  "fraud_flags": [],
  "route": "Adjuster-Queue",
  "explanation": "Covered vandalism, medium severity. Confidence 0.82 is below the auto-approve threshold.",
  "created_at": "2026-11-22T09:30:00Z"
}
```

## Allowed Values

Same as the Allowed Values section in SCHEMA.md.

| Domain | Values |
|---|---|
| Claim type | `Collision`, `Theft`, `Glass`, `Weather`, `Vandalism` |
| Severity | `Low`, `Medium`, `High` |
| Coverage outcome | `Covered`, `Not covered` |
| Fraud flag | `NEW_POLICY`, `FREQUENT_CLAIMS`, `THEFT_NO_POLICE_REPORT` |
| Route | `Auto-Approve`, `Adjuster-Queue`, `Investigation` |

## Errors

All errors use one shape:

```json
{ "error": { "code": "claim_not_found", "message": "Claim 99 does not exist." } }
```

| Status | Code | When |
|---|---|---|
| 400 | `invalid_request` | Missing or malformed field, or `policy_id` does not belong to `customer_id`. |
| 404 | `claim_not_found` | No claim with that id, or no triage result yet on the GET triage endpoint. |
| 404 | `customer_not_found`, `policy_not_found` | On `POST /claims`. |
| 502 | `llm_failed` | The LLM call in step 1, 2 or 6 failed. No result is written. |

## Out of Scope for v1

Photo upload, payments, settlement, repair shop integration, total loss assessment, other drivers, adjuster feedback or override, and the incident time or place mismatch flag.
