export interface RouteModel {
  value: string;
  label: string;
  hint: string;
}

export interface CustomerModel {
  customer_id: number;
  full_name: string;
}

export interface PolicyOptionModel {
  policy_id: number;
  customer_id: number;
  cover_type: string;
  start_date: string;
  end_date: string;
}

export interface ConfigModel {
  pageSize: number;
  routes: RouteModel[];
  fraudFlags: Record<string, string>;
  customers: CustomerModel[];
  policies: PolicyOptionModel[];
}
