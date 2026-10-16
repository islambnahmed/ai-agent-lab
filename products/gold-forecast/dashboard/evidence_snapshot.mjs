// Research-only, fail-closed snapshot. Capture time is NOT publication proof.
export const FROZEN = Object.freeze({
  batchId:'worker-a-2026-10-16-cycle169',
  anchorCommit:'609fc40a6233ea25ff1f6716a5bcc5df8c37f321',
  anchorCommittedAt:'2026-10-16T21:26:01Z',
  originDate:'2026-10-16', originPrice:4181.90,
  sourceId:'westmetall-gold-usd-ozt-london-2026', sourceSession:'unspecified',
  predictions:Object.freeze({1:4176.897267384459,7:4168.677039660794,30:4154.572183780181})
});
const day=d=>typeof d==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(d)&&
  !Number.isNaN(Date.parse(d+'T00:00:00Z'))&&new Date(d+'T00:00:00Z').toISOString().slice(0,10)===d;
const time=t=>typeof t==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2})$/.test(t)&&Number.isFinite(Date.parse(t));
const fail=m=>{throw Error(m)};
export function buildSnapshot({asOf,observations=[],sourceId=FROZEN.sourceId,sourceSession=FROZEN.sourceSession}={}) {
  if(!time(asOf)) fail('asOf must be an offset-aware timestamp');
  if(sourceId!==FROZEN.sourceId||sourceSession!==FROZEN.sourceSession) fail('Source/session identity mismatch');
  if(!Array.isArray(observations)||observations.length>1000) fail('Invalid observations');
  const now=Date.parse(asOf),anchor=Date.parse(FROZEN.anchorCommittedAt);
  if(now<anchor) fail('Snapshot predates anchor');
  let previous=FROZEN.originDate;
  for(const [i,r] of observations.entries()) {
    if(!r||!day(r.date)||r.date<=previous) fail('Invalid or unordered date at '+i);
    if(typeof r.price!=='number'||!Number.isFinite(r.price)||r.price<=0) fail('Invalid price at '+i);
    if(!time(r.capturedAt)) fail('Missing capture timestamp at '+i);
    const captured=Date.parse(r.capturedAt);
    if(captured>now||captured<anchor||captured<Date.parse(r.date+'T00:00:00Z')) fail('Invalid capture at '+i);
    if(r.sourceId!==FROZEN.sourceId||r.sourceSession!==FROZEN.sourceSession) fail('Source/session mismatch at '+i);
    previous=r.date;
  }
  const forecasts=[1,7,30].map(h=>{
    const point=FROZEN.predictions[h];
    if(observations.length<h) return {horizon:h,point,status:'pending',observedSinceOrigin:observations.length,required:h};
    const target=observations[h-1],b=Math.abs(FROZEN.originPrice-target.price),c=Math.abs(point-target.price);
    return {horizon:h,point,status:'matured_timing_unverified',targetDate:target.date,
      baselineAbsoluteError:b,challengerAbsoluteError:c,improvementUsd:b-c,
      directionCorrect:Math.sign(point-FROZEN.originPrice)===Math.sign(target.price-FROZEN.originPrice),
      caveat:'Self-declared capture time does not prove provider publication chronology.'};
  });
  return {schemaVersion:1,batchId:FROZEN.batchId,generatedAsOf:asOf,
    anchorCommit:FROZEN.anchorCommit,anchorCommittedAt:FROZEN.anchorCommittedAt,
    reference:{date:FROZEN.originDate,price:FROZEN.originPrice,unit:'USD/troy oz',sourceId:FROZEN.sourceId,session:FROZEN.sourceSession},
    observedSinceOrigin:observations.length,forecastStatus:'research_only',forecasts,
    warnings:['Not a live quote.','Matured outcomes remain timing-unverified.','No demonstrated predictive skill or profitability.']};
}
