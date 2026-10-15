/**
 * Verify the pinned Git revision describes the entire Gold Lab source tree.
 * Keep peer changes elsewhere in the repository out of this check.
 */
import {execFileSync} from 'node:child_process';
import path from 'node:path';

export function assertGoldTreeClean(goldRoot) {
  if (typeof goldRoot !== 'string' || !goldRoot.trim()) throw Error('Gold root required');
  const cwd = path.resolve(goldRoot);
  const changes = execFileSync('git', ['status', '--porcelain=v1', '--untracked-files=all', '--', '.'], {
    cwd, encoding: 'utf8', maxBuffer: 2 * 1024 * 1024,
  });
  if (changes.trim()) throw Error('Commit non-ignored Gold Lab changes before issuing forecasts: ' +
    changes.trim().split('\n').slice(0, 5).join(' | '));
  const codeCommit = execFileSync('git', ['rev-parse', 'HEAD'], {cwd, encoding: 'utf8'}).trim();
  if (!/^[a-f0-9]{40}$/.test(codeCommit)) throw Error('Invalid pinned code commit');
  return codeCommit;
}
