export interface ClaimModel {
  claim_id: number;
  customer_id: number;
  policy_id: number;
  filing_date: string;
  fnol_text: string;
  police_report_number: string | null;
}

export interface NewClaimModel {
  customer_id: number;
  policy_id: number;
  filing_date: string;
  fnol_text: string;
  police_report_number: string | null;
}

export interface PolicyModel {
  policy_id: number;
  cover_type: string;
  excess: number;
  start_date: string;
  end_date: string;
  exclusions: string[];
}

export interface HistoryModel {
  history_id: number;
  filing_date: string;
  claim_type: string;
}

export interface DetailModel {
  claim: ClaimModel;
  policy: PolicyModel;
  history: HistoryModel[];
}

export interface SummaryModel {
  claim_id: number;
  customer_id: number;
  filing_date: string;
  claim_type: string | null;
  severity: string | null;
  route: string | null;
}

export interface PageModel {
  items: SummaryModel[];
  total: number;
}

export interface FilterModel {
  route: string | null;
  untriaged: boolean;
  offset: number;
}
