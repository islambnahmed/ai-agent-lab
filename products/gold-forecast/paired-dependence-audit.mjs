/**
 * Diagnostic of serial dependence in paired forecast losses.
 * No significance or skill verdict: overlapping training histories, model
 * selection, data revisions and nonstationarity are NOT fixed by HAC.
 */
const average = xs => xs.reduce((a,b)=>a+b,0)/xs.length;
const ISO = /^\d{4}-\d{2}-\d{2}$/;
function checkDate(s) {
  if(typeof s!=='string' || !ISO.test(s) || new Date(s+'T00:00:00Z').toISOString().slice(0,10)!==s)
    throw Error('Invalid ISO date');
}
export function pairedDependenceAudit(windows, options={}) {
  const {minimumWindows=20, lag=null} = options;
  if(!Array.isArray(windows)) throw Error('windows must be an array');
  if(!Number.isInteger(minimumWindows)||minimumWindows<2) throw Error('Invalid minimumWindows');
  const d=[];
  let prevTarget=null;
  for(const w of windows) {
    if(!w || typeof w!=='object') throw Error('Invalid window');
    checkDate(w.origin_date); checkDate(w.target_date);
    if(w.origin_date>=w.target_date) throw Error('Invalid target order');
    if(prevTarget!==null && prevTarget>w.origin_date) throw Error('Overlapping or unordered windows');
    prevTarget=w.target_date;
    for(const key of ['baseline','candidate','actual']) {
      if(typeof w[key]!=='number'||!Number.isFinite(w[key])||w[key]<=0) throw Error('Invalid price');
    }
    const b=Math.abs(w.baseline-w.actual), c=Math.abs(w.candidate-w.actual);
    for(const [key,expected] of [['baseline_abs_error',b],['candidate_abs_error',c]]) {
      if(key in w && (typeof w[key]!=='number'||!Number.isFinite(w[key])||Math.abs(w[key]-expected)>1e-8*Math.max(1,expected)))
        throw Error('Inconsistent recorded error');
    }
    d.push(b-c); // positive = candidate better
  }
  const n=d.length;
  if(lag!==null && (!Number.isInteger(lag)||lag<0||lag>=n)) throw Error('Invalid lag');
  if(n<minimumWindows || n<3) return {
    status:'insufficient_windows',n,minimum_windows:minimumWindows,
    mean_improvement:n?average(d):null, iid_standard_error:null,hac_standard_error:null,
    lag:null,claim_of_skill:false
  };
  const L=lag??Math.max(1,Math.min(n-1,Math.floor(n**0.25)));
  const m=average(d), centered=d.map(x=>x-m);
  const gamma=k=>centered.slice(k).reduce((s,x,i)=>s+x*centered[i],0)/n;
  const g0=gamma(0);
  const iidSE=Math.sqrt(g0*n/(n-1)/n);
  const longRun=g0+2*Array.from({length:L},(_,i)=>{
    const k=i+1;return (1-k/(L+1))*gamma(k);
  }).reduce((a,b)=>a+b,0);
  const hacSE=Math.sqrt(Math.max(0,longRun)/n);
  const degenerate=g0<1e-20||longRun<1e-20;
  return {
    status:degenerate?'degenerate_variance':'diagnostic_only',
    n,minimum_windows:minimumWindows,lag:L,
    mean_improvement:m, iid_standard_error:iidSE,hac_standard_error:hacSE,
    iid_nominal_z:degenerate?null:m/iidSE,
    hac_nominal_z:degenerate?null:m/hacSE,
    hac_to_iid_se_ratio:iidSE>0?hacSE/iidSE:null,
    claim_of_skill:false,
    caveat:'Diagnostic only. HAC assumes a reasonably stable short-memory loss process; disjoint windows can still depend. Nominal z is NOT a valid post-selection skill test.'
  };
}
