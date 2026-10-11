/** Prequential interval calibration with delayed labels.
 * At step t, first observe y[t], then issue forecast from history through t
 * targeting t+h. No future label may enter calibration.
 * Diagnostic only: no coverage guarantee under drift/dependence.
 */
export function conformalQuantile(scores, alpha=0.2) {
  if (!Array.isArray(scores) || !scores.length || !Number.isFinite(alpha) || alpha<=0 || alpha>=1 ||
      scores.some(s=>!Number.isFinite(s)||s<0)) throw Error('Invalid calibration scores/alpha');
  const n=scores.length, rank=Math.ceil((n+1)*(1-alpha));
  if(rank>n) return null;
  return [...scores].sort((a,b)=>a-b)[rank-1];
}
export class DelayedCalibrator {
  constructor({horizon=7,alpha=0.2,window=60,minCalibration=30}={}) {
    if(!Number.isInteger(horizon)||horizon<1||!Number.isInteger(window)||window<1||
       !Number.isInteger(minCalibration)||minCalibration<1||minCalibration>window||
       !Number.isFinite(alpha)||alpha<=0||alpha>=1) throw Error('Invalid configuration');
    this.horizon=horizon;this.alpha=alpha;this.window=window;this.minCalibration=minCalibration;
    this.lastObserved=-1;this.lastIssued=-1;this.pending=new Map();this.scores=[];
    this.settled=[];
  }
  observe(index,actual) {
    if(!Number.isInteger(index)||index!==this.lastObserved+1||!Number.isFinite(actual)||actual<=0)
      throw Error('Observation must be positive and sequential');
    this.lastObserved=index;
    const p=this.pending.get(index);
    if(!p) return null;
    this.pending.delete(index);
    const score=Math.abs(actual-p.point)/p.point;
    const record={...p,actual,score,hit:p.band===null?null:actual>=p.lower&&actual<=p.upper};
    this.settled.push(record);
    this.scores.push(score);
    if(this.scores.length>this.window)this.scores.shift();
    return record;
  }
  issue(index,point) {
    if(!Number.isInteger(index)||index!==this.lastObserved||this.lastIssued===index||
       !Number.isFinite(point)||point<=0)throw Error('Forecast must follow observed step exactly once');
    this.lastIssued=index;
    const band=this.scores.length>=this.minCalibration?conformalQuantile(this.scores,this.alpha):null;
    const record={origin:index,target:index+this.horizon,point,band,
      lower:band===null?null:Math.max(0,point*(1-band)),
      upper:band===null?null:point*(1+band)};
    this.pending.set(record.target,record);
    return {...record};
  }
}
export function intervalScore(actual,point,band,alpha=0.2) {
  if (![actual,point,band,alpha].every(Number.isFinite)||actual<=0||point<=0||band<0||alpha<=0||alpha>=1)
    throw Error('Invalid interval score input');
  const lower=Math.max(0,point*(1-band)),upper=point*(1+band);
  return (upper-lower)/point+2/alpha*Math.max(0,lower-actual,actual-upper)/point;
}
