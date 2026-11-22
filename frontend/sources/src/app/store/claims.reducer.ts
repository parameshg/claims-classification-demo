import { createFeature, createReducer, on } from '@ngrx/store';
import { DetailModel, FilterModel, SummaryModel } from '../models/claim.model';
import { ErrorModel } from '../models/error.model';
import { TriageModel } from '../models/triage.model';
import { ClaimsActions } from './claims.actions';

export type Status = 'idle' | 'loading' | 'loaded' | 'error';

export interface ClaimsState {
  list: { items: SummaryModel[]; total: number; status: Status; error: ErrorModel | null };
  filter: FilterModel;
  detail: {
    claimId: number | null;
    data: DetailModel | null;
    triage: TriageModel | null;
    status: Status;
    error: ErrorModel | null;
    running: boolean;
    runError: ErrorModel | null;
  };
  create: { saving: boolean; error: ErrorModel | null; carriedError: ErrorModel | null };
  announcement: string;
}

export const initialState: ClaimsState = {
  list: { items: [], total: 0, status: 'idle', error: null },
  filter: { route: null, untriaged: false, offset: 0 },
  detail: { claimId: null, data: null, triage: null, status: 'idle', error: null, running: false, runError: null },
  create: { saving: false, error: null, carriedError: null },
  announcement: '',
};

export const claimsFeature = createFeature({
  name: 'claims',
  reducer: createReducer(
    initialState,
    on(ClaimsActions.listRequested, (s, { filter }) => ({
      ...s,
      filter,
      list: { ...s.list, status: 'loading' as Status, error: null },
    })),
    on(ClaimsActions.listLoaded, (s, { page }) => ({
      ...s,
      list: { items: page.items, total: page.total, status: 'loaded' as Status, error: null },
      announcement: `${page.total} claims found.`,
    })),
    on(ClaimsActions.listFailed, (s, { error }) => ({
      ...s,
      list: { ...s.list, status: 'error' as Status, error },
      announcement: `Error: ${error.message}`,
    })),

    on(ClaimsActions.detailRequested, (s, { id }) => ({
      ...s,
      detail: { ...initialState.detail, claimId: id, status: 'loading' as Status },
    })),
    on(ClaimsActions.detailLoaded, (s, { detail, triage }) => ({
      ...s,
      detail: {
        ...s.detail,
        data: detail,
        triage,
        status: 'loaded' as Status,
        error: null,
        runError: s.create.carriedError,
      },
      create: { ...s.create, carriedError: null },
    })),
    on(ClaimsActions.detailFailed, (s, { error }) => ({
      ...s,
      detail: { ...s.detail, status: 'error' as Status, error },
      announcement: `Error: ${error.message}`,
    })),

    on(ClaimsActions.triageRequested, (s) => ({
      ...s,
      detail: { ...s.detail, running: true, runError: null },
      announcement: 'Triage running.',
    })),
    on(ClaimsActions.triageSucceeded, (s, { triage }) => ({
      ...s,
      detail: { ...s.detail, running: false, triage, runError: null },
      announcement: 'Triage done.',
    })),
    on(ClaimsActions.triageFailed, (s, { error }) => ({
      ...s,
      detail: { ...s.detail, running: false, runError: error },
      announcement: 'Triage failed. The previous result, if any, is unchanged.',
    })),

    on(ClaimsActions.createRequested, (s) => ({
      ...s,
      create: { saving: true, error: null, carriedError: null },
      announcement: 'Creating claim and running triage.',
    })),
    on(ClaimsActions.createSucceeded, (s) => ({ ...s, create: { ...s.create, saving: false } })),
    on(ClaimsActions.createTriageFailed, (s, { error }) => ({
      ...s,
      create: { saving: false, error: null, carriedError: error },
    })),
    on(ClaimsActions.createFailed, (s, { error }) => ({
      ...s,
      create: { saving: false, error, carriedError: null },
      announcement: `Error: ${error.message}`,
    })),
    on(ClaimsActions.createReset, (s) => ({ ...s, create: { saving: false, error: null, carriedError: null } })),
  ),
});

export const {
  selectList,
  selectFilter,
  selectDetail,
  selectCreate,
  selectAnnouncement,
} = claimsFeature;
