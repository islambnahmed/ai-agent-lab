/** Worker A — causal availability audit for 5-minute OHLC candle-close forecasts.
 * Historical CSV timestamps may denote bar OPEN or bar CLOSE; neither may be
 * silently assumed. This checks timing only, not quote provenance or skill.
 */
const STEP_MS = 5 * 60_000;
const HORIZON_MS = 75 * 60_000;
const check = (ok, why) => { if (!ok) throw new Error(why); };
const validMs = (n) => Number.isSafeInteger(n) && n >= 0;

export function closeAvailableAt(stampMs, {stampConvention, publishDelayMs = 0} = {}) {
  check(validMs(stampMs), 'invalid candle timestamp');
  check(stampMs % STEP_MS === 0, 'timestamp is not on a 5-minute boundary');
  check(stampConvention === 'open' || stampConvention === 'close',
    'stampConvention must be explicitly open or close');
  check(validMs(publishDelayMs) && publishDelayMs <= STEP_MS,
    'publishDelayMs must be between 0 and 5 minutes');
  return stampMs + (stampConvention === 'open' ? STEP_MS : 0) + publishDelayMs;
}

/** Check a forecast issued against a candle close for a nominal 75m horizon.
 * issuedAtMs must be an externally witnessed issue time in any real study.
 * Outcome capture authenticity is NOT proven by this function.
 */
export function auditCandleForecast({originStampMs, targetStampMs, issuedAtMs,
  stampConvention, publishDelayMs = 0} = {}) {
  check(validMs(issuedAtMs), 'invalid issuance time');
  const originAvailableAtMs = closeAvailableAt(originStampMs, {stampConvention, publishDelayMs});
  const targetAvailableAtMs = closeAvailableAt(targetStampMs, {stampConvention, publishDelayMs});
  check(targetStampMs - originStampMs === HORIZON_MS,
    'target is not exactly 75 candle minutes after origin');
  const originKnown = issuedAtMs >= originAvailableAtMs;
  const targetUnknown = issuedAtMs < targetAvailableAtMs;
  const effectiveLeadMs = targetAvailableAtMs - issuedAtMs;
  const exactly75mLead = effectiveLeadMs === HORIZON_MS;
  return Object.freeze({stampConvention, publishDelayMs, originAvailableAtMs,
    targetAvailableAtMs, issuedAtMs, effectiveLeadMs,
    eligibleFor75mClaim:originKnown && targetUnknown && exactly75mLead,
    status:!originKnown ? 'lookahead_origin_not_yet_available' :
      !targetUnknown ? 'outcome_already_available' :
      !exactly75mLead ? 'effective_horizon_not_75m' : 'timing_eligible',
    caveat:'Timestamp convention, publishing delay, independent issuance evidence, and provider authenticity must be verified externally.'});
}
