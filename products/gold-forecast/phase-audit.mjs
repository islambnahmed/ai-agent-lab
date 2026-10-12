/** Phase sensitivity across disjoint forecast-origin offsets. */
export function phaseSensitivity(rows,h){
  if(!Array.isArray(rows)||!Number.isInteger(h)||h<1||h>365)throw Error('Invalid input');
  return Array.from({length:h},(_,offset)=>({offset,n:rows.filter(r=>r.originIndex%h===offset).length}));
}
