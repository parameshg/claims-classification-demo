import { Injectable, inject } from '@angular/core';
import { Router } from '@angular/router';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { catchError, forkJoin, map, of, switchMap, tap, exhaustMap, throwError } from 'rxjs';
import { ErrorModel } from '../models/error.model';
import { ClaimsService } from '../services/claims.service';
import { ClaimsActions } from './claims.actions';

@Injectable()
export class ClaimsEffects {
  private readonly actions = inject(Actions);
  private readonly api = inject(ClaimsService);
  private readonly router = inject(Router);

  list = createEffect(() =>
    this.actions.pipe(
      ofType(ClaimsActions.listRequested),
      switchMap(({ filter }) =>
        this.api.list(filter).pipe(
          map((page) => ClaimsActions.listLoaded({ page })),
          catchError((error: ErrorModel) => of(ClaimsActions.listFailed({ error }))),
        ),
      ),
    ),
  );

  detail = createEffect(() =>
    this.actions.pipe(
      ofType(ClaimsActions.detailRequested),
      switchMap(({ id }) =>
        forkJoin({
          detail: this.api.get(id),
          triage: this.api.triage(id).pipe(
            catchError((error: ErrorModel) => (error.status === 404 ? of(null) : throwError(() => error))),
          ),
        }).pipe(
          map(({ detail, triage }) => ClaimsActions.detailLoaded({ detail, triage })),
          catchError((error: ErrorModel) => of(ClaimsActions.detailFailed({ error }))),
        ),
      ),
    ),
  );

  triage = createEffect(() =>
    this.actions.pipe(
      ofType(ClaimsActions.triageRequested),
      exhaustMap(({ id }) =>
        this.api.run(id).pipe(
          map((triage) => ClaimsActions.triageSucceeded({ triage })),
          catchError((error: ErrorModel) => of(ClaimsActions.triageFailed({ error }))),
        ),
      ),
    ),
  );

  create = createEffect(() =>
    this.actions.pipe(
      ofType(ClaimsActions.createRequested),
      exhaustMap(({ model }) =>
        this.api.create(model).pipe(
          switchMap((claim) =>
            this.api.run(claim.claim_id).pipe(
              map(() => ClaimsActions.createSucceeded({ claimId: claim.claim_id })),
              catchError((error: ErrorModel) =>
                of(ClaimsActions.createTriageFailed({ claimId: claim.claim_id, error })),
              ),
            ),
          ),
          catchError((error: ErrorModel) => of(ClaimsActions.createFailed({ error }))),
        ),
      ),
    ),
  );

  open = createEffect(
    () =>
      this.actions.pipe(
        ofType(ClaimsActions.createSucceeded, ClaimsActions.createTriageFailed),
        tap(({ claimId }) => this.router.navigate(['/claims', claimId])),
      ),
    { dispatch: false },
  );
}
