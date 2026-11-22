import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, catchError, throwError } from 'rxjs';
import { ClaimModel, DetailModel, FilterModel, NewClaimModel, PageModel } from '../models/claim.model';
import { ErrorModel } from '../models/error.model';
import { TriageModel } from '../models/triage.model';
import { ConfigService } from './config.service';

export function toError(err: unknown): ErrorModel {
  if (err instanceof HttpErrorResponse) {
    if (err.status === 0) {
      return { status: 0, code: 'network', message: 'Could not reach the server.' };
    }
    const body = err.error?.error;
    return {
      status: err.status,
      code: body?.code ?? 'unknown',
      message: body?.message ?? 'Something went wrong.',
    };
  }
  return { status: 0, code: 'unknown', message: 'Something went wrong.' };
}

@Injectable({ providedIn: 'root' })
export class ClaimsService {
  private readonly http = inject(HttpClient);
  private readonly config = inject(ConfigService);
  private readonly base = '/api/v1/claims';

  list(filter: FilterModel): Observable<PageModel> {
    let params = new HttpParams().set('limit', this.config.data.pageSize).set('offset', filter.offset);
    if (filter.route) params = params.set('route', filter.route);
    if (filter.untriaged) params = params.set('triaged', 'false');
    return this.http.get<PageModel>(this.base, { params }).pipe(catchError((e) => throwError(() => toError(e))));
  }

  get(id: number): Observable<DetailModel> {
    return this.http.get<DetailModel>(`${this.base}/${id}`).pipe(catchError((e) => throwError(() => toError(e))));
  }

  triage(id: number): Observable<TriageModel> {
    return this.http.get<TriageModel>(`${this.base}/${id}/triage`).pipe(catchError((e) => throwError(() => toError(e))));
  }

  run(id: number): Observable<TriageModel> {
    return this.http.post<TriageModel>(`${this.base}/${id}/triage`, null).pipe(catchError((e) => throwError(() => toError(e))));
  }

  create(model: NewClaimModel): Observable<ClaimModel> {
    return this.http.post<ClaimModel>(this.base, model).pipe(catchError((e) => throwError(() => toError(e))));
  }
}
