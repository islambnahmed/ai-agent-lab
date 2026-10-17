import test from 'node:test';
import assert from 'node:assert/strict';
import {isValidOffsetTimestamp as valid} from './timestamp_validation.mjs';
test('accepts valid UTC, offsets, leap days and milliseconds',()=>{
  for (const t of ['2026-10-16T21:26:01Z','2026-10-16T21:26:01+03:00','2026-10-16T21:26:01-14:00','2026-10-16T21:26:01+14:00','2024-02-29T00:00:00.999Z','2000-02-29T23:59:59Z','2026-10-16T21:26:01+05:45']) assert.equal(valid(t),true,t);
});
test('rejects impossible calendar dates instead of normalizing them',()=>{
  for (const t of ['2026-02-29T12:00:00Z','2026-02-30T12:00:00Z','2026-04-31T12:00:00Z','1900-02-29T12:00:00Z','2026-13-01T12:00:00Z','2026-00-01T12:00:00Z','0000-01-01T12:00:00Z','2026-01-00T12:00:00Z']) assert.equal(valid(t),false,t);
});
test('rejects invalid clock and timezone offset values',()=>{
  for (const t of ['2026-10-16T24:00:00Z','2026-10-16T23:60:00Z','2026-10-16T23:59:60Z','2026-10-16T21:26:01+14:01','2026-10-16T21:26:01-15:00','2026-10-16T21:26:01+05:60','2026-10-16T21:26:01','2026-10-16T21:26:01.1234Z']) assert.equal(valid(t),false,t);
});
test('rejects malformed and non-string values',()=>{
  for (const t of [null,undefined,0,{},'2026-10-16','2026-10-16T21:26:01z','2026-10-16T21:26:01+0300']) assert.equal(valid(t),false,String(t));
});
