import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';

// An algebraic certificate of *conditions* for lower absolute error.
// Does not authenticate outcomes or establish prospective skill.
const sha256 = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');
export function verifyAndCertify(receipt) {
  if (!receipt || typeof receipt !== 'object' || Array.isArray(receipt)) throw Error('invalid receipt');
  const {id, ...body} = receipt;
  if (id !== sha256(body)) throw Error('receipt hash mismatch');
  const {horizon,point,baseline,lower,upper,originClose,issuedAt} = receipt;
  if (![1,7,30].includes(horizon) || ![point,baseline,lower,upper,originClose].every(Number.isFinite)) throw Error('invalid receipt numbers');
  if (!(lower <= point && point <= upper) || !(baseline > 0 && point > 0)) throw Error('invalid receipt range');
  const difference = point - baseline;
  const threshold = (point + baseline) / 2;
  return {
    receiptId:id, horizon, issuedAt, model:receipt.model,
    point, baseline, deltaVsBaseline:difference,
    outcomeStatus:'not_verified',
    winCondition:difference === 0 ? 'never_strictly_better' : difference > 0 ? 'actual_above_threshold' : 'actual_below_threshold',
    threshold: difference === 0 ? null : threshold,
    maximumAbsoluteErrorAdvantage:Math.abs(difference),
    caveat:'Purely algebraic win condition for absolute error; no target prices, timestamps or realized skill verified.'
  };
}
export function compareAbsErrors(cert, actual) {
  if (!Number.isFinite(actual) || actual <= 0) throw Error('invalid actual');
  return {
    model:Math.abs(cert.point - actual),
    baseline:Math.abs(cert.baseline - actual),
    wins:Math.abs(cert.point - actual) < Math.abs(cert.baseline - actual)
  };
}
if (process.argv[1] && import.meta.url === new URL('file://' + process.argv[1]).href) {
  const results = process.argv.slice(2).map(path => verifyAndCertify(JSON.parse(readFileSync(path, 'utf8'))));
  console.log(JSON.stringify({schemaVersion:1,certificates:results},null,2));
}
