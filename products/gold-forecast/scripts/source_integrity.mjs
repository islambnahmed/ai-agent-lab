/** Bind a saved provider payload to its fetch manifest before it can be used. */
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';

const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');
const NAMES=new Set(['history','spot','crosscheck']);

export function readVerifiedSnapshot(dataDir,name,manifest){
  if(!NAMES.has(name))throw Error('Unexpected provider snapshot');
  const meta=manifest?.[name];
  if(meta?.status!=='fetched'||meta.httpStatus!==200||
     typeof meta.savedSha256!=='string'||!/^[a-f0-9]{64}$/.test(meta.savedSha256))
    throw Error('Missing verified provider snapshot metadata: '+name);
  const bytes=fs.readFileSync(path.join(dataDir,name+'.json'));
  if(sha256(bytes)!==meta.savedSha256)throw Error('Saved provider snapshot hash mismatch: '+name);
  return JSON.parse(bytes.toString('utf8'));
}
