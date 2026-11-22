import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'na' })
export class NaPipe implements PipeTransform {
  transform(value: unknown): string {
    return value === null || value === undefined || value === '' ? 'Not Available' : String(value);
  }
}
