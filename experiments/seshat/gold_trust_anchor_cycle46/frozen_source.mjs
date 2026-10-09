/** Independent trust anchors for Seshat's frozen October 2026 nowcast.
 * Import this module from the dashboard BEFORE trusting downloaded manifest JSON.
 * This does not prove publication time or prediction skill.
 */
export const FROZEN = Object.freeze({
  repository:'islambnahmed/ai-agent-lab',
  source_path:'experiments/seshat/gold_asof_cycle28/nowcast_2026_10.json',
  source_commit:'ebedcce9a4250b37106a4eb8c54ce962656cb35e',
  source_record_sha256:'430d07aab434ae3ec45aa920b6fce6cf6cd1e8794461613d5e19b8e2c66f28be',
  source_git_blob_sha1:'c9def1f51c1890e7e60e09c173aeb397b94a77bf',
  source_commit_committer_date:'2026-10-09T02:17:06Z',
  data_sha256:'393793d66847bc4ccbee832424bbda8b9ececb010ca4d2da0c7e090a8b4a04d7'
});
const fields=['repository','source_path','source_commit','source_record_sha256',
  'source_git_blob_sha1','source_commit_committer_date'];
export function assertFrozenManifest(manifest) {
  if (!manifest || typeof manifest !== 'object' || Array.isArray(manifest))
    throw Error('Missing manifest');
  for (const key of fields)
    if (manifest[key] !== FROZEN[key]) throw Error('Untrusted manifest anchor: '+key);
  if (manifest.schema_version !== 1 || manifest.settlement_status !== 'PENDING')
    throw Error('Unrecognized manifest schema or settlement state');
  return manifest;
}
const toHex = a => Array.from(a, b=>b.toString(16).padStart(2,'0')).join('');
async function digest(algorithm, bytes) {
  if (!globalThis.crypto?.subtle) throw Error('Web Crypto secure context required');
  return toHex(new Uint8Array(await crypto.subtle.digest(algorithm,bytes)));
}
export async function verifyFrozenBytes(bytes,manifest) {
  assertFrozenManifest(manifest);
  if (!(bytes instanceof Uint8Array)) throw Error('Raw Uint8Array required');
  const header=new TextEncoder().encode('blob '+bytes.length+'\0');
  const blob=new Uint8Array(header.length+bytes.length);
  blob.set(header);blob.set(bytes,header.length);
  const [sha256,sha1]=await Promise.all([digest('SHA-256',bytes),digest('SHA-1',blob)]);
  if (sha256!==FROZEN.source_record_sha256 || sha1!==FROZEN.source_git_blob_sha1)
    throw Error('Forecast bytes do not match frozen GitHub object');
  const record=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
  if (record.data_sha256!==FROZEN.data_sha256 || record.target_month!=='2026-10' ||
      record.as_of_month!=='2026-09' || record.no_change!==4319 ||
      Math.abs(record.endpoint_drift-4416.626)>1e-9)
    throw Error('Frozen record has unexpected inputs or target');
  return record;
}
