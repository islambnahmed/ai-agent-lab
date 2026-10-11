import {parseGoldCsv} from './csv_guard.mjs';

// Weekday proxy only: not an exchange holiday calendar or authenticated market feed.
export function parseSessionCsv(text,{nowMs=Date.now(),minSessions=237}={}) {
  if (!Number.isInteger(minSessions) || minSessions<1) throw Error('Invalid minimum session count');
  const rows=parseGoldCsv(text,{nowMs,minPoints:minSessions});
  const series=rows.filter(({date})=>{
    const weekday=new Date(date+'T12:00:00Z').getUTCDay();
    return weekday!==0 && weekday!==6;
  });
  if (series.length<minSessions) throw Error('CSV needs at least '+minSessions+' weekday sessions; got '+series.length+' after excluding '+(rows.length-series.length)+' weekend rows');
  return {series,weekendRowsExcluded:rows.length-series.length};
}
