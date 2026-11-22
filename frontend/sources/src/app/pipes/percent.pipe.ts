import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'pct' })
export class PercentPipe implements PipeTransform {
  transform(value: number | null | undefined): string {
    return value === null || value === undefined ? 'Not Available' : `${Math.round(value * 100)}%`;
  }
}
