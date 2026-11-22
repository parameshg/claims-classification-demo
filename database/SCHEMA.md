# Database Schema

SQLite schema for the motor claim agent. Derived from [INTENT.md](../INTENT.md); terms are defined in [GLOSSARY.md](../GLOSSARY.md).

All inputs and outputs live in one SQLite database. Dates are ISO 8601 text (`YYYY-MM-DD`). Enforce foreign keys with `PRAGMA foreign_keys = ON;`.

## Overview

```
customers 1──* policies 1──* claims 1──1 triage_results 1──* triage_fraud_flags
    └──────────────────────* claim_history
```

| Table | Role |
|---|---|
| `customers` | Policyholder. The only driver in v1. |
| `policies` | Policy summary: cover type, excess, dates, exclusions. |
| `claims` | Input: the FNOL text and filing details. |
| `claim_history` | Input: synthetic past claims for the same customer. |
| `triage_results` | Output: one row per claim. Rerunning a claim replaces it. |
| `triage_fraud_flags` | Output: fraud flags raised for a triage result. |

## Input Tables

### customers

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `customer_id` | INTEGER | PRIMARY KEY | |
| `full_name` | TEXT | NOT NULL | |

### policies

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `policy_id` | INTEGER | PRIMARY KEY | |
| `customer_id` | INTEGER | NOT NULL, FK → `customers` | |
| `cover_type` | TEXT | NOT NULL | e.g. comprehensive, third party fire and theft, third party only |
| `excess` | NUMERIC | NOT NULL, CHECK `excess >= 0` | |
| `start_date` | TEXT | NOT NULL | |
| `end_date` | TEXT | NOT NULL, CHECK `end_date >= start_date` | |
| `exclusions` | TEXT | NOT NULL DEFAULT `'[]'` | JSON array of excluded event strings |

### claims

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `claim_id` | INTEGER | PRIMARY KEY | |
| `customer_id` | INTEGER | NOT NULL, FK → `customers` | |
| `policy_id` | INTEGER | NOT NULL, FK → `policies` | |
| `filing_date` | TEXT | NOT NULL | Used for the 30-days-from-start and twelve-month fraud rules. |
| `fnol_text` | TEXT | NOT NULL | Customer-written text. |
| `police_report_number` | TEXT | NULL | Needed for the theft fraud rule. |

The structured fields the agent extracts at intake (incident date, place, parties, injuries, description) are not input columns. They are stored on `triage_results`.

### claim_history

Synthetic prior claims. The current claim is not in this table. The fraud rule counts it in addition.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `history_id` | INTEGER | PRIMARY KEY | |
| `customer_id` | INTEGER | NOT NULL, FK → `customers` | |
| `filing_date` | TEXT | NOT NULL | |
| `claim_type` | TEXT | NOT NULL, CHECK in claim types | |

Index: `CREATE INDEX idx_history_customer_date ON claim_history (customer_id, filing_date);`

## Output Tables

### triage_results

One row per claim. The primary key on `claim_id` enforces this. Write with `INSERT OR REPLACE` (or delete then insert in one transaction) so a rerun replaces the old result, including its flags.

| Column | Type | Constraints | Step |
|---|---|---|---|
| `claim_id` | INTEGER | PRIMARY KEY, FK → `claims` ON DELETE CASCADE | |
| `incident_date` | TEXT | NULL | 1 Intake |
| `incident_place` | TEXT | NULL | 1 Intake |
| `parties` | TEXT | NULL | 1 Intake |
| `injured` | INTEGER | NULL, CHECK in (0, 1) | 1 Intake |
| `description` | TEXT | NULL | 1 Intake |
| `missing_fields` | TEXT | NOT NULL DEFAULT `'[]'` | 1 Intake. JSON array of required fields that were missing or unclear. |
| `claim_type` | TEXT | NULL, CHECK in claim types | 2 Classify |
| `severity` | TEXT | NULL, CHECK in (`Low`, `Medium`, `High`) | 2 Classify |
| `confidence` | REAL | NULL, CHECK `confidence BETWEEN 0 AND 1` | 2 Classify |
| `coverage_outcome` | TEXT | NULL, CHECK in (`Covered`, `Not covered`) | 3 Policy check |
| `coverage_reason` | TEXT | NULL | 3 Policy check. Names the exclusion or inactive policy. |
| `route` | TEXT | NOT NULL, CHECK in (`Auto-approve`, `Adjuster queue`, `Investigation`) | 5 Route |
| `explanation` | TEXT | NOT NULL | 6 Explain |
| `created_at` | TEXT | NOT NULL DEFAULT CURRENT_TIMESTAMP | |

Required intake fields are `incident_date`, `claim_type` and `injured`. When any is missing, the row keeps NULL for it, lists it in `missing_fields`, and `route` is `Adjuster queue` unless a fraud flag sends it to `Investigation`.

### triage_fraud_flags

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `claim_id` | INTEGER | NOT NULL, FK → `triage_results` ON DELETE CASCADE | |
| `flag` | TEXT | NOT NULL, CHECK in flag values | |
| | | PRIMARY KEY (`claim_id`, `flag`) | |

## Allowed Values

| Domain | Values |
|---|---|
| Claim type | `Collision`, `Theft`, `Glass`, `Weather`, `Vandalism` |
| Severity | `Low`, `Medium`, `High` |
| Coverage outcome | `Covered`, `Not covered` |
| Fraud flag | `NEW_POLICY` (filed within 30 days of policy start), `FREQUENT_CLAIMS` (three or more claims in twelve months, counting the current one), `THEFT_NO_POLICE_REPORT` |
| Route | `Auto-Approve`, `Adjuster-Queue`, `Investigation` |

The incident time or place mismatch flag is out of scope for v1 and has no value.

## Out of Scope

The schema has no tables for photos, payments, settlements, repair shops, total loss, other drivers, or adjuster feedback and overrides.
