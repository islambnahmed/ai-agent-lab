import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {preserveFirstObservedTarget} from '../settlement-observations.mjs';
import {gateSettlement,summarizeSettlements} from '../settlement-eligibility.mjs';

const id='c'.repeat(64),digest='d'.repeat(64);
const arithmetic={id,horizon:7,status:'matured',targetDate:'2026-10-12',
  actual:4200,modelAbsError:5,baselineAbsError:12,covered:true};
const setup=t=>{
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),'gold-policy-integration-'));
  t.after(()=>fs.rmSync(directory,{recursive:true,force:true}));
  return {directory,observedAt:'2026-10-13T12:00:00Z',sourceDigest:digest};
};
const pipeline=(outcome,options)=>gateSettlement(preserveFirstObservedTarget(outcome,options));

test('matching matured targets remain provisional and never enter headline MAE',t=>{
  const options=setup(t);
  const first=pipeline(arithmetic,options);
  assert.equal(first.status,'provisional');
  assert.equal(first.modelAbsError,5);
  assert.equal(pipeline(arithmetic,options).status,'provisional');
  const summary=summarizeSettlements([first])[1];
  assert.equal(summary.matured,0);
  assert.equal(summary.provisional,1);
  assert.equal(summary.modelMae,null);
  assert.equal(summary.baselineMae,null);
  const record=JSON.parse(fs.readFileSync(path.join(options.directory,id+'.json'),'utf8'));
  assert.equal(record.actual,4200);
});

test('revised target is quarantined before the timing gate, with no error leakage',t=>{
  const options=setup(t);
  pipeline(arithmetic,options);
  const revised=pipeline({...arithmetic,actual:4300,modelAbsError:95},options);
  assert.equal(revised.status,'quarantined');
  assert.equal(revised.modelAbsError,undefined);
  assert.equal(revised.baselineAbsError,undefined);
  const summary=summarizeSettlements([revised])[1];
  assert.equal(summary.quarantined,1);
  assert.equal(summary.provisional,0);
  assert.equal(summary.modelMae,null);
});

test('pending and preexisting quarantine remain fail-closed',t=>{
  const options=setup(t);
  const pending=pipeline({id,horizon:7,status:'pending'},options);
  const bad=pipeline({id,horizon:7,status:'quarantined',error:'vintage mismatch'},options);
  assert.equal(pending.status,'pending');
  assert.equal(bad.status,'quarantined');
  assert.equal(fs.existsSync(path.join(options.directory,id+'.json')),false);
  const summary=summarizeSettlements([pending,bad])[1];
  assert.equal(summary.pending,1);
  assert.equal(summary.quarantined,1);
  assert.equal(summary.matured,0);
});

test('order matters: timing gate must not run before first-target capture',t=>{
  const options=setup(t);
  assert.throws(()=>preserveFirstObservedTarget(gateSettlement(arithmetic),options),
    /Invalid settlement outcome/);
  assert.equal(pipeline(arithmetic,options).status,'provisional');
});
