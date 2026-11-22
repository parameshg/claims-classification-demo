import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ConfigModel, CustomerModel, PolicyOptionModel, RouteModel } from '../models/config.model';

const PAGE_SIZE = 50;

const ROUTES: RouteModel[] = [
  { value: 'Auto-Approve', label: 'Auto Approve', hint: 'Low severity, covered, confidence above 0.9.' },
  { value: 'Adjuster-Queue', label: 'Adjuster Queue', hint: 'Needs a person to review.' },
  { value: 'Investigation', label: 'Investigation', hint: 'A fraud flag was raised.' },
];

const FRAUD_FLAGS: Record<string, string> = {
  NEW_POLICY: 'Filed within 30 days of policy start',
  FREQUENT_CLAIMS: 'Three or more claims in twelve months (including this one)',
  THEFT_NO_POLICE_REPORT: 'Theft claim with no police report number',
};

@Injectable({ providedIn: 'root' })
export class ConfigService {
  private readonly http = inject(HttpClient);
  private config: ConfigModel = {
    pageSize: PAGE_SIZE,
    routes: ROUTES,
    fraudFlags: FRAUD_FLAGS,
    customers: [],
    policies: [],
  };

  async load(): Promise<void> {
    const [customers, policies] = await Promise.all([
      firstValueFrom(this.http.get<CustomerModel[]>('/api/v1/customers')).catch(() => []),
      firstValueFrom(this.http.get<PolicyOptionModel[]>('/api/v1/policies')).catch(() => []),
    ]);
    this.config = { ...this.config, customers, policies };
  }

  get data(): ConfigModel {
    return this.config;
  }

  route(value: string): RouteModel | undefined {
    return this.config.routes.find((r) => r.value === value);
  }

  flag(value: string): string {
    return this.config.fraudFlags[value] ?? value;
  }
}
