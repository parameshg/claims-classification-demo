import { DOCUMENT } from '@angular/common';
import { Injectable, effect, inject, signal } from '@angular/core';

export type Mode = 'light' | 'dark';
const KEY = 'claims-theme';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly doc = inject(DOCUMENT);
  readonly mode = signal<Mode>(this.initial());

  constructor() {
    effect(() => {
      const mode = this.mode();
      this.doc.documentElement.classList.toggle('dark', mode === 'dark');
      try {
        localStorage.setItem(KEY, mode);
      } catch {
        /* storage unavailable */
      }
    });
  }

  toggle(): void {
    this.mode.update((m) => (m === 'dark' ? 'light' : 'dark'));
  }

  private initial(): Mode {
    try {
      const saved = localStorage.getItem(KEY);
      if (saved === 'light' || saved === 'dark') return saved;
    } catch {
      /* storage unavailable */
    }
    return this.doc.defaultView?.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
}
