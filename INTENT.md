## Purpose

This is a claim agent for motor insurance. The agent reads a new claim, classifies it, checks it against the policy, flags fraud signals, and recommends a route. It is decision support only: it never pays, denies or settles a claim. Terms are defined in [GLOSSARY.md](GLOSSARY.md).

## Scope

- In-scope: FNOL text, policy summary, claim history, claim type, severity, coverage outcome, fraud flags, route.
- Out-of-scope for v1: photos and image analysis, payments, settlement negotiation, repair shop integration, total loss assessment, drivers other than the policyholder, adjuster feedback or override, and the Fraud flag for an incident time or place that does not match the description.

## Claim Types

- Collision: vehicle hits another vehicle or object.
- Theft: vehicle or contents stolen.
- Glass: windscreen or window damage only.
- Weather: hail, flood, storm, falling tree.
- Vandalism: deliberate damage by a third party.

## Coverage Outcome

- Covered: the policy was active on the incident date and does not exclude the event.
- Not covered: the policy excludes the event, or was not active on the incident date.

## Severity Levels

- Low: cosmetic damage, no injury, no third party.
- Medium: drivable or repairable, no injury, no third party.
- High: not drivable, injury reported, a third party involved, or any theft.
- Glass is Low unless an injury is reported. Hitting a fixed object alone does not involve a third party.

## Inputs and Data Sources

- FNOL text written by the customer.
- Policy summary: cover type, excess, start and end dates, exclusions.
- Synthetic claim history for the same customer.
- All inputs live in a SQLite database. Each claim has one triage result stored there; running a claim again replaces it.

## Agent Workflow

An LLM handles steps 1 and 2. Plain code handles steps 3, 4 and 5, so the same input always gives the same answer.

1. Intake: extract the structured fields from the FNOL text (incident date, place, parties, injuries, description). The required fields are incident date, claim type, and whether anyone was injured.
2. Classify: assign claim type and severity with a confidence score.
3. Policy check: compare the incident date and event to the policy dates and exclusions to set the coverage outcome. The outcome stays empty when the incident date or claim type is missing.
4. Fraud raise: raise fraud flags for rule matches.
5. Route and explain: record the missing required fields, recommend auto-approve, adjuster queue or investigation, and build a short explanation the adjuster can read in ten seconds. The explanation is assembled from the results of steps 2 to 4 and has no LLM call. It states the claim type, severity and confidence, the coverage outcome and reason, any fraud flags, any missing fields, and the route taken.

If a required field is missing or unclear, the agent does not guess. The claim goes to the adjuster queue and the explanation names the missing field.

## Fraud Flags (rule based)

- Claim filed within 30 days of policy start (measured from the filing date).
- Same customer has three or more claims in twelve months, counting the current claim.
- Theft claim with no police report number.

## Routing Rules

Apply in this order. The first match wins.

1. Any fraud flag: Investigation.
2. Any missing required field (incident date, claim type, injured): Adjuster queue, with the explanation naming the missing fields.
3. Not covered: Adjuster queue, with the explanation naming the policy exclusion or inactive policy.
4. Low severity, covered, and confidence above 0.9: Auto-approve.
5. Everything else: Adjuster queue.

Missing required fields override the not-covered and auto-approve rules. A fraud flag still sends the claim to investigation.