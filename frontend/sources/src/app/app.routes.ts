import { Routes } from '@angular/router';
import { ClaimDetail } from './claim-detail/claim-detail';
import { ClaimList } from './claim-list/claim-list';
import { ClaimNew } from './claim-new/claim-new';
import { NotFound } from './not-found/not-found';

export const routes: Routes = [
  { path: '', component: ClaimList, title: 'Claims' },
  { path: 'claims/new', component: ClaimNew, title: 'New claim' },
  { path: 'claims/:claimId', component: ClaimDetail, title: 'Claim' },
  { path: '**', component: NotFound, title: 'Not found' },
];
