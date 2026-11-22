# Test Scenarios

Eval cases for the motor claim agent. Each case is one claim in [seed.sql](../database/seed.sql). Terms are defined in [GLOSSARY.md](../GLOSSARY.md) and the rules in [INTENT.md](../INTENT.md).

The expected values are what the agent should produce for each claim. Steps 3, 4 and 5 (coverage, fraud flags, route) are plain code and must match exactly. Steps 1 and 2 (intake, claim type, severity, confidence) come from the LLM, so compare them against the expected values and review misses by hand.

## Summary

| Claim | Scenario | Expected route |
|---|---|---|
| 1 | Minor scrape, covered | Auto-Approve |
| 10 | Glass chip, covered | Auto-Approve |
| 2 | Rear-ended by a third party, neck pain | Adjuster-Queue |
| 3 | Theft with a police report | Adjuster-Queue |
| 4 | Theft on a third-party-only policy | Adjuster-Queue (not covered) |
| 9 | Windscreen chip after the policy expired | Adjuster-Queue (not covered) |
| 8 | No incident date, injuries unclear | Adjuster-Queue (missing fields) |
| 5 | Filed 12 days after policy start | Investigation |
| 6 | Third prior claim in 12 months, plus this one | Investigation |
| 7 | Theft with no police report | Investigation |

## Expected Results

| Claim | Incident date | Claim type | Severity | Injured | Coverage | Fraud flags | Route |
|---|---|---|---|---|---|---|---|
| 1 | 2026-03-01 | Collision | Low | 0 | Covered | none | Auto-Approve |
| 2 | 2026-04-08 | Collision | High | 1 | Covered | none | Adjuster-Queue |
| 3 | 2026-02-16 | Theft | High | 0 | Covered | none | Adjuster-Queue |
| 4 | 2026-01-10 | Theft | High | 0 | Not covered | none | Adjuster-Queue |
| 5 | 2026-03-21 | Collision | Medium | 0 | Covered | `NEW_POLICY` | Investigation |
| 6 | 2026-06-18 | Weather | Medium | 0 | Covered | `FREQUENT_CLAIMS` | Investigation |
| 7 | missing or unclear | Theft | High | 0 | Covered | `THEFT_NO_POLICE_REPORT` | Investigation |
| 8 | missing | Collision | n/a | missing | n/a | none | Adjuster-Queue |
| 9 | 2026-01-30 | Glass | Low | 0 | Not covered | none | Adjuster-Queue |
| 10 | 2026-04-24 | Glass | Low | 0 | Covered | none | Auto-Approve |

## Cases

### Claim 1: Minor scrape, covered

- Customer 1, policy 1 (comprehensive, 2025-06-01 to 2026-05-31, no exclusions).
- Cosmetic damage, drivable, nobody hurt, no third party, so severity is Low.
- No fraud flag: policy is old, one prior claim in 2023, and it is not a theft.
- Routes to Auto-Approve only if confidence is above 0.9. At 0.9 or below it routes to Adjuster-Queue.

### Claim 2: Rear-ended by a third party

- Customer 2, policy 2 (comprehensive, 2025-09-01 to 2026-08-31).
- A third party is involved and a neck injury is reported, so severity is High.
- Covered, no fraud flag (one prior claim in the last twelve months, so two with this one).
- Rule 4 applies: Adjuster-Queue.

### Claim 3: Theft with a police report

- Customer 3, policy 3 (third party fire and theft, 2025-07-15 to 2026-07-14).
- Any theft is High severity. Theft is not excluded and the policy was active.
- Police report number `POL-2026-004512` is present, so no `THEFT_NO_POLICE_REPORT`. One prior claim, so two with this one.
- Adjuster-Queue.

### Claim 4: Theft excluded by the policy

- Customer 4, policy 4 (third party only, 2025-04-01 to 2026-03-31), exclusions include theft.
- The policy was active on the incident date but excludes the event, so coverage is Not covered.
- The explanation must name the theft exclusion.
- Rule 2: Adjuster-Queue.

### Claim 5: New policy

- Customer 5, policy 5 starts 2026-03-10, claim filed 2026-03-22, which is 12 days later.
- Raises `NEW_POLICY`. Rule 1: Investigation, even though the claim is covered.

### Claim 6: Frequent claims

- Customer 6 has history filed 2025-12-05, 2026-02-14 and 2026-04-02. The claim is filed 2026-06-20.
- All three prior claims fall inside twelve months, so with the current claim the count is four. Raises `FREQUENT_CLAIMS`.
- Rule 1: Investigation.

### Claim 7: Theft with no police report

- Customer 3, policy 3, filed 2026-05-05. No police report number.
- Raises `THEFT_NO_POLICE_REPORT`. Customer 3 has two claims in twelve months with this one, so no `FREQUENT_CLAIMS`.
- The text says "sometime last week", so the incident date may be recorded as missing. If so, it is listed in `missing_fields`. The route is Investigation either way, because a fraud flag outranks missing fields.

### Claim 8: Missing required fields

- Customer 8, policy 8 (third party fire and theft, 2025-12-01 to 2026-11-30).
- The text gives no incident date and does not say whether anyone was injured.
- `incident_date` and `injured` stay NULL and are listed in `missing_fields`. The agent must not guess.
- No fraud flag, so the route is Adjuster-Queue and the explanation names the missing fields.
- Coverage cannot be set without an incident date, so `coverage_outcome` may be NULL.

### Claim 9: Policy not active on the incident date

- Customer 7, policy 7 ended 2024-12-31. Incident date is 2026-01-30.
- Coverage is Not covered and the explanation must name the inactive policy.
- Rule 2: Adjuster-Queue.

### Claim 10: Glass chip, covered

- Customer 1, policy 1. Glass damage with no injury is Low.
- No fraud flag: customer 1 has one prior claim in 2023, so two with the current claim.
- Routes to Auto-Approve only if confidence is above 0.9.

## Checks

- Fraud flags are raised only by the three rules in INTENT.md. The time or place mismatch flag is out of scope.
- Rerunning a claim replaces its `triage_results` row and its `triage_fraud_flags` rows.
- Every claim ends with a non-empty `explanation`.
- The routing order is: fraud flag, not covered, low severity and covered and confidence above 0.9, everything else. Missing required fields force Adjuster-Queue unless a fraud flag applies.
