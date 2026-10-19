// Khepri experiment 313: neutral-aware diagnostic; not a model selector.
export function directionAudit(rows,{relativeTolerance=0,absoluteTolerance=0}={}){
  if(!Array.isArray(rows)||!rows.length)throw Error('No evaluation rows');
  if(!Number.isFinite(relativeTolerance)||relativeTolerance<0||!Number.isFinite(absoluteTolerance)||absoluteTolerance<0)throw Error('Invalid neutral tolerance');
  const matrix={down:{down:0,neutral:0,up:0},neutral:{down:0,neutral:0,up:0},up:{down:0,neutral:0,up:0}};
  let mae=0,legacy=0,decisive=0,hits=0,up=0,down=0,upHit=0,downHit=0;
  for(const r of rows){
    if(!r||![r.originClose,r.point,r.actual].every(Number.isFinite)||r.originClose<=0||r.point<=0||r.actual<=0)throw Error('Invalid evaluation row');
    const t=Math.max(absoluteTolerance,relativeTolerance*r.originClose);
    const label=x=>x>t?'up':x < -t?'down':'neutral';
    const pred=label(r.point-r.originClose),actual=label(r.actual-r.originClose);
    matrix[actual][pred]++;mae+=Math.abs(r.point-r.actual);
    legacy+=Number(Math.sign(r.point-r.originClose)===Math.sign(r.actual-r.originClose));
    if(actual==='up'){up++;upHit+=Number(pred==='up');}
    if(actual==='down'){down++;downHit+=Number(pred==='down');}
    if(pred!=='neutral'){decisive++;hits+=Number(pred===actual);}
  }
  return {n:rows.length,mae:mae/rows.length,legacyDirectionAccuracy:100*legacy/rows.length,
    actionCoveragePct:100*decisive/rows.length,actionableHitRatePct:decisive?100*hits/decisive:null,
    balancedRecallPct:up&&down?50*(upHit/up+downHit/down):null,
    actualClassCounts:{up,down,neutral:Object.values(matrix.neutral).reduce((a,b)=>a+b,0)},
    confusionActualRows:matrix};
}
