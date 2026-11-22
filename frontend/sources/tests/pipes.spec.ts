import { NaPipe } from '../src/app/pipes/na.pipe';
import { PercentPipe } from '../src/app/pipes/percent.pipe';
import { YesNoPipe } from '../src/app/pipes/yesno.pipe';

describe('pipes', () => {
  it('shows Not Available for null and blank', () => {
    const na = new NaPipe();
    expect(na.transform(null)).toBe('Not Available');
    expect(na.transform('')).toBe('Not Available');
    expect(na.transform('Glass')).toBe('Glass');
  });

  it('formats Yes, No and unknown', () => {
    const p = new YesNoPipe();
    expect(p.transform(true)).toBe('Yes');
    expect(p.transform(false)).toBe('No');
    expect(p.transform(null)).toBe('Not Available');
  });

  it('rounds confidence to a whole percent', () => {
    const p = new PercentPipe();
    expect(p.transform(0.82)).toBe('82%');
    expect(p.transform(null)).toBe('Not Available');
  });
});
