#!/usr/bin/env node
/**
 * Audit GitHub-published gold forecast receipts against an independently
 * server-timestamped push workflow run. Offline input is a snapshot of GitHub
 * API evidence; refresh it independently before making public claims.
 *
 * Input JSON: { receipts:[{path,receipt,raw}], commit:{sha,files:[{filename,status,sha}]},
 *               workflowRuns:[{head_sha,event,created_at,html_url}] }
 */
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {isDeepStrictEqual} from 'node:util';
export const hash=value=>createHash('sha256').update(JSON.stringify(value)).digest('hex');
export function gitBlobSha(raw){
  const bytes=Buffer.from(raw,'utf8');
  return createHash('sha1').update(`blob ${bytes.length}\0`).update(bytes).digest('hex');
}
function verifyReceipt(receipt){
  if(!receipt||typeof receipt!=='object')throw Error('Invalid receipt');
  const {id,...payload}=receipt;
  if(id!==hash(payload)||receipt.schemaVersion!==1)throw Error('Receipt integrity mismatch');
  if(![1,7,30].includes(receipt.horizon)||!Number.isInteger(receipt.historyLength)||receipt.historyLength<165)
    throw Error('Invalid receipt metadata');
  instant(receipt.issuedAt);
  return true;
}
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
const SHA = /^[0-9a-f]{40}$/;
const MS_DAY = 86400000;
function utcDay(date){
  if(typeof date!=='string'||!ISO_DATE.test(date))throw Error('Invalid UTC date');
  const ms=Date.parse(date+'T00:00:00Z');
  if(!Number.isFinite(ms)||new Date(ms).toISOString().slice(0,10)!==date)throw Error('Impossible UTC date');
  return ms;
}
function instant(s){
  if(typeof s!=='string'||!/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$/.test(s))throw Error('Expected UTC timestamp');
  const ms=Date.parse(s);
  if(!Number.isFinite(ms)||new Date(ms).toISOString().slice(0,10)!==s.slice(0,10))throw Error('Invalid timestamp');
  return ms;
}
function safePath(p){
  return typeof p==='string'&&/^products\/gold-forecast\/reports\/prospective\/\d{4}-\d\d-\d\d-h(?:1|7|30)\.json$/.test(p);
}
export function auditAnchors(input){
  const {receipts,commit,workflowRuns}=input||{};
  if(!Array.isArray(receipts)||!receipts.length||!commit||!SHA.test(commit.sha)||!Array.isArray(commit.files)||!Array.isArray(workflowRuns))
    throw Error('Receipts, commit SHA/files and workflow runs required');
  const added=new Map(commit.files.filter(f=>f.status==='added').map(f=>[f.filename,f.sha]));
  // Author/committer timestamps are NOT an independent anchor. Require a
  // server-generated Actions run created after the receipts were issued.
  const eligible=workflowRuns.filter(r=>r.event==='push'&&r.head_sha===commit.sha&&
    /^https:\/\/github\.com\/[^/]+\/[^/]+\/actions\/runs\/\d+$/.test(r.html_url||'')&&
    typeof r.created_at==='string');
  const anchors=eligible.flatMap(r=>{
    try{return [{at:instant(r.created_at),url:r.html_url}]}catch{return []}
  }).sort((a,b)=>a.at-b.at);
  const paths=new Set();
  const results=receipts.map(({path,receipt,raw})=>{
    const problems=[];
    if(!safePath(path))problems.push('unexpected_receipt_path');
    if(paths.has(path))problems.push('duplicate_receipt_path');
    paths.add(path);
    if(!added.has(path))problems.push('receipt_not_added_in_anchor_commit');
    // Bind the exact published UTF-8 file bytes to the anchored Git commit.
    try{
      if(typeof raw!=='string'||!SHA.test(added.get(path))||
         gitBlobSha(raw)!==added.get(path)||
         !isDeepStrictEqual(JSON.parse(raw),receipt))
        problems.push('receipt_not_bound_to_commit_blob');
    }catch{problems.push('receipt_not_bound_to_commit_blob')}
    try{verifyReceipt(receipt)}catch{problems.push('invalid_receipt_hash_or_metadata')}
    let issue,source,earliest;
    try{
      issue=instant(receipt.issuedAt);
      source=instant(receipt.sourceManifest?.receivedAt);
      if(source>issue||issue-source>MS_DAY/24)problems.push('stale_or_future_source');
      const origin=utcDay(receipt.originDate);
      if(origin>=Date.parse(receipt.issuedAt.slice(0,10)+'T00:00:00Z'))problems.push('origin_not_before_issue_day');
      earliest=origin+(receipt.horizon+1)*MS_DAY;
      if(receipt.targetDate!==null&&receipt.targetDate!==undefined){
        const target=utcDay(receipt.targetDate);
        if(target<origin+receipt.horizon*MS_DAY)problems.push('target_before_minimum_horizon');
        earliest=target+MS_DAY;
      }
    }catch{problems.push('invalid_receipt_time_or_origin')}
    const anchor=anchors.find(a=>issue!==undefined&&a.at>=issue);
    if(!anchor)problems.push('no_post_issue_server_timestamp');
    const preOutcome=anchor&&earliest!==undefined?anchor.at<earliest:null;
    return {path,id:receipt?.id||null,horizon:receipt?.horizon,
      anchorUrl:anchor?.url||null,anchorAt:anchor?new Date(anchor.at).toISOString():null,
      earliestPossibleMaturityAt:earliest===undefined?null:new Date(earliest).toISOString(),
      preOutcome:preOutcome===true?'confirmed_under_UTC_day_convention':preOutcome===false?'indeterminate':'unanchored',
      problems};
  });
  return {schemaVersion:1,commit:commit.sha,receipts:results,
    valid:results.every(r=>!r.problems.length&&r.preOutcome==='confirmed_under_UTC_day_convention'),
    limitations:['GitHub Actions created_at is a server timestamp; offline JSON must be re-fetched from GitHub before reliance.',
      'Commit author/committer dates are not trusted anchors.',
      'Git blob SHA-1 binds exact bytes to a Git commit file listing; re-fetch commit and blob from GitHub before independent reliance.',
      'Pre-outcome status relies on completed UTC-day observations, not a verified market close or independent source vintage.',
      'An anchor does not establish price accuracy, outcome maturity, or predictive skill.']};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  if(process.argv.length!==3){console.error('Usage: node anchor_audit.mjs github-evidence.json');process.exit(2)}
  try{
    const result=auditAnchors(JSON.parse(readFileSync(process.argv[2],'utf8')));
    console.log(JSON.stringify(result,null,2));process.exitCode=result.valid?0:1;
  }catch(e){console.error(e.message);process.exitCode=2}
}
