/**
 * Strict point-in-time reconstruction for daily numeric observations.
 * Contract: each event has {date: 'YYYY-MM-DD', price: positive number,
 * received_at: timezone-qualified ISO 8601 timestamp}.
 * received_at must be a genuine recorded receipt time, not backfilled from date.
 * A session can have multiple versions; last received version wins only as of cutoff.
 * Identical receipt timestamps with conflicting prices fail closed.
 * No claim of tamper-proof receipts or source truth is made here.
 */
function isoDay(value){
  if(typeof value!=="string" || !/^\d{4}-\d{2}-\d{2}$/.test(value))throw Error("Invalid session date");
  const ms=Date.parse(value+"T00:00:00Z");
  if(!Number.isFinite(ms)||new Date(ms).toISOString().slice(0,10)!==value)throw Error("Invalid calendar day");
  return value;
}
function timestamp(value){
  if(typeof value!=="string" || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value))throw Error("Missing/ambiguous receipt timestamp");
  isoDay(value.slice(0,10));
  const hh=Number(value.slice(11,13)),mm=Number(value.slice(14,16)),ss=Number(value.slice(17,19));
  if(hh>23||mm>59||ss>59)throw Error("Invalid receipt clock");
  const offset=value.match(/([+-])(\d{2}):(\d{2})$/);
  if(offset&&(Number(offset[2])>14||Number(offset[3])>59||(Number(offset[2])===14&&Number(offset[3])!==0)))throw Error("Invalid receipt timezone");
  const ms=Date.parse(value);
  if(!Number.isFinite(ms))throw Error("Invalid receipt timestamp");
  return ms;
}
export function snapshotAt(events,cutoff){
  if(!Array.isArray(events))throw Error("Expected events array");
  const stop=timestamp(cutoff),day=new Date(stop).toISOString().slice(0,10),chosen=new Map();
  for(const event of events){
    const date=isoDay(event?.date);
    const price=event?.price;
    if(typeof price!=="number"||!Number.isFinite(price)||price<=0)throw Error("Invalid price");
    const received=timestamp(event.received_at);
    if(received>stop || date>day)continue;
    const prior=chosen.get(date);
    if(prior&&prior.received===received&&prior.price!==price)throw Error("Conflicting simultaneous versions");
    if(!prior||received>prior.received)chosen.set(date,{date,price,received});
  }
  return [...chosen.values()].sort((a,b)=>a.date.localeCompare(b.date)).map(({date,price})=>({date,price}));
}
export function predictAt(events,cutoff,h,model,predict){
  const series=snapshotAt(events,cutoff);
  if(series.length<42)throw Error("Insufficient point-in-time observations");
  return {prediction:predict(series.map(x=>x.price),h,model),lastDate:series.at(-1).date,observations:series.length};
}
