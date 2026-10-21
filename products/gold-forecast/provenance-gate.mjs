/** Fail closed if code capable of issuing prospective receipts is not committed.
 * Intentionally excludes generated data/, reports/ and runs/.
 * This does not prove the commit preceded target close; the external Git
 * timestamp of the issued receipt must still be checked separately.
 */
import {execFileSync} from 'node:child_process';
export const ISSUER_PATHS=[
  'forecast.mjs','models.mjs','data.mjs','historical-integrity.mjs',
  'calendar_contract.mjs','journal.mjs','provenance-gate.mjs','scripts'
];
export function assertCommittedIssuer(root){
  const dirty=execFileSync('git',['status','--porcelain','--',...ISSUER_PATHS],{cwd:root,encoding:'utf8'});
  if(dirty.trim())throw Error('Commit implementation before issuing forecasts');
  return execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim();
}
