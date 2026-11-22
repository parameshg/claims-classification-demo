import { Component, input, output } from '@angular/core';

@Component({
  selector: 'app-banner',
  templateUrl: './banner.html',
  styleUrl: './banner.css',
})
export class Banner {
  readonly message = input.required<string>();
  readonly retryLabel = input<string>('Try again');
  readonly retryable = input<boolean>(true);
  readonly retry = output<void>();
}
