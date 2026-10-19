// Offline audit of the integrity and evidentiary limits of published forecast receipts.
// Git commit author/committer dates are NOT trusted server timestamps.
import {createHash} from 'node:crypto';
import fs from 'node:fs';

const sha256 = value => createHash('sha256').update(value).digest('hex');
const gitBlobSha = raw => {
  const bytes = Buffer.from(raw, 'utf8');
  return createHash('sha1').update(`blob ${bytes.length}\0`).update(bytes).digest('hex');
};
const requireTrue = (ok, why) => { if (!ok) throw Error(why); };
function instant(value, label) {
  requireTrue(typeof value === 'string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$/.test(value), `${label}: UTC timestamp required`);
  const t = Date.parse(value);
  requireTrue(Number.isFinite(t), `${label}: invalid timestamp`);
  return t;
}

export function auditReceipt({path, raw}, anchor, asOf) {
  requireTrue(typeof path === 'string' && path.startsWith('products/gold-forecast/reports/prospective/') && path.endsWith('.json'), 'Unexpected receipt path');
  requireTrue(typeof raw === 'string', 'Receipt raw text required');
  const receipt = JSON.parse(raw);
  const {id, ...payload} = receipt;
  requireTrue(/^[a-f0-9]{64}$/.test(id || '') && id === sha256(JSON.stringify(payload)), 'Receipt payload hash mismatch');
  requireTrue(receipt.schemaVersion === 1 && [1, 7, 30].includes(receipt.horizon), 'Invalid receipt version or horizon');
  requireTrue(/^[a-f0-9]{40}$/.test(receipt.codeCommit || ''), 'Invalid code commit');
  requireTrue(Number.isInteger(receipt.historyLength) && receipt.historyLength >= 165, 'Invalid history length');
  requireTrue(/^\d{4}-\d\d-\d\d$/.test(receipt.originDate || ''), 'Invalid origin date');
  requireTrue(Number.isFinite(receipt.point) && Number.isFinite(receipt.lower) && Number.isFinite(receipt.upper) && receipt.lower <= receipt.point && receipt.point <= receipt.upper, 'Invalid forecast interval');
  const issued = instant(receipt.issuedAt, 'issuedAt');
  const received = instant(receipt.sourceManifest?.receivedAt, 'source receivedAt');
  requireTrue(issued >= received && issued - received <= 3600000, 'Source snapshot not within one hour before issue');
  const now = instant(asOf, 'asOf');
  requireTrue(now >= issued, 'Audit predates receipt');
  requireTrue(/^[a-f0-9]{40}$/.test(anchor?.sha || ''), 'Invalid anchor commit SHA');
  const entry = anchor.files?.find(f => f.filename === path);
  requireTrue(entry && entry.status === 'added', 'Receipt not added in stated commit');
  requireTrue(entry.sha === gitBlobSha(raw), 'Receipt bytes do not match Git blob in anchor commit');
  const claimedCommitTime = instant(anchor.committerDate, 'committerDate');
  const issueToClaimedCommitSeconds = (claimedCommitTime - issued) / 1000;
  const originMidnight = Date.parse(receipt.originDate + 'T00:00:00Z');
  requireTrue(Number.isFinite(originMidnight) && originMidnight < issued, 'Origin must predate issuance');
  const originAgeHoursRange = [Math.max(0, (issued - originMidnight - 86400000) / 3600000), (issued - originMidnight) / 3600000];
  return {
    path, id, horizon: receipt.horizon, model: receipt.model, originDate: receipt.originDate,
    issuedAt: receipt.issuedAt, targetDate: receipt.targetDate,
    anchorCommit: anchor.sha, claimedCommitterDate: anchor.committerDate,
    issueToClaimedCommitSeconds,
    payloadHashVerified: true, gitBlobMatched: true,
    gitTimeEvidence: 'unverified_client_controlled_timestamp',
    sourceTimeEvidence: 'self_attested_in_receipt',
    originAgeHoursRange,
    settlementStatus: 'not_evaluated_no_outcome_or_original_vintage',
    warnings: [
      'Git commit author/committer dates do not independently prove when GitHub first received the commit.',
      ...(issueToClaimedCommitSeconds < 0 ? ['Claimed Git commit date precedes receipt issuance.'] : []),
      ...(receipt.targetDate === null ? ['Target is defined by future observed closes; exact target date cannot be inferred from receipt.'] : []),
      'Do not score a receipt until an authenticated outcome and original historical vintage are available.'
    ]
  };
}

export function auditSet(receipts, anchor, asOf) {
  requireTrue(Array.isArray(receipts) && receipts.length > 0, 'Receipts required');
  const rows = receipts.map(r => auditReceipt(r, anchor, asOf));
  requireTrue(new Set(rows.map(r => r.id)).size === rows.length, 'Duplicate receipt ID');
  requireTrue(new Set(rows.map(r => r.horizon)).size === rows.length, 'Duplicate forecast horizon in batch');
  return {
    schemaVersion: 1, asOf, receiptCount: rows.length,
    verifiedGitContentBindings: rows.length,
    independentlyVerifiedIssueTimes: 0,
    maturedOutcomesEvaluated: 0,
    evidenceLevel: 'content_integrity_only_not_predictive_skill',
    caveat: 'Git API blob SHAs can verify bytes in a commit. Client-set Git commit dates do not prove server receipt time. No outcome data was supplied.',
    receipts: rows
  };
}

if (process.argv[1] && import.meta.url === new URL('file://' + process.argv[1]).href) {
  const [anchorPath, asOf, ...receiptPaths] = process.argv.slice(2);
  requireTrue(anchorPath && asOf && receiptPaths.length > 0, 'Usage: node audit_prospective_receipts.mjs anchor.json AS_OF_UTC receipt1.json ...');
  const anchor = JSON.parse(fs.readFileSync(anchorPath, 'utf8'));
  const receipts = receiptPaths.map(path => ({path: path.replaceAll('\\', '/').replace(/^.*?(products\/gold-forecast\/reports\/prospective\/)/, '$1'), raw: fs.readFileSync(path, 'utf8')}));
  process.stdout.write(JSON.stringify(auditSet(receipts, anchor, asOf), null, 2) + '\n');
}
