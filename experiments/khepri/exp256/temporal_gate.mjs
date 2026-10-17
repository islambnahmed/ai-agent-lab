/** Khepri experiment 256: UTC date normalization for prospective receipts.
 * Day-only target observations do not authenticate their intraday close times.
 * No source authenticity, independent timestamp, or predictive-skill claim.
 */
import {parseInstant} from '../../../products/gold-forecast/historical-integrity.mjs';
export const utcDay=instant=>new Date(parseInstant(instant)).toISOString().slice(0,10);
export function assertFutureTarget(targetDate,issuedAt){
  if(targetDate!==null&&targetDate<=utcDay(issuedAt))
    throw Error('Target UTC day is not strictly after issue UTC day');
}
export function assertOutcomeNotBeforeIssue(targetDate,issuedAt){
  if(targetDate<utcDay(issuedAt))throw Error('Outcome predates issue in UTC');
}
export function targetDayCompleted(targetDate,asOf){return targetDate<utcDay(asOf);}
