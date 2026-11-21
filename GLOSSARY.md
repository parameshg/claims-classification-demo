# Motor Claims Triage

A decision-support agent that reads a newly reported motor insurance claim and recommends where it should be routed. It never pays, denies or settles a claim.

## Language

**Claim**:
A customer's request to be compensated under their policy for one incident.
_Avoid_: Case, ticket

**FNOL (first notice of loss)**:
The customer's own free-text account of the incident, as first reported.
_Avoid_: Claim form, report

**Customer**:
The policyholder who files a claim. Each customer has one active policy at a time.
_Avoid_: Client, claimant, driver, account

**Policy**:
The customer's insurance contract, summarised by cover type, excess, start and end dates, and exclusions.
_Avoid_: Plan, account

**Incident date**:
The date the event happened, as stated in the FNOL. It decides whether the policy was active.

**Filing date**:
The date the customer reported the claim. It is the date used for the "within 30 days of policy start" fraud flag.
_Avoid_: Claim date

**Claim history**:
The earlier claims on record for the same customer.

**Required fields**:
The facts the agent must extract from the FNOL before it will classify a claim: Incident date, Claim type, and whether anyone was injured. If any is missing the claim goes to the Adjuster queue.

### Assessments

**Claim type**:
What kind of incident happened: Collision, Theft, Glass, Weather or Vandalism.
_Avoid_: Category, claim category

**Severity**:
How serious the incident is. Low is cosmetic damage with no injury and no third party. High is a vehicle that cannot be driven, a reported injury, a third party involved, or any theft. Medium is everything between. Glass is low unless an injury is reported.

**Third party**:
A person or a vehicle owned by someone other than the policyholder who is affected by the incident. Hitting a fixed object alone does not involve a Third party.
_Avoid_: Other party

**Confidence**:
How sure the agent is of its claim type and severity, from 0 to 1.

**Coverage outcome**:
Whether the policy covers the incident: covered or not covered.
_Avoid_: Not covered as a claim type

**Fraud flag**:
A rule-based signal that a claim deserves closer scrutiny. A flag is not a finding of fraud. The flags are: filed within 30 days of policy start, three or more claims by the same customer in twelve months (counting the current claim), and a Theft claim with no police report number.

### Routing

**Route**:
The queue the agent recommends for a claim: Auto-approve, Adjuster queue or Investigation.
_Avoid_: Decision, outcome

**Auto-approve**:
A Route meaning the claim is fast-tracked with no human review needed before it moves on. It is not a payment.
_Avoid_: Approved, paid

**Adjuster queue**:
A Route for claims a human claims adjuster must review.

**Investigation**:
A Route for claims sent to special investigations because of a Fraud flag.
_Avoid_: SIU queue

**Triage result**:
The single record the agent produces for a claim: Claim type, severity, confidence, coverage outcome, fraud flags, route and explanation. Running a claim again replaces its earlier result.
_Avoid_: Decision, verdict

**Explanation**:
The short written reason for a route, readable by an adjuster in ten seconds.
_Avoid_: Summary, justification
