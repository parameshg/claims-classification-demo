import { Component, computed, inject, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Store } from '@ngrx/store';
import { Banner } from '../banner/banner';
import { NaPipe } from '../pipes/na.pipe';
import { RouteBadge } from '../route-badge/route-badge';
import { ConfigService } from '../services/config.service';
import { ClaimsActions } from '../store/claims.actions';
import { selectFilter, selectList } from '../store/claims.reducer';

@Component({
  selector: 'app-claim-list',
  imports: [RouterLink, Banner, RouteBadge, NaPipe],
  templateUrl: './claim-list.html',
  styleUrl: './claim-list.css',
})
export class ClaimList implements OnInit {
  private readonly store = inject(Store);
  readonly config = inject(ConfigService);
  readonly list = this.store.selectSignal(selectList);
  readonly filter = this.store.selectSignal(selectFilter);
  readonly pageSize = this.config.data.pageSize;
  readonly skeleton = [0, 1, 2, 3, 4];
  readonly columns = [0, 1, 2, 3, 4];

  readonly loading = computed(() => this.list().status === 'loading' || this.list().status === 'idle');
  readonly from = computed(() => (this.list().total === 0 ? 0 : this.filter().offset + 1));
  readonly to = computed(() => Math.min(this.filter().offset + this.pageSize, this.list().total));
  readonly hasPrev = computed(() => this.filter().offset > 0);
  readonly hasNext = computed(() => this.filter().offset + this.pageSize < this.list().total);

  ngOnInit(): void {
    this.load(this.filter());
  }

  load(filter = this.filter()): void {
    this.store.dispatch(ClaimsActions.listRequested({ filter }));
  }

  setRoute(value: string | null): void {
    this.load({ ...this.filter(), route: value, offset: 0 });
  }

  setUntriaged(event: Event): void {
    this.load({ ...this.filter(), untriaged: (event.target as HTMLInputElement).checked, offset: 0 });
  }

  prev(): void {
    this.load({ ...this.filter(), offset: Math.max(0, this.filter().offset - this.pageSize) });
  }

  next(): void {
    this.load({ ...this.filter(), offset: this.filter().offset + this.pageSize });
  }
}
