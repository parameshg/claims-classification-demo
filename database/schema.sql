PRAGMA foreign_keys = ON;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    full_name   TEXT NOT NULL
);

CREATE TABLE policies (
    policy_id   INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (customer_id),
    cover_type  TEXT NOT NULL,
    excess      NUMERIC NOT NULL CHECK (excess >= 0),
    start_date  TEXT NOT NULL,
    end_date    TEXT NOT NULL CHECK (end_date >= start_date),
    exclusions  TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE claims (
    claim_id             INTEGER PRIMARY KEY,
    customer_id          INTEGER NOT NULL REFERENCES customers (customer_id),
    policy_id            INTEGER NOT NULL REFERENCES policies (policy_id),
    filing_date          TEXT NOT NULL,
    fnol_text            TEXT NOT NULL,
    police_report_number TEXT NULL
);

CREATE TABLE claim_history (
    history_id  INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (customer_id),
    filing_date TEXT NOT NULL,
    claim_type  TEXT NOT NULL CHECK (claim_type IN ('Collision','Theft','Glass','Weather','Vandalism'))
);
CREATE INDEX idx_history_customer_date ON claim_history (customer_id, filing_date);

CREATE TABLE triage_results (
    claim_id         INTEGER PRIMARY KEY REFERENCES claims (claim_id) ON DELETE CASCADE,
    incident_date    TEXT NULL,
    incident_place   TEXT NULL,
    parties          TEXT NULL,
    injured          INTEGER NULL CHECK (injured IN (0, 1)),
    description      TEXT NULL,
    missing_fields   TEXT NOT NULL DEFAULT '[]',
    claim_type       TEXT NULL CHECK (claim_type IN ('Collision','Theft','Glass','Weather','Vandalism')),
    severity         TEXT NULL CHECK (severity IN ('Low','Medium','High')),
    confidence       REAL NULL CHECK (confidence BETWEEN 0 AND 1),
    coverage_outcome TEXT NULL CHECK (coverage_outcome IN ('Covered','Not covered')),
    coverage_reason  TEXT NULL,
    route            TEXT NOT NULL CHECK (route IN ('Auto-Approve','Adjuster-Queue','Investigation')),
    explanation      TEXT NOT NULL,
    created_at       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE triage_fraud_flags (
    claim_id INTEGER NOT NULL REFERENCES triage_results (claim_id) ON DELETE CASCADE,
    flag     TEXT NOT NULL CHECK (flag IN ('NEW_POLICY','FREQUENT_CLAIMS','THEFT_NO_POLICE_REPORT')),
    PRIMARY KEY (claim_id, flag)
);
