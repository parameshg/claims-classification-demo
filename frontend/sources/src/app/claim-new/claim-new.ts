import { NgTemplateOutlet } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Store } from '@ngrx/store';
import { Banner } from '../banner/banner';
import { map, startWith } from 'rxjs';
import { NewClaimModel } from '../models/claim.model';
import { ConfigService } from '../services/config.service';
import { ClaimsActions } from '../store/claims.actions';
import { selectCreate } from '../store/claims.reducer';

@Component({
  selector: 'app-claim-new',
  imports: [NgTemplateOutlet, ReactiveFormsModule, RouterLink, Banner],
  templateUrl: './claim-new.html',
  styleUrl: './claim-new.css',
})
export class ClaimNew implements OnInit {
  private readonly store = inject(Store);
  private readonly fb = inject(FormBuilder);
  readonly config = inject(ConfigService);
  readonly create = this.store.selectSignal(selectCreate);
  readonly submitted = signal(false);

  readonly form = this.fb.nonNullable.group({
    customer_id: ['', Validators.required],
    policy_id: ['', Validators.required],
    filing_date: [today(), Validators.required],
    fnol_text: ['', [Validators.required, Validators.pattern(/\S/)]],
    police_report_number: [''],
  });

  private readonly customer = toSignal(
    this.form.controls.customer_id.valueChanges.pipe(startWith(this.form.controls.customer_id.value), map(String)),
    { initialValue: '' },
  );
  readonly customerChosen = computed(() => this.customer() !== '');
  readonly policies = computed(() =>
    this.config.data.policies.filter((p) => String(p.customer_id) === this.customer()),
  );

  capitalise(text: string): string {
    return text.charAt(0).toUpperCase() + text.slice(1);
  }

  constructor() {
    this.form.controls.customer_id.valueChanges.pipe(takeUntilDestroyed()).subscribe(() => {
      this.form.controls.policy_id.setValue('');
    });
  }

  ngOnInit(): void {
    this.store.dispatch(ClaimsActions.createReset());
  }

  invalid(name: keyof typeof this.form.controls): boolean {
    const c = this.form.controls[name];
    return c.invalid && (c.touched || this.submitted());
  }

  submit(): void {
    this.submitted.set(true);
    if (this.form.invalid || this.create().saving) {
      this.form.markAllAsTouched();
      return;
    }
    const v = this.form.getRawValue();
    const report = v.police_report_number.trim();
    const model: NewClaimModel = {
      customer_id: Number(v.customer_id),
      policy_id: Number(v.policy_id),
      filing_date: v.filing_date,
      fnol_text: v.fnol_text,
      police_report_number: report === '' ? null : report,
    };
    this.store.dispatch(ClaimsActions.createRequested({ model }));
  }
}

function today(): string {
  const d = new Date();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${m}-${day}`;
}
