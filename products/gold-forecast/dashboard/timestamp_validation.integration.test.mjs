import test from 'node:test';
import assert from 'node:assert/strict';
import {buildSnapshot,FROZEN} from './evidence_snapshot.mjs';
import {makeView} from './dashboard_view.mjs';

test('snapshot refuses invalid asOf date and timezone offset',()=>{
  for(const asOf of ['2026-02-30T12:00:00Z','2026-10-30T12:00:00+14:30'])
    assert.throws(()=>buildSnapshot({asOf}),/asOf/);
});
test('snapshot refuses invalid capturedAt timestamp',()=>{
  const row={date:'2026-10-19',price:4180,capturedAt:'2026-10-30T11:00:00+14:30',sourceId:FROZEN.sourceId,sourceSession:FROZEN.sourceSession};
  assert.throws(()=>buildSnapshot({asOf:'2026-10-30T12:00:00Z',observations:[row]}),/timestamp/);
});
test('view refuses invalid generatedAsOf timestamp',()=>{
  const s=buildSnapshot({asOf:'2026-10-30T12:00:00Z'});
  s.generatedAsOf='2026-02-30T12:00:00Z';
  assert.throws(()=>makeView(s),/Invalid research snapshot/);
});
