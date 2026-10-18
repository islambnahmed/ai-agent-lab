import test from 'node:test';
import assert from 'node:assert/strict';
import {assertVintageOverlap} from '../vintage-overlap.mjs';

const f=[{date:'2026-10-01',price:100},{date:'2026-10-02',price:101},{date:'2026-10-04',price:102}];
const future={date:'2026-10-05',price:103};
const check=r=>assertVintageOverlap(f,r,'2026-10-04');

test('unchanged vintage with future close is accepted',()=>assert.deepEqual(check([...f,future]),{compared:3,leftTruncated:false}));
test('rolling left truncation is accepted',()=>assert.deepEqual(check([...f.slice(1),future]),{compared:2,leftTruncated:true}));
test('interior historical date insertion quarantined',()=>assert.throws(()=>check([f[0],f[1],{date:'2026-10-03',price:101.5},f[2],future]),/dates/));
test('interior historical date deletion quarantined',()=>assert.throws(()=>check([f[0],f[2],future]),/dates/));
test('historical price revision quarantined',()=>assert.throws(()=>check([f[0],{...f[1],price:900},f[2],future]),/price/));
test('missing origin quarantined',()=>assert.throws(()=>check([f[0],f[1],future]),/Origin missing/));
test('origin mismatch quarantined',()=>assert.throws(()=>assertVintageOverlap(f,[...f,future],'2026-10-03'),/Invalid frozen/));
test('backfilled older history quarantined',()=>assert.throws(()=>check([{date:'2026-09-30',price:99},...f,future]),/dates/));
