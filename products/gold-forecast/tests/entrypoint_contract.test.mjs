import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const root=new URL('../',import.meta.url);
const read=name=>readFileSync(new URL(name,root),'utf8');
test('site runs verified app, not legacy app',()=>{
  const html=read('index.html');
  assert.match(html,/src="\.\/app_verified\.mjs"/);
  assert.doesNotMatch(html,/src="\.\/app\.mjs"/);
});
test('verified app calls strict CSV session guard',()=>{
  const app=read('app_verified.mjs');
  assert.match(app,/parseSessionCsv/);
  assert.match(app,/parseSessionCsv\(await file\.text\(\)\)/);
  assert.doesNotMatch(app,/function parseCSV\(/);
});
