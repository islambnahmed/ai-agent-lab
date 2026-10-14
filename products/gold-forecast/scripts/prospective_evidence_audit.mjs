// Worker A: conservative evidence triage for already-issued gold forecast receipts.
// Does not fetch market data, assert a target close, or claim predictive skill.
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';

const instant = (s, name) => {
  if (typeof s !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$/.test(s)) throw Error(`${name}: UTC ISO timestamp required`);
  const ms = Date.parse(s);
  if (!Number.isFinite(ms) || new Date(ms).toISOString().slice(0, 10) !== s.slice(0, 10)) throw Error(`${name}: invalid timestamp`);
  return ms;
};
const digest = x => createHash('sha256').update(JSON.stringify(x)).digest('hex');
const finitePositive = x => typeof x === 'number' && Number.isFinite(x) && x > 0;

export function auditReceipt(receipt, {githubAnchorAt, verifiedTargetFirstAvailableAt = null} = {}) {
  if (!receipt || typeof receipt !== 'object' || Array.isArray(receipt)) throw Error('Receipt object required');
  const {id, ...payload} = receipt;
  if (typeof id !== 'string' || digest(payload) !== id) throw Error('Receipt hash mismatch');
  if (receipt.schemaVersion !== 1 || ![1,7,30].includes(receipt.horizon)) throw Error('Unexpected receipt schema or horizon');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(receipt.originDate)) throw Error('Origin date required');
  if (!/^[0-9a-f]{40}$/.test(receipt.codeCommit)) throw Error('Pinned code commit required');
  if (!/^[0-9a-f]{64}$/.test(receipt.historyHash) || !Number.isInteger(receipt.historyLength) || receipt.historyLength < 165) throw Error('Historical source fingerprint missing');
  for (const k of ['point','lower','upper','baseline','originClose']) if (!finitePositive(receipt[k])) throw Error(`Invalid ${k}`);
  if (!(receipt.lower <= receipt.point && receipt.point <= receipt.upper)) throw Error('Invalid forecast interval');
  const issue = instant(receipt.issuedAt, 'issuedAt');
  const fetched = instant(receipt.sourceManifest?.receivedAt, 'sourceManifest.receivedAt');
  if (fetched > issue || issue-fetched > 3600000) throw Error('Source snapshot not within 1h before issue');
  if (receipt.originDate > receipt.issuedAt.slice(0,10)) throw Error('Origin after issue');
  if (!githubAnchorAt) throw Error('Independent GitHub publication anchor required');
  const anchor = instant(githubAnchorAt,'githubAnchorAt');
  if (anchor < issue) throw Error('Anchor predates claimed issue');
  const noIncrementalSkillPossible = receipt.point === receipt.baseline;
  let prospectiveEligibility = 'unverified_target_availability';
  if (verifiedTargetFirstAvailableAt != null) {
    const available = instant(verifiedTargetFirstAvailableAt,'verifiedTargetFirstAvailableAt');
    prospectiveEligibility = available > anchor ? 'time_eligible_conditional_on_verified_source' : 'not_prospective_target_already_available';
  }
  return {
    receiptId: id, horizon: receipt.horizon, model: receipt.model,
    issueAt: receipt.issuedAt, githubAnchorAt, originDate: receipt.originDate,
    targetDate: receipt.targetDate,
    prospectiveEligibility, outcomeStatus: 'unverified_no_target_close_supplied',
    noIncrementalSkillPossible, point: receipt.point, baseline: receipt.baseline,
    absolutePointBaselineDifference: Math.abs(receipt.point - receipt.baseline),
    cannotIndependentlyReconstructInputFromHashAlone: true,
    requiredEvidence: [
      'Authentic source-specific target close and observation order after frozen origin',
      'Verifiable first-publication time of target close strictly after GitHub anchor',
      'Original source vintage or independently checked unchanged historical prefix',
      'Model and baseline absolute errors on the same source/target without reselection'
    ],
    caution: 'A GitHub timestamp proves receipt publication, not that the target close was unknown; this audit does not settle forecasts.'
  };
}

if (process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href) {
  try {
    const [, , anchor, ...files] = process.argv;
    if (!anchor || !files.length) throw Error('Usage: node prospective_evidence_audit.mjs <github-run-created-at> <receipt.json> [...]');
    const results = files.map(f => auditReceipt(JSON.parse(readFileSync(f,'utf8')), {githubAnchorAt: anchor}));
    console.log(JSON.stringify({auditVersion:1, results},null,2));
  } catch (e) { console.error(e.message); process.exitCode=1; }
}