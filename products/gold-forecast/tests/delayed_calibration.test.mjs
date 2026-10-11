import test from 'node:test';
import assert from 'node:assert/strict';
import {conformalQuantile,DelayedCalibrator,intervalScore} from '../delayed_calibration.mjs';

test('quantile finite sample exact rank and no finite rank',()=>{
 assert.equal(conformalQuantile([.3,.1,.2,.5,.4],.2),.5);
 assert.equal(conformalQuantile([.1,.2],.2),null);
 assert.equal(conformalQuantile([.2,.1,.4,.3],.5),.3);
});
test('no future residual can enter window before its target matures',()=>{
 const c=new DelayedCalibrator({horizon:3,window:10,minCalibration:1,alpha:.5});
 for(let t=0;t<3;t++){assert.equal(c.observe(t,100),null);assert.equal(c.issue(t,100).band,null);assert.equal(c.scores.length,0)}
 const r=c.observe(3,150);assert.equal(r.origin,0);assert.equal(r.score,.5);
 assert.equal(c.scores.length,1);assert.equal(c.issue(3,100).band,.5);
 assert.equal(c.pending.size,3);
});
test('displayed interval membership equals recorded hit including asymmetric actual',()=>{
 const c=new DelayedCalibrator({horizon:1,window:5,minCalibration:1,alpha:.5});
 c.observe(0,100);c.issue(0,100);
 c.observe(1,150);const r=c.issue(1,100);assert.equal(r.band,.5);assert.equal(r.lower,50);assert.equal(r.upper,150);
 assert.equal(c.observe(2,200).hit,false);
});
test('bounded rolling window',()=>{
 const c=new DelayedCalibrator({horizon:1,window:3,minCalibration:1,alpha:.5});
 for(let t=0;t<20;t++){c.observe(t,100+t);c.issue(t,100)}
 assert.equal(c.scores.length,3);assert.equal(c.pending.size,1);
});
test('rejects duplicate issues, nonsequential labels and bad values',()=>{
 const c=new DelayedCalibrator();
 assert.throws(()=>c.issue(0,100));assert.throws(()=>c.observe(1,100));
 c.observe(0,100);c.issue(0,100);
 assert.throws(()=>c.issue(0,100));assert.throws(()=>c.observe(0,100));
 assert.throws(()=>c.observe(1,0));assert.throws(()=>c.observe(1,Infinity));
});
test('separate horizon streams do not share immature labels',()=>{
 const a=new DelayedCalibrator({horizon:1,window:10,minCalibration:1,alpha:.5});
 const b=new DelayedCalibrator({horizon:7,window:10,minCalibration:1,alpha:.5});
 for(let t=0;t<6;t++){a.observe(t,100+t);b.observe(t,100+t);a.issue(t,100);b.issue(t,100)}
 assert.equal(a.scores.length,5);assert.equal(b.scores.length,0);
});
test('proper interval score penalizes both excessive width and misses',()=>{
 assert.ok(intervalScore(120,100,.1)>intervalScore(120,100,.2));
 assert.ok(intervalScore(100,100,.5)>intervalScore(100,100,.1));
});
test('invalid config and scores rejected',()=>{
 assert.throws(()=>new DelayedCalibrator({horizon:0}));
 assert.throws(()=>new DelayedCalibrator({minCalibration:100,window:10}));
 assert.throws(()=>conformalQuantile([-.2],.2));
 assert.throws(()=>intervalScore(0,100,.1));
});
