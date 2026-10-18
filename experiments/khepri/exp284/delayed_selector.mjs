// Khepri exp284: causal online selector, synthetic benchmark only.
// Does not access live prices or promote a production model.
export function pointForecast(prices, i, h, model) {
  if (!Number.isInteger(i) || i < 20 || i >= prices.length || !Number.isInteger(h) || h < 1 || h > 30) throw Error('Invalid origin/horizon');
  const now = prices[i];
  if (!(now > 0) || !(prices[i-20] > 0)) throw Error('Non-positive price');
  if (model === 'persistence') return now;
  if (model === 'momentum') {
    const daily = Math.log(now / prices[i-20]) / 20;
    const cap = Math.max(-0.012, Math.min(0.012, daily));
    return now * Math.exp(cap * h * 0.45 * Math.exp(-h / 20));
  }
  throw Error('Unknown model');
}
export function decisionAt(forecasts, prices, origin, horizon, mode, opts = {}) {
  if (!Number.isInteger(origin) || !Number.isInteger(horizon) || horizon < 1 || origin < 0 || origin >= prices.length) throw Error('Invalid decision');
  if (!['naive', 'guarded', 'persistence'].includes(mode)) throw Error('Unknown mode');
  if (mode === 'persistence') return {model:'persistence',evidence:0};
  const maxOrigin = origin - horizon;
  const eligible = forecasts.filter(f => f.origin <= maxOrigin && f.origin >= 0);
  const pool = mode === 'guarded'
    ? eligible.filter(f => f.origin % horizon === 0).slice(-(opts.maxDisjoint ?? 30))
    : eligible.slice(-(opts.maxOverlapping ?? 100));
  if (pool.length < (mode === 'guarded' ? (opts.minDisjoint ?? 12) : 5)) return {model:'persistence',evidence:pool.length};
  let baseline = 0, challenger = 0, wins = 0;
  for (const row of pool) {
    const actual = prices[row.origin + horizon];
    const baseError = Math.abs(row.persistence - actual);
    const altError = Math.abs(row.momentum - actual);
    baseline += baseError;
    challenger += altError;
    if (altError < baseError) wins++;
  }
  const advantage = baseline > 0 ? 1 - challenger / baseline : -Infinity;
  const gate = mode === 'naive' ? advantage > 0 : advantage > (opts.minGain ?? 0.08) && wins / pool.length >= (opts.minWinRate ?? 0.60);
  return {model:gate ? 'momentum' : 'persistence',evidence:pool.length,advantage,winRate:wins/pool.length};
}
export function walkForward(prices, horizon, mode, opts = {}) {
  if (!Array.isArray(prices) || prices.length < 200 || prices.some(p => !Number.isFinite(p) || p <= 0)) throw Error('Invalid series');
  const start = opts.warmup ?? 65, rows = [];
  for (let i = start; i + horizon < prices.length; i++) {
    const persistence = pointForecast(prices, i, horizon, 'persistence');
    const momentum = pointForecast(prices, i, horizon, 'momentum');
    const d = decisionAt(rows, prices, i, horizon, mode, opts);
    rows.push({origin:i,persistence,momentum,chosen:d.model,evidence:d.evidence});
  }
  const auditStart = opts.auditStart ?? Math.floor(prices.length * 0.6);
  const audit = rows.filter(r => r.origin >= auditStart);
  const err = (row, m) => Math.abs(row[m] - prices[row.origin + horizon]);
  const mae = name => audit.reduce((s,r) => s + err(r,name),0)/audit.length;
  const chosen = audit.reduce((s,r) => s + err(r,r.chosen),0)/audit.length;
  return {horizon,mode,n:audit.length,mae:chosen,baselineMae:mae('persistence'),momentumMae:mae('momentum'),
    promotionRate:audit.filter(r => r.chosen === 'momentum').length/audit.length,
    rows:opts.includeRows ? rows : undefined};
}
