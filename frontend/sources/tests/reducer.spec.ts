import { ClaimsActions } from '../src/app/store/claims.actions';
import { claimsFeature, initialState } from '../src/app/store/claims.reducer';

const reduce = claimsFeature.reducer;

describe('claims reducer', () => {
  it('marks the list as loading and keeps the filter', () => {
    const filter = { route: 'Investigation', untriaged: false, offset: 0 };
    const s = reduce(initialState, ClaimsActions.listRequested({ filter }));
    expect(s.list.status).toBe('loading');
    expect(s.filter).toEqual(filter);
  });

  it('stores a loaded page', () => {
    const s = reduce(initialState, ClaimsActions.listLoaded({ page: { items: [], total: 0 } }));
    expect(s.list.status).toBe('loaded');
  });

  it('keeps the previous triage when a re-run fails', () => {
    const triage = { claim_id: 1, route: 'Adjuster-Queue' } as never;
    const loaded = reduce(initialState, ClaimsActions.triageSucceeded({ triage }));
    const failed = reduce(
      loaded,
      ClaimsActions.triageFailed({ error: { status: 502, code: 'llm_failed', message: 'x' } }),
    );
    expect(failed.detail.triage).toBe(triage);
    expect(failed.detail.running).toBe(false);
    expect(failed.detail.runError?.code).toBe('llm_failed');
  });

  it('carries a post-create triage error to the detail screen', () => {
    const error = { status: 502, code: 'llm_failed', message: 'x' };
    const s1 = reduce(initialState, ClaimsActions.createTriageFailed({ claimId: 3, error }));
    const s2 = reduce(s1, ClaimsActions.detailLoaded({ detail: {} as never, triage: null }));
    expect(s2.detail.runError).toEqual(error);
    expect(s2.create.carriedError).toBeNull();
  });
});
