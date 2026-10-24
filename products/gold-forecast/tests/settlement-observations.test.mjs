import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {preserveFirstObservedTarget as preserve} from '../settlement-observations.mjs';
const id='a'.repeat(64),digest='b'.repeat(64);
const mature={id,horizon:1,status:'matured',targetDate:'2026-10-12',actual:4200,
  modelAbsError:10,baselineAbsError:20};
const options=t=>{const directory=fs.mkdtempSync(path.join(os.tmpdir(),'gold-target-'));
  t.after(()=>fs.rmSync(directory,{recursive:true,force:true}));
  return {directory,observedAt:'2026-10-13T12:00:00Z',sourceDigest:digest};};
test('first target is recorded once, and repeated matching target is accepted',t=>{
  const opt=options(t);
  assert.equal(preserve(mature,opt).status,'matured');
  const filename=path.join(opt.directory,id+'.json');
  const original=fs.readFileSync(filename,'utf8');
  assert.equal(preserve(mature,{...opt,observedAt:'2026-10-14T12:00:00Z'}).status,'matured');
  assert.equal(fs.readFileSync(filename,'utf8'),original);
});
test('revised target price cannot silently change reported settlement',t=>{
  const opt=options(t);preserve(mature,opt);
  const r=preserve({...mature,actual:4400,modelAbsError:190},opt);
  assert.equal(r.status,'quarantined');assert.match(r.error,/revised/);
  assert.equal(r.modelAbsError,undefined);
});
test('inserted future observation cannot silently change target date',t=>{
  const opt=options(t);preserve(mature,opt);
  assert.equal(preserve({...mature,targetDate:'2026-10-11'},opt).status,'quarantined');
});
test('previously matured target cannot silently revert to pending',t=>{
  const opt=options(t);preserve(mature,opt);
  assert.equal(preserve({id,horizon:1,status:'pending'},opt).status,'quarantined');
});
test('pending does not create baseline and quarantine remains quarantine',t=>{
  const opt=options(t);
  assert.equal(preserve({id,horizon:1,status:'pending'},opt).status,'pending');
  assert.equal(fs.existsSync(path.join(opt.directory,id+'.json')),false);
  assert.equal(preserve({id,horizon:1,status:'quarantined',error:'bad vintage'},opt).status,'quarantined');
});
test('corrupt local record fails closed instead of being overwritten',t=>{
  const opt=options(t);fs.writeFileSync(path.join(opt.directory,id+'.json'),'{');
  assert.equal(preserve(mature,opt).status,'quarantined');
  fs.writeFileSync(path.join(opt.directory,id+'.json'),'null');
  assert.equal(preserve(mature,opt).status,'quarantined');
});
test('invalid receipt IDs and invalid maturity values are rejected',t=>{
  const opt=options(t);
  assert.throws(()=>preserve({...mature,id:'../../foo'},opt),TypeError);
  assert.throws(()=>preserve({...mature,actual:Infinity},opt),TypeError);
});
