export interface TriageModel {
  claim_id: number;
  incident_date: string | null;
  incident_place: string | null;
  parties: string | null;
  injured: boolean | null;
  description: string | null;
  missing_fields: string[];
  claim_type: string | null;
  severity: string | null;
  confidence: number | null;
  coverage_outcome: string | null;
  coverage_reason: string | null;
  fraud_flags: string[];
  route: string;
  explanation: string;
  created_at: string;
}
