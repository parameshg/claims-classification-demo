# Frontend UI

UI spec for the motor claim agent, for adjusters. Derived from [backend/API.md](../backend/API.md) and [INTENT.md](../INTENT.md); terms are defined in [GLOSSARY.md](../GLOSSARY.md).

The UI is decision support only. It shows the agent's recommendation. It has no control to pay, deny, settle, or override a route (all out of scope for v1).

## Users and Goal

The user is a claims adjuster. They need to see which claims need attention, read the agent's recommendation in about ten seconds, and check the evidence behind it.

## Screens

| Screen | Path | API calls |
|---|---|---|
| Claim list | `/` | `GET /claims` |
| Claim detail | `/claims/:claim_id` | `GET /claims/{id}`, `GET /claims/{id}/triage`, `POST /claims/{id}/triage` |
| New claim | `/claims/new` | `POST /claims`, then `POST /claims/{id}/triage` |

### Claim list

A table with one row per claim.

| Column | Source | Notes |
|---|---|---|
| Claim | `claim_id` | Links to the detail screen. |
| Filed | `filing_date` | |
| Type | `claim_type` | Shows "Not triaged" when null. |
| Severity | `severity` | |
| Route | `route` | Shown as a badge (see [Route badges](#route-badges)). |

Controls:

- Route filter (All, Auto-Approve, Adjuster-Queue, Investigation), sent as `route`.
- "Not triaged" toggle, sent as `triaged=false`.
- Paging with 50 rows per page, using `limit` and `offset`. Shows `total`.
- "New Claim" button.

Empty state: "No claims match these filters."

### Claim detail

Top to bottom:

1. **Header.** Claim id, filing date, and the route badge.
2. **Explanation.** The `explanation` text, large and first, so it can be read in ten seconds. Below it, the claim type, severity and confidence.
3. **Missing fields.** Shown only when `missing_fields` is not empty. Lists each field name. Appears above everything else in the body because the agent did not guess.
4. **Fraud flags.** Shown only when `fraud_flags` is not empty. Each flag shows a plain-language label (see [Fraud flag labels](#fraud-flag-labels)).
5. **Coverage.** `coverage_outcome`, and `coverage_reason` when not covered. Also the policy summary: cover type, excess, start and end dates, exclusions.
6. **Extracted details.** Incident date, place, parties, injured (Yes or No), description.
7. **Original FNOL text.** The customer's `fnol_text`, so the adjuster can check the extraction against the source. Also shows `police_report_number` or "None".
8. **Claim history.** Table of prior claims (date and type) from `history`.
9. **Actions.** "Run triage" if none exists, "Re-run triage" otherwise.

Re-running asks for confirmation: "This replaces the current triage result." On confirm, the screen calls `POST /claims/{id}/triage` and shows the new result.

If `GET /claims/{id}/triage` returns `404`, the claim has not been triaged. Show the FNOL text, policy and history, and a "Run triage" button in place of sections 2 to 6.

### New claim

A form with these fields:

| Field | Required | Control |
|---|---|---|
| Customer | yes | Select, by `customer_id`. |
| Policy | yes | Select, limited to the chosen customer's policies. |
| Filing date | yes | Date input, defaults to today. |
| FNOL text | yes | Multi-line text. |
| Police report number | no | Text. |

On submit, the UI creates the claim, then runs triage, then opens the detail screen. If the claim is created but triage fails, it opens the detail screen with the "Run triage" button and an error message.

## Components

### Route badges

| Route | Label | Meaning shown on hover |
|---|---|---|
| `Auto-Approve` | Auto-approve | Low severity, covered, confidence above 0.9. |
| `Adjuster-Queue` | Adjuster queue | Needs a person to review. |
| `Investigation` | Investigation | A fraud flag was raised. |

Colour is never the only signal. Every badge carries its text label.

### Fraud flag labels

| Flag | Label |
|---|---|
| `NEW_POLICY` | Filed within 30 days of policy start |
| `FREQUENT_CLAIMS` | Three or more claims in twelve months (including this one) |
| `THEFT_NO_POLICE_REPORT` | Theft claim with no police report number |

### Confidence

Shown as a percentage to the nearest whole number (0.82 as 82%). A note beside it reads "Auto-approve needs more than 90%" when the claim is Low severity and covered but the route is not auto-approve.

## States

| State | Behaviour |
|---|---|
| Loading | Skeleton rows on the list. A spinner on the detail screen. |
| Triage running | "Run triage" button disabled with a spinner. The LLM steps can take several seconds. Other sections stay visible. |
| `400 invalid_request` | Show the `message` next to the form. |
| `404 claim_not_found` | Full-page "Claim not found" with a link to the list. |
| `502 llm_failed` | Banner: "Triage failed. The previous result, if any, is unchanged." With a "Try again" button. |
| Network error | Banner with a "Try again" button. |

## Behaviour Rules

- Null fields show "Not Available", never a blank or a guess.
- The UI does not recompute coverage, flags or routes. It displays what the API returns.
- All text is rendered as plain text, including `fnol_text` and `explanation`.
- Dates display as stored (`YYYY-MM-DD`).

## Accessibility

- Every interactive element is reachable and usable by keyboard.
- Form fields have visible labels and error messages tied to the field.
- Status changes (triage running, triage done, errors) are announced to screen readers.
- Text and badge contrast meets WCAG AA.

## Out of Scope for v1

Photo upload or viewing, payment or settlement actions, adjuster override or feedback, repair shop views, total loss assessment, other drivers, and login. Any display of the incident time or place mismatch flag is also out.
