// Standalone audit: reproduces directionAccuracy formula in gold-forecast/forecast.mjs
// from main blob 2cd3731fbb764967387270b0aeafa4ed25fafabd.
// This is an experiment, not a production replacement or trading signal.
export function legacyDirectionAccuracy(rows) {
  if (!rows.length) throw Error('No evaluation rows');
  return 100 * rows.reduce((sum, r) => sum + (Math.sign(r.point-r.originClose) === Math.sign(r.actual-r.originClose) ? 1 : 0), 0) / rows.length;
}

export function directionDiagnostics(rows, {minMovePct=0}={}) {
  if (!Array.isArray(rows) || !rows.length) throw Error('No evaluation rows');
  if (!Number.isFinite(minMovePct) || minMovePct < 0) throw Error('Invalid minimum move');
  const sign=(change, origin) => Math.abs(change)/origin * 100 <= minMovePct ? 0 : Math.sign(change);
  let active=0, hits=0, flatActual=0, upActual=0, downActual=0, activeOnFlat=0;
  for (const r of rows) {
    if (![r.point,r.actual,r.originClose].every(Number.isFinite) || r.originClose<=0 || r.point<=0 || r.actual<=0) throw Error('Invalid row');
    const predicted=sign(r.point-r.originClose,r.originClose);
    const observed=sign(r.actual-r.originClose,r.originClose);
    if (observed===0) flatActual++;
    else if (observed===1) upActual++;
    else downActual++;
    if (predicted!==0) {
      active++;
      if (predicted===observed) hits++;
      if (observed===0) activeOnFlat++;
    }
  }
  const n=rows.length;
  return {
    n,active,abstained:n-active,participationPct:100*active/n,
    conditionalDirectionalAccuracyPct:active?100*hits/active:null,
    hits,flatActual,upActual,downActual,activeOnFlat,
    // Fixed comparator policies, never an ex-post selected winner.
    alwaysUpAccuracyPct:100*upActual/n,
    alwaysDownAccuracyPct:100*downActual/n,
    legacyDirectionAccuracyPct:legacyDirectionAccuracy(rows),
    caveat:'Conditional accuracy without participation and precommitted comparator is not evidence of edge.'
  };
}
