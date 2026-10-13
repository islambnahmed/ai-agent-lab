/** Khepri exp158: peer-relative annual minute cadence anomaly guard.
 * Counts are screening evidence, not proof of missing bars.
 */
const median = values => {
  if (!values.length || values.some(x=>!Number.isFinite(x))) throw new Error('median needs finite numbers');
  const s=[...values].sort((a,b)=>a-b),m=s.length>>1;
  return s.length%2?s[m]:(s[m-1]+s[m])/2;
};
export function annualCadenceAudit(requests,{minPeerYears=5,lowRatio=0.92,highGapRatio=2}={}) {
  if (!Array.isArray(requests)||!Number.isInteger(minPeerYears)||minPeerYears<3 ||
      !(lowRatio>0&&lowRatio<1)||!(highGapRatio>1)) throw new Error('invalid audit input');
  const years=requests.filter(r=>/^\d{4}$/.test(String(r?.period??''))).map(r=>({
    year:Number(r.period),minuteRows:r.minuteRows,gapsOverOneMinute:r.gapsOverOneMinute,
    maxGapMinutes:r.maxGapMinutes,status:r.status
  }));
  if(new Set(years.map(x=>x.year)).size!==years.length)throw new Error('duplicate year');
  if(years.some(r=>!Number.isInteger(r.minuteRows)||r.minuteRows<1||
      !Number.isInteger(r.gapsOverOneMinute)||r.gapsOverOneMinute<0||
      !Number.isFinite(r.maxGapMinutes)||r.maxGapMinutes<0))throw new Error('bad annual counts');
  if(years.length<minPeerYears+1)throw new Error('not enough comparable years');
  return years.map(y=>{
    const peers=years.filter(x=>x.year!==y.year);
    const peerMedianRows=median(peers.map(x=>x.minuteRows));
    const peerMedianGaps=median(peers.map(x=>x.gapsOverOneMinute));
    const rowRatio=y.minuteRows/peerMedianRows;
    const gapRatio=peerMedianGaps?y.gapsOverOneMinute/peerMedianGaps:null;
    const lowMinuteCount=rowRatio<lowRatio;
    const highGapCount=gapRatio!==null&&gapRatio>highGapRatio;
    return {year:y.year,status:y.status,minuteRows:y.minuteRows,gapsOverOneMinute:y.gapsOverOneMinute,
      peerMedianRows,peerMedianGaps,rowRatio,relativeDeficitPct:100*(1-rowRatio),
      gapRatio,lowMinuteCount,highGapCount,
      needsInvestigation:lowMinuteCount,
      classification:lowMinuteCount?'peer_relative_minute_deficit':highGapCount?'fragmented_cadence_without_count_deficit':'within_peer_count_range',
      caveat:'Peer counts are screening evidence, not proof of missing minutes. Trading schedules, feed changes and quote sparsity require raw intraday verification.'};
  });
}
