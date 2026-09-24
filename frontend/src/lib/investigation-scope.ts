export function buildUtcDateScope(startDate: string, endDate: string) {
  return {
    start_time: new Date(`${startDate}T00:00:00Z`).toISOString(),
    end_time: new Date(`${endDate}T23:59:59Z`).toISOString(),
    timezone: 'UTC',
  };
}
