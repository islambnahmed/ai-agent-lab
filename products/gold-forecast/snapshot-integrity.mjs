// Detect divergence between the provider snapshot saved by fetch_data.py
// and the manifest used for issuing/settling prospective receipts.
// This is local file integrity, not upstream authenticity or timestamp proof.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';

const SHA256=/^[0-9a-f]{64}$/;
export function readVerifiedSnapshot(dataDir,name,manifest,{expectedUrl}={}){
  if(name!=='history')throw Error('Unsupported receipt snapshot');
  const meta=manifest?.[name];
  if(meta?.status!=='fetched'||!SHA256.test(meta.storedSha256??'')||!SHA256.test(meta.rawSha256??''))
    throw Error('Missing successful source manifest or snapshot hash: fetch fresh data');
  if(typeof expectedUrl==='string'&&meta.url!==expectedUrl)
    throw Error('Unexpected snapshot source URL');
  const bytes=fs.readFileSync(path.join(dataDir,name+'.json'));
  const digest=createHash('sha256').update(bytes).digest('hex');
  if(digest!==meta.storedSha256)throw Error('Saved source snapshot differs from fetch manifest');
  return JSON.parse(bytes.toString('utf8'));
}
