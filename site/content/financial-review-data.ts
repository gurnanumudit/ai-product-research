// Published exploratory results. Capacities are tested observations, not a continuous model.
export const followupRows = [
  { capacity: 5, slots: 56, confidence: 31, verification: 35, random: 17 },
  { capacity: 10, slots: 112, confidence: 59, verification: 88, random: 35 },
  { capacity: 20, slots: 225, confidence: 103, verification: 143, random: 67 },
  { capacity: 50, slots: 563, confidence: 204, verification: 211, random: 185 },
];
export const totalAnswers = 1127;
export const totalMismatches = 347;
export type ReviewPolicy = 'confidence' | 'verification' | 'random';
export function reviewMetrics(row: typeof followupRows[number], policy: ReviewPolicy) {
  const selected = row[policy];
  const missed = totalMismatches - selected;
  const unreviewed = totalAnswers - row.slots;
  // Mandatory review includes all 15 abstentions, so none remain outside review.
  return { selected, missed, unreviewed, accuracy: 100 * (unreviewed - missed) / unreviewed, precision: 100 * selected / row.slots };
}
