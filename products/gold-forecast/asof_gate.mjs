/** Point-in-time daily data gate for the Gold MVP.
 * Explicit asOf enables reproducible replay. Calendar-day limits are policy,
 * not proof of an exchange trading calendar or original publication vintage.
 */
const DAY=86400000;
const iso=d=>d.toISOString().slice(0,10);
const midnight=d=>Date.parse(d+"T00:00:00Z");
function parseDate(v){
  if(typeof v!=="string")throw Error("Missing/non-string date");
  if(/^\d{4}-\d{2}-\d{2}$/.test(v)){
    const t=midnight(v);
    if(!Number.isFinite(t)||iso(new Date(t))!==v)throw Error("Invalid calendar date");
    return {day:v,t,datedOnly:true};
  }
  if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(v))
    throw Error("Ambiguous timestamp; ISO with timezone required");
  const t=Date.parse(v),localDay=v.slice(0,10),clock=v.slice(11,19);
  if(!Number.isFinite(t)||!Number.isFinite(midnight(localDay))||
     iso(new Date(midnight(localDay)))!==localDay||
     +clock.slice(0,2)>23||+clock.slice(3,5)>59||+clock.slice(6,8)>59)
    throw Error("Invalid calendar timestamp");
  return {day:iso(new Date(t)),t,datedOnly:false};
}
export function auditDailySeries(raw,{asOf,maxAgeDays=7,maxGapDays=7,minValue=Number.EPSILON,minRows=3}={}){
  if(!Array.isArray(raw)||!raw.length)throw Error("Missing daily observations");
  const now=typeof asOf==="string"?Date.parse(asOf):asOf instanceof Date?asOf.getTime():NaN;
  if(!Number.isFinite(now))throw Error("Explicit valid asOf required");
  if(![maxAgeDays,maxGapDays,minRows].every(Number.isInteger)||maxAgeDays<0||
     maxGapDays<1||minRows<2||!Number.isFinite(minValue))throw Error("Invalid audit policy");
  const daily=new Map();
  for(const p of raw){
    const {day,t,datedOnly}=parseDate(p?.t??p?.date);
    if(datedOnly&&day===iso(new Date(now)))
      throw Error("Same-day daily close lacks verified publication timestamp: "+day);
    if(p?.price==null&&p?.close==null)throw Error("Missing price: "+day);
    const price=Number(p?.price??p?.close);
    if(!Number.isFinite(price)||price<minValue)throw Error("Invalid value: "+day);
    if(t>now)throw Error("Future observation: "+day);
    if(daily.has(day)&&!Object.is(daily.get(day),price))
      throw Error("Conflicting observations: "+day);
    daily.set(day,price);
  }
  const rows=[...daily].sort(([a],[b])=>a.localeCompare(b)).map(([date,price])=>({date,price}));
  if(rows.length<minRows)throw Error("Insufficient observations: "+rows.length);
  const age=(midnight(iso(new Date(now)))-midnight(rows.at(-1).date))/DAY;
  if(age>maxAgeDays)throw Error("Stale daily history: "+age+" days");
  for(let i=1;i<rows.length;i++){
    const gap=(midnight(rows[i].date)-midnight(rows[i-1].date))/DAY;
    if(gap>maxGapDays)throw Error("Unexplained "+gap+"-day gap ending "+rows[i].date);
  }
  return {rows,latest:rows.at(-1).date,ageDays:age,duplicatesCollapsed:raw.length-rows.length};
}
