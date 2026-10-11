/** Fail-closed observation-time gate for daily XAU/USD historical closes.
 * Prevents future and same-UTC-day observations being treated as completed
 * daily closes. NOT proof of publication vintage, source authenticity,
 * absence of revisions, calendar accuracy, or predictive skill.
 */
const DAY=/^\d{4}-\d{2}-\d{2}$/;
const ZONED=/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,3})?)?(?:Z|[+-]\d{2}:\d{2})$/;
function parseInstant(s,label){
  if(typeof s!=='string'||!ZONED.test(s))throw Error(label+': explicit ISO timezone required');
  const calendarDay=s.slice(0,10);
  if(new Date(calendarDay+'T00:00:00Z').toISOString().slice(0,10)!==calendarDay)throw Error(label+': invalid calendar date');
  const ms=Date.parse(s);
  if(!Number.isFinite(ms))throw Error(label+': invalid timestamp');
  return ms;
}
function parseObservationDate(value){
  if(typeof value!=='string')throw Error('Observation date must be a string');
  if(DAY.test(value)){
    const ms=Date.parse(value+'T00:00:00Z');
    if(!Number.isFinite(ms)||new Date(ms).toISOString().slice(0,10)!==value)throw Error('Invalid observation date');
    return value;
  }
  return new Date(parseInstant(value,'Observation timestamp')).toISOString().slice(0,10);
}
function positivePrice(p){
  if(typeof p!=='number'&&(typeof p!=='string'||!/^\d+(?:\.\d+)?$/.test(p.trim())))throw Error('Invalid close price');
  const n=Number(p);
  if(!Number.isFinite(n)||n<=0)throw Error('Invalid close price');
  return n;
}
/** @returns {{series:Array<{date:string,price:number}>,excludedSameDay:number,latestDate:string,ageDays:number,asOf:string}} */
export function validateHistoricalCloses(raw,options={}){
  if(!Array.isArray(raw))throw Error('Expected array of historical observations');
  const {asOf,requireFresh=true,maxAgeDays=7,minRows=165}=options;
  const asOfMs=parseInstant(asOf,'asOf');
  if(!Number.isInteger(maxAgeDays)||maxAgeDays<0||!Number.isInteger(minRows)||minRows<1||typeof requireFresh!=='boolean')throw Error('Invalid gate options');
  const asOfDay=new Date(asOfMs).toISOString().slice(0,10);
  const seen=new Map();let excludedSameDay=0;
  for(const row of raw){
    if(!row||typeof row!=='object'||Array.isArray(row))throw Error('Invalid observation');
    const date=parseObservationDate(row.t??row.date);
    const price=positivePrice(row.price??row.close);
    if(date>asOfDay)throw Error('Future-dated observation: '+date);
    if(date===asOfDay){excludedSameDay++;continue;}
    if(seen.has(date)&&seen.get(date)!==price)throw Error('Conflicting duplicate close: '+date);
    seen.set(date,price);
  }
  const series=[...seen].sort((a,b)=>a[0].localeCompare(b[0])).map(([date,price])=>({date,price}));
  if(series.length<minRows)throw Error('Insufficient completed closes: '+series.length+'/'+minRows);
  const latestDate=series.at(-1).date;
  const ageDays=Math.floor((Date.parse(asOfDay+'T00:00:00Z')-Date.parse(latestDate+'T00:00:00Z'))/86400000);
  if(requireFresh&&ageDays>maxAgeDays)throw Error('Stale completed close: '+ageDays+' calendar days old');
  return {series,excludedSameDay,latestDate,ageDays,asOf};
}
