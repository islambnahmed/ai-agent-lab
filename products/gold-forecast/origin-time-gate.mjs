/** Fail-closed research-origin timestamps from observed M1 bid bars.
 * Minute labels denote bar starts; add one minute before joining macro data.
 * This is NOT evidence of vendor publication latency or trade execution time.
 */
const MINUTE=/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:00(?:Z|\+00:00)$/;
function minuteClose(stamp,date){
  if(typeof stamp!=='string'||!MINUTE.test(stamp))throw Error('Expected UTC minute-bar timestamp');
  const ms=Date.parse(stamp);
  if(!Number.isFinite(ms)||new Date(ms).toISOString().slice(0,10)!==date||
     new Date(ms).toISOString().slice(11,19)!==stamp.slice(11,19))throw Error('Invalid UTC minute timestamp or day');
  return ms;
}
export function deriveResearchOriginTimes(series,dayAudit){
  if(!Array.isArray(series)||!Array.isArray(dayAudit)||!series.length)throw Error('Price series and day audit required');
  const byDate=new Map();
  for(const row of dayAudit){
    if(!row||typeof row.date!=='string'||byDate.has(row.date))throw Error('Duplicate/invalid audited day');
    byDate.set(row.date,row);
  }
  let previous=-Infinity;
  return series.map(row=>{
    if(!row||typeof row.date!=='string'||!Number.isFinite(row.price)||row.price<=0)throw Error('Invalid price row');
    const audit=byDate.get(row.date);
    if(!audit||audit.price!==row.price||!Number.isInteger(audit.observedMinutes)||audit.observedMinutes<1||audit.observedMinutes>1440)
      throw Error('Missing/mismatched source minute audit: '+row.date);
    const first=minuteClose(audit.firstMinuteAt,row.date);
    const last=minuteClose(audit.lastMinuteAt,row.date);
    if(first>last||last<=previous)throw Error('Out-of-order minute audit: '+row.date);
    previous=last;
    return new Date(last+60_000).toISOString();
  });
}
