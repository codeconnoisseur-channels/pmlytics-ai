import { describe, expect, it } from 'vitest';
import { SAMPLE_SCENARIOS } from '@/lib/sample-scenarios';

describe('completed scenario previews', () => {
  it('keeps every brief decision-led, attributable, and free of implementation leakage', () => {
    const forbidden = /localhost|api\s*v\d|http\s*502|hogql|jql|research_agent|upstream error/i;

    for (const scenario of Object.values(SAMPLE_SCENARIOS)) {
      expect(scenario.status).toBe('completed');
      expect(scenario.recommendation.recommendation.length).toBeGreaterThan(40);
      expect(scenario.recommendation.success_metrics.length).toBeGreaterThan(0);
      expect(Object.keys(scenario.evidence_ledger)).toHaveLength(3);
      expect(JSON.stringify(scenario)).not.toMatch(forbidden);

      const records = Object.values(scenario.evidence_ledger).flatMap(
        (item) => item.supporting_records ?? []
      );
      expect(records.length).toBeGreaterThan(0);
      expect(JSON.stringify(records)).not.toMatch(
        /requester_id|distinct_id|transaction_id|failure_code|system prompt|prompt injection/i
      );

      for (const finding of scenario.recommendation.factual_observations) {
        const evidenceIds = finding.evidence_ids ?? [];
        expect(evidenceIds.length).toBeGreaterThan(0);
        for (const evidenceId of evidenceIds) {
          expect(scenario.evidence_ledger[evidenceId]).toBeDefined();
        }
      }
    }
  });

  it('rejects the false wallet outage premise', () => {
    const wallet = SAMPLE_SCENARIOS.inv_p12a_scenario_3;
    expect(wallet.recommendation.problem_statement).toMatch(/does not show elevated transaction failures/i);
    expect(wallet.recommendation.recommendation).toMatch(/Do not open an incident/i);
    expect(JSON.stringify(wallet)).toMatch(/No wallet-funding failure events/i);
  });

  it('isolates the bill-payment incident to electricity', () => {
    const bills = SAMPLE_SCENARIOS.inv_p12a_scenario_4;
    expect(bills.recommendation.problem_statement).toMatch(/electricity-provider incident/i);
    expect(bills.recommendation.affected_users).toMatch(/cable, airtime, and internet/i);
    expect(bills.recommendation.confidence).toBe('high');
  });
});
