/**
 * Fail-closed prospective reporting policy.
 *
 * A valid forecast receipt and a later observed price do not prove that the
 * forecast was publicly anchored before the target close. Until a separately
 * verified publication/close-time attestation is implemented, no settled
 * outcome is eligible for headline prospective performance statistics.
 *
 * Keep the arithmetic for investigation, but label it provisional.
 */
const HORIZONS = Object.freeze([1, 7, 30]);
const VALID = new Set(['pending', 'matured', 'provisional', 'quarantined']);

export function gateSettlement(outcome) {
  if (!outcome || typeof outcome !== 'object' || Array.isArray(outcome) ||
      !VALID.has(outcome.status)) {
    throw new TypeError('Invalid settlement outcome status');
  }
  if (outcome.status !== 'matured') return {...outcome};
  return {
    ...outcome,
    status: 'provisional',
    timingEvidence: 'unverified_publication_before_target_close',
    timingCaveat: 'Settlement arithmetic is descriptive only. An independently verified '
      + 'server publication timestamp and target-close timestamp are required '
      + 'before including this forecast in prospective performance metrics.'
  };
}

export function summarizeSettlements(outcomes) {
  if (!Array.isArray(outcomes)) throw new TypeError('Settlement outcomes must be an array');
  // Reapply the gate here too: direct callers must not bypass CLI classification.
  const safe = outcomes.map(gateSettlement);
  for (const outcome of safe) {
    if (!outcome || !VALID.has(outcome.status) || !HORIZONS.includes(outcome.horizon)) {
      throw new TypeError('Invalid outcome status or horizon');
    }
  }
  return HORIZONS.map(horizon => {
    const group = safe.filter(row => row.horizon === horizon);
    return {
      horizon,
      matured: 0, // No authenticated publication-before-close verifier exists yet.
      provisional: group.filter(row => row.status === 'provisional').length,
      pending: group.filter(row => row.status === 'pending').length,
      quarantined: group.filter(row => row.status === 'quarantined').length,
      modelMae: null,
      baselineMae: null
    };
  });
}
