import { NgTemplateOutlet } from '@angular/common';
import { Component, DestroyRef, computed, inject, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Store } from '@ngrx/store';
import { Banner } from '../banner/banner';
import { NaPipe } from '../pipes/na.pipe';
import { PercentPipe } from '../pipes/percent.pipe';
import { YesNoPipe } from '../pipes/yesno.pipe';
import { RouteBadge } from '../route-badge/route-badge';
import { ConfigService } from '../services/config.service';
import { ClaimsActions } from '../store/claims.actions';
import { selectDetail } from '../store/claims.reducer';

@Component({
  selector: 'app-claim-detail',
  imports: [NgTemplateOutlet, RouterLink, Banner, RouteBadge, NaPipe, YesNoPipe, PercentPipe],
  templateUrl: './claim-detail.html',
  styleUrl: './claim-detail.css',
})
export class ClaimDetail implements OnInit {
  private readonly store = inject(Store);
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);
  readonly config = inject(ConfigService);
  readonly detail = this.store.selectSignal(selectDetail);
  readonly confirming = signal(false);

  readonly lowCovered = computed(() => {
    const t = this.detail().triage;
    return !!t && t.severity === 'Low' && t.coverage_outcome === 'Covered' && t.route !== 'Auto-Approve';
  });

  ngOnInit(): void {
    this.route.paramMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      const id = Number(params.get('claimId'));
      this.confirming.set(false);
      if (Number.isInteger(id) && id > 0) {
        this.store.dispatch(ClaimsActions.detailRequested({ id }));
      }
    });
  }

  reload(): void {
    const id = this.detail().claimId;
    if (id !== null) this.store.dispatch(ClaimsActions.detailRequested({ id }));
  }

  run(): void {
    const id = this.detail().claimId;
    if (id === null) return;
    this.confirming.set(false);
    this.store.dispatch(ClaimsActions.triageRequested({ id }));
  }

  askRerun(): void {
    this.confirming.set(true);
  }

  cancelRerun(): void {
    this.confirming.set(false);
  }

  get notFound(): boolean {
    const d = this.detail();
    return d.status === 'error' && d.error?.code === 'claim_not_found';
  }

  get invalidId(): boolean {
    const id = Number(this.route.snapshot.paramMap.get('claimId'));
    return !Number.isInteger(id) || id <= 0;
  }

  runMessage(): string {
    const e = this.detail().runError;
    if (!e) return '';
    return e.code === 'llm_failed'
      ? 'Triage failed. The previous result, if any, is unchanged.'
      : e.message;
  }
}
