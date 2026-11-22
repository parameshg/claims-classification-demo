import { createActionGroup, emptyProps, props } from '@ngrx/store';
import { DetailModel, FilterModel, NewClaimModel, PageModel } from '../models/claim.model';
import { ErrorModel } from '../models/error.model';
import { TriageModel } from '../models/triage.model';

export const ClaimsActions = createActionGroup({
  source: 'Claims',
  events: {
    'List Requested': props<{ filter: FilterModel }>(),
    'List Loaded': props<{ page: PageModel }>(),
    'List Failed': props<{ error: ErrorModel }>(),

    'Detail Requested': props<{ id: number }>(),
    'Detail Loaded': props<{ detail: DetailModel; triage: TriageModel | null }>(),
    'Detail Failed': props<{ error: ErrorModel }>(),

    'Triage Requested': props<{ id: number }>(),
    'Triage Succeeded': props<{ triage: TriageModel }>(),
    'Triage Failed': props<{ error: ErrorModel }>(),

    'Create Requested': props<{ model: NewClaimModel }>(),
    'Create Succeeded': props<{ claimId: number }>(),
    'Create Triage Failed': props<{ claimId: number; error: ErrorModel }>(),
    'Create Failed': props<{ error: ErrorModel }>(),
    'Create Reset': emptyProps(),
  },
});
