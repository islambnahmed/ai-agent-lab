/** Verify exact raw response and normalized history before consuming provider data.
 * Local consistency only: does not authenticate upstream or release-time availability.
 */
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';

const SHA256 = /^[a-f0-9]{64}$/;
const digest = bytes => createHash('sha256').update(bytes).digest('hex');

function requirePhysicalDirectory(filename) {
  const stat = fs.lstatSync(filename);
  if (stat.isSymbolicLink() || !stat.isDirectory())
    throw Error('Custody directory must be a physical directory');
  if (fs.realpathSync(filename) !== path.resolve(filename))
    throw Error('Custody directory escapes expected location');
}

function regularFileBytes(filename) {
  const fd = fs.openSync(filename, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW);
  try {
    const stat = fs.fstatSync(fd);
    if (!stat.isFile() || stat.size > 20_000_000)
      throw Error('Custody path is not a bounded regular file');
    return fs.readFileSync(fd);
  } finally {
    fs.closeSync(fd);
  }
}

export function verifyHistoryCustody(root, manifest) {
  const m = manifest?.history;
  if (!m || m.status !== 'fetched') throw Error('History fetch is not verified successful');
  if (!SHA256.test(m.rawSha256 ?? '') || !SHA256.test(m.snapshotSha256 ?? ''))
    throw Error('Missing or malformed custody digests');
  if (m.rawArchivePath !== `raw-vintages/${m.rawSha256}.json`)
    throw Error('Raw archive path is not content-addressed');
  if (!Number.isSafeInteger(m.rawByteLength) || m.rawByteLength < 1 || m.rawByteLength > 5_000_000)
    throw Error('Invalid raw response byte length');
  const dataDir = path.join(root, 'data');
  requirePhysicalDirectory(path.resolve(root));
  requirePhysicalDirectory(dataDir);
  requirePhysicalDirectory(path.join(dataDir, 'raw-vintages'));
  const raw = regularFileBytes(path.join(dataDir, 'raw-vintages', `${m.rawSha256}.json`));
  const snapshot = regularFileBytes(path.join(dataDir, 'history.json'));
  if (raw.length !== m.rawByteLength || digest(raw) !== m.rawSha256)
    throw Error('Raw archive content mismatch');
  if (digest(snapshot) !== m.snapshotSha256)
    throw Error('Normalized snapshot content mismatch');
  let original, normalized;
  try {
    original = JSON.parse(raw.toString('utf8'));
    normalized = JSON.parse(snapshot.toString('utf8'));
  } catch {
    throw Error('Invalid JSON in raw or normalized snapshot');
  }
  if (JSON.stringify(original) !== JSON.stringify(normalized))
    throw Error('Raw archive and normalized snapshot have different JSON values');
  return normalized;
}
