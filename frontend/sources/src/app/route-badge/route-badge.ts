import { Component, computed, inject, input } from '@angular/core';
import { ConfigService } from '../services/config.service';

@Component({
  selector: 'app-route-badge',
  templateUrl: './route-badge.html',
  styleUrl: './route-badge.css',
})
export class RouteBadge {
  private readonly config = inject(ConfigService);
  readonly route = input<string | null>(null);
  readonly size = input<'sm' | 'lg'>('sm');
  readonly emptyLabel = input<string>('Unclassified');
  readonly info = computed(() => {
    const value = this.route();
    return value ? this.config.route(value) : undefined;
  });
}
