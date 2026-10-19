import test from 'node:test';
import assert from 'node:assert/strict';
test('UTC date equivalence',()=>assert.equal(new Date('2026-10-18T23:00:00-05:00').toISOString().slice(0,10),'2026-10-19'));
