import {summarizeSettlements} from './settlement-accounting.mjs';

/**
 * Pure reporting adapter for the existing journal CLI.
 * The adapter NEVER promotes an algorithmic settlement to a verified forecast.
 * It accepts only receipt and outcome objects; provenance must be audited separately.
 */
export function buildSettlementReport(receipts, outcomes, asOf) {
  if(typeof asOf !== 'string' || !Number.isFinite(Date.parse(asOf)) ||
     !/(Z|[+-]\d\d:\d\d)$/.test(asOf)) throw Error('Offset-aware asOf required');
  const accounting = summarizeSettlements(receipts, outcomes);
  // Legacy shape remains available for existing consumers of settlements.json.
  const summaries = accounting.map(({horizon,matured,modelMae,baselineMae})=>({
    horizon,matured,modelMae,baselineMae
  }));
  return {
    asOf, outcomes, summaries, accounting,
    caveat: 'Algorithmically settled outcomes are not independently verified; Git receipt publication, target-close time, and price availability require external evidence.'
  };
}
