/**
 * Fail-closed, local-only ESM issuance-code provenance check.
 * Usage: node --experimental-vm-modules code-provenance-audit.mjs /path/to/products/gold-forecast scripts/journal.mjs
 * Verifies the static local ESM import closure matches the Git HEAD tree byte-for-byte.
 * This does not authenticate remote commits, data vintages, or issuance time.
 */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const runGit = (cwd, ...args) => execFileSync('git', args, {cwd, encoding:'utf8', stdio:['ignore','pipe','pipe']}).trim();
const within = (root, filename) => {
  const rel = path.relative(root, filename);
  return rel && rel !== '..' && !rel.startsWith('..'+path.sep) && !path.isAbsolute(rel);
};
function validateRelative(root, name) {
  if (typeof name !== 'string' || !name || path.isAbsolute(name) || name.split(/[\\/]/).includes('..') || name.startsWith('-')) {
    throw Error('Unsafe local module path: '+name);
  }
  const abs=path.resolve(root,name);
  if (!within(root,abs)) throw Error('Path escapes product root: '+name);
  const segments=path.relative(root,abs).split(path.sep);
  let current=root;
  for (const part of segments) {
    current=path.join(current,part);
    if (fs.lstatSync(current).isSymbolicLink()) throw Error('Symlink dependency not supported: '+name);
  }
  if (!fs.statSync(abs).isFile()) throw Error('Not a regular file: '+name);
  return abs;
}
function dependencies(filename, source) {
  // A conservative guard for constructs that cannot be resolved statically.
  // False positives in comments/strings cause rejection, never acceptance.
  if (/\bimport\s*\(/.test(source) || /\brequire\s*\(/.test(source)) {
    throw Error('Dynamic import/require requires manual review: '+filename);
  }
  const mod=new vm.SourceTextModule(source,{identifier:filename});
  return mod.dependencySpecifiers;
}
export function auditStaticClosure(productRoot, entry='scripts/journal.mjs', extra=['package.json']) {
  if (typeof vm.SourceTextModule !== 'function') throw Error('Run with --experimental-vm-modules');
  const root=fs.realpathSync(productRoot);
  const repo=fs.realpathSync(runGit(root,'rev-parse','--show-toplevel'));
  if (!within(repo,root)) throw Error('Product root must be inside a Git checkout');
  const seen=new Set(), queue=[entry];
  const repoPaths=[];
  while (queue.length) {
    const relative=queue.pop();
    const full=validateRelative(root,relative);
    if (seen.has(full)) continue;
    seen.add(full);
    if (!/\.(mjs|js|cjs)$/.test(full)) throw Error('Unsupported module type: '+relative);
    const source=fs.readFileSync(full,'utf8');
    for (const spec of dependencies(full,source)) {
      if (spec.startsWith('node:')) continue;
      if (!spec.startsWith('./') && !spec.startsWith('../')) throw Error('Unpinned external dependency: '+spec);
      const target=path.resolve(path.dirname(full),spec);
      if (!within(root,target)) throw Error('Import outside product root: '+spec);
      queue.push(path.relative(root,target));
    }
  }
  for (const name of extra) seen.add(validateRelative(root,name));
  for (const full of [...seen].sort()) {
    const repoPath=path.relative(repo,full).split(path.sep).join('/');
    let head, index, working;
    try {
      head=runGit(repo,'rev-parse','HEAD:'+repoPath);
      index=runGit(repo,'rev-parse',':'+repoPath);
      working=runGit(repo,'hash-object','--no-filters','--',full);
    } catch { throw Error('Untracked or missing from HEAD/index: '+repoPath); }
    if (head!==index || head!==working) throw Error('Not identical to HEAD: '+repoPath);
    repoPaths.push(repoPath);
  }
  const commit=runGit(repo,'rev-parse','HEAD');
  if (!/^[0-9a-f]{40}$/.test(commit)) throw Error('Invalid Git HEAD SHA');
  return {commit,files:repoPaths};
}
if (process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  const root=process.argv[2];
  if (!root) {console.error('Usage: node --experimental-vm-modules code-provenance-audit.mjs PRODUCT_ROOT [ENTRY]');process.exitCode=2;}
  else {
    try {console.log(JSON.stringify(auditStaticClosure(root,process.argv[3]??'scripts/journal.mjs'),null,2));}
    catch(e) {console.error('REJECTED: '+e.message);process.exitCode=1;}
  }
}
