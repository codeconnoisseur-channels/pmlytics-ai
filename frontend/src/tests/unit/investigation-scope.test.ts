import { describe, expect, it } from 'vitest';
import { buildUtcDateScope } from '@/lib/investigation-scope';

describe('buildUtcDateScope', () => {
  it('preserves the dates selected by the user regardless of local timezone', () => {
    expect(buildUtcDateScope('2026-08-28', '2026-08-31')).toEqual({
      start_time: '2026-08-28T00:00:00.000Z',
      end_time: '2026-08-31T23:59:59.000Z',
      timezone: 'UTC',
    });
  });
});
