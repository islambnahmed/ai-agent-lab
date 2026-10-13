import test from 'node:test';
import assert from 'node:assert/strict';
import {auditAnchors,hash,gitBlobSha} from '../anchor_audit.mjs';
const SHA='a'.repeat(40), CODE='b'.repeat(40), path='products/gold-forecast/reports/prospective/2026-10-11-h1.json';
function receipt(override={}){
  const r={schemaVersion:1,issuedAt:'2026-10-12T17:12:52.272Z',source:'test',codeCommit:CODE,
    sourceManifest:{receivedAt:'2026-10-12T17:10:55.750Z'},horizon:1,
    originDate:'2026-10-11',historyLength:324,targetDate:null,point:4207.98,baseline:4207.98,...override};
  return {...r,id:hash(r)};
}
function input(r=receipt(),at='2026-10-12T17:13:55Z'){
  const raw=JSON.stringify(r,null,2)+'\n';
  return {receipts:[{path,receipt:r,raw}],commit:{sha:SHA,files:[{filename:path,status:'added',sha:gitBlobSha(raw)}]},
    workflowRuns:[{event:'push',head_sha:SHA,created_at:at,html_url:'https://github.com/islambnahmed/ai-agent-lab/actions/runs/123'}]};
}
test('accepts GitHub server push anchor before earliest UTC-day outcome',()=>{
  const r=auditAnchors(input());assert.equal(r.valid,true);
  assert.equal(r.receipts[0].earliestPossibleMaturityAt,'2026-10-13T00:00:00.000Z');
});
test('rejects forged receipt hash',()=>{
  const x=input();x.receipts[0].receipt.point=1;
  assert.equal(auditAnchors(x).receipts[0].problems.includes('invalid_receipt_hash_or_metadata'),true);
});
test('rejects run before issuance and mismatched commit SHA',()=>{
  const x=input(receipt(),'2026-10-12T17:11:00Z');assert.equal(auditAnchors(x).valid,false);
  const y=input();y.workflowRuns[0].head_sha='c'.repeat(40);assert.equal(auditAnchors(y).valid,false);
});
test('never trusts Git commit timestamps alone',()=>{
  const x=input();x.workflowRuns=[];x.commit.committerDate='2026-10-12T17:13:52Z';
  assert.equal(auditAnchors(x).receipts[0].preOutcome,'unanchored');
});
test('later anchor is indeterminate rather than falsely labeled post-outcome',()=>{
  const r=auditAnchors(input(receipt(),'2026-10-13T01:00:00Z'));
  assert.equal(r.receipts[0].preOutcome,'indeterminate');assert.equal(r.valid,false);
});
test('requires commit to add receipt file',()=>{
  const x=input();x.commit.files[0].status='modified';
  assert.ok(auditAnchors(x).receipts[0].problems.includes('receipt_not_added_in_anchor_commit'));
});
test('rejects origin from issuance day and impossible dates',()=>{
  const r=auditAnchors(input(receipt({originDate:'2026-10-12'})));
  assert.ok(r.receipts[0].problems.includes('origin_not_before_issue_day'));
  const x=auditAnchors(input(receipt({originDate:'2026-02-30'})));
  assert.ok(x.receipts[0].problems.includes('invalid_receipt_time_or_origin'));
});
test('horizon 7 earliest possible maturity is 8 days after origin midnight',()=>{
  const p='products/gold-forecast/reports/prospective/2026-10-11-h7.json';
  const x=input(receipt({horizon:7}));x.receipts[0].path=p;x.commit.files[0].filename=p;
  assert.equal(auditAnchors(x).receipts[0].earliestPossibleMaturityAt,'2026-10-19T00:00:00.000Z');
});
test('rejects source timestamp after issue',()=>{
  const x=input(receipt({sourceManifest:{receivedAt:'2026-10-12T17:15:00Z'}}));
  assert.ok(auditAnchors(x).receipts[0].problems.includes('stale_or_future_source'));
});
test('self-consistent forged receipt cannot borrow genuine commit and server timestamp',()=>{
  const x=input();
  const r=x.receipts[0].receipt;
  r.point=999999;
  const {id,...payload}=r;r.id=hash(payload);
  x.receipts[0].raw=JSON.stringify(r,null,2)+'\n';
  assert.equal(auditAnchors(x).valid,false);
  assert.ok(auditAnchors(x).receipts[0].problems.includes('receipt_not_bound_to_commit_blob'));
});
test('rejects missing raw published bytes and missing Git blob SHA',()=>{
  const x=input();delete x.receipts[0].raw;
  assert.ok(auditAnchors(x).receipts[0].problems.includes('receipt_not_bound_to_commit_blob'));
  const y=input();delete y.commit.files[0].sha;
  assert.ok(auditAnchors(y).receipts[0].problems.includes('receipt_not_bound_to_commit_blob'));
});
test('rejects changed raw formatting, raw mismatch, and forged Git blob SHA',()=>{
  const x=input();x.receipts[0].raw=x.receipts[0].raw.trim();
  assert.ok(auditAnchors(x).receipts[0].problems.includes('receipt_not_bound_to_commit_blob'));
  const y=input();y.receipts[0].raw='{}';
  assert.ok(auditAnchors(y).receipts[0].problems.includes('receipt_not_bound_to_commit_blob'));
  const z=input();z.commit.files[0].sha='f'.repeat(40);
  assert.ok(auditAnchors(z).receipts[0].problems.includes('receipt_not_bound_to_commit_blob'));
});
