// Verify the local history snapshot against the exact bytes recorded at fetch time.
// A manifest hash is an integrity check, not proof of provider identity or publication time.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';

export function loadVerifiedHistory(root){
  const dir=path.join(root,'data');
  const manifest=JSON.parse(fs.readFileSync(path.join(dir,'fetch-manifest.json'),'utf8'));
  const entry=manifest?.history;
  if(entry?.status!=='fetched'||typeof entry.rawSha256!=='string'||
      !/^[0-9a-f]{64}$/.test(entry.rawSha256)||typeof entry.receivedAt!=='string')
    throw Error('Historical snapshot lacks a valid fetched manifest');
  const raw=fs.readFileSync(path.join(dir,'history.json'));
  const digest=createHash('sha256').update(raw).digest('hex');
  if(digest!==entry.rawSha256)throw Error('Historical source bytes differ from fetch manifest: quarantine snapshot');
  return {manifest,history:JSON.parse(raw.toString('utf8'))};
}
