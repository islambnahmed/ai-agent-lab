// Bind local parsed provider snapshots to the fetch manifest that describes them.
// rawSha256 fingerprints the HTTP body; storedSha256 fingerprints the exact
// JSON bytes written to data/*.json after parsing and serialization.
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';

const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const sha256 = value => typeof value === 'string' && /^[0-9a-f]{64}$/.test(value);

export function parseVerifiedSnapshot(bytes, meta, name='snapshot') {
  if (!meta || meta.status !== 'fetched' || meta.httpStatus !== 200 ||
      !sha256(meta.rawSha256) || !sha256(meta.storedSha256)) {
    throw Error(name + ': missing successful, integrity-tagged fetch; run npm run data');
  }
  if (digest(bytes) !== meta.storedSha256) {
    throw Error(name + ': local snapshot differs from fetch manifest; re-fetch data');
  }
  return JSON.parse(bytes.toString('utf8'));
}

export function readVerifiedSnapshot(root, manifest, name) {
  if (!['history', 'spot', 'crosscheck'].includes(name)) throw Error('Unknown snapshot name');
  // Read the exact bytes before JSON.parse so a reserialized/old file cannot
  // masquerade as the provider response described by this manifest.
  return parseVerifiedSnapshot(readFileSync(join(root, 'data', name + '.json')),
                               manifest?.[name], name);
}
