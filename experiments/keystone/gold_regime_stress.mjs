/**
 * Reproducible synthetic-regime challenge for the *existing* Gold Lab predictors.
 * No live data, no provider downloads, no portfolio returns, no model promotion.
 * Run: node experiments/keystone/gold_regime_stress.mjs [--seeds=12] [--json]
 */
import {predict} from '../../products/gold-forecast/models.mjs';

export const SCENARIOS = Object.freeze(['iid', 'momentum', 'regime_flip']);
export const HORIZONS = Object.freeze([1, 7, 30]);
export const MODELS = Object.freeze(['persistence', 'momentum', 'mean_reversion', 'ridge']);
const N = 360;
const SPLIT = 240;
const WARMUP = 80;

function rng(seed) {
  let state = seed >>> 0;
  if (!state) state = 0x6d2b79f5;
  return () => {
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    return (state >>> 0) / 4294967296;
  };
}
function normal(random) {
  // Fixed Box-Muller transform; clamp away from log(0).
  const u = Math.max(random(), Number.MIN_VALUE);
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * random());
}

export function generate(scenario, seed, n = N) {
  if (!SCENARIOS.includes(scenario) || !Number.isInteger(seed) || n < SPLIT + 31)
    throw Error('Invalid synthetic scenario, seed, or length');
  const random = rng(seed), prices = [2000];
  let prev = 0;
  for (let t = 1; t < n; t++) {
    const phi = scenario === 'iid' ? 0 : scenario === 'momentum' ? 0.5 : (t < SPLIT ? 0.55 : -0.55);
    const ret = phi * prev + 0.007 * normal(random);
    prices.push(prices.at(-1) * Math.exp(ret));
    prev = ret;
  }
  return prices;
}

function origins(h, phase) {
  const first = phase === 'selection' ? WARMUP : SPLIT;
  const exclusive = phase === 'selection' ? SPLIT - h : N - h;
  const out = [];
  // Each target belongs strictly to its own phase; no boundary-crossing labels.
  for (let i = first; i < exclusive; i += h) out.push(i);
  return out;
}

export function evaluate(prices, h, phase) {
  if (!HORIZONS.includes(h) || !['selection', 'audit'].includes(phase) || prices.length !== N)
    throw Error('Invalid evaluation contract');
  const points = origins(h, phase);
  const losses = Object.fromEntries(MODELS.map(m => [m, []]));
  for (const i of points) {
    const known = prices.slice(0, i + 1);
    const actual = prices[i + h];
    for (const model of MODELS) {
      const point = predict(known, h, model);
      if (!Number.isFinite(point) || point <= 0) throw Error(`Invalid ${model} prediction`);
      losses[model].push(Math.abs(point - actual));
    }
  }
  const mae = Object.fromEntries(MODELS.map(m => [m, losses[m].reduce((a,b) => a+b,0)/points.length]));
  return {n: points.length, mae};
}

function percentile(sorted, p) {
  return sorted[Math.max(0, Math.min(sorted.length - 1, Math.floor(p * (sorted.length - 1))))];
}
function bootstrapCI(values, seed = 0x5eeda11) {
  const random = rng(seed), means = [];
  for (let b = 0; b < 400; b++) {
    let total = 0;
    for (let i = 0; i < values.length; i++) total += values[Math.floor(random() * values.length)];
    means.push(total / values.length);
  }
  means.sort((a,b) => a-b);
  return [percentile(means, 0.025), percentile(means, 0.975)];
}

export function run({seeds = 12} = {}) {
  if (!Number.isInteger(seeds) || seeds < 2 || seeds > 64) throw Error('seeds must be 2..64');
  const results = [];
  for (const scenario of SCENARIOS) for (const h of HORIZONS) {
    const replicates = [];
    for (let k = 0; k < seeds; k++) {
      // Independent deterministic paths across scenario/horizon/replicate.
      const seed = (0x9e3779b9 ^ ((SCENARIOS.indexOf(scenario)+1)*0x85ebca6b) ^ (h*0xc2b2ae35) ^ (k*0x27d4eb2f)) >>> 0;
      const prices = generate(scenario, seed);
      const selection = evaluate(prices, h, 'selection');
      const audit = evaluate(prices, h, 'audit');
      const winner = MODELS.reduce((best, m) => selection.mae[m] < selection.mae[best] ? m : best, 'persistence');
      const selectionSkill = 100 * (1 - selection.mae[winner]/selection.mae.persistence);
      const auditSkill = 100 * (1 - audit.mae[winner]/audit.mae.persistence);
      replicates.push({winner, selectionSkill, auditSkill, selectionN:selection.n, auditN:audit.n});
    }
    const skills = replicates.map(r => r.auditSkill);
    const mean = skills.reduce((a,b)=>a+b,0)/skills.length;
    const chosenNonBaseline = replicates.filter(r => r.winner !== 'persistence');
    results.push({scenario, horizon:h, independentPaths:seeds,
      originsPerPath:{selection:replicates[0].selectionN, audit:replicates[0].auditN},
      selected:Object.fromEntries(MODELS.map(m=>[m,replicates.filter(r=>r.winner===m).length])),
      meanAuditSkillPct:mean,
      bootstrap95Pct:bootstrapCI(skills, seedForCI(scenario,h)),
      selectedBeatsBaselineOnAudit:replicates.filter(r=>r.auditSkill>0).length,
      selectionWinnerFailsAudit:chosenNonBaseline.filter(r=>r.auditSkill<=0).length,
      nonBaselineSelections:chosenNonBaseline.length});
  }
  return {schemaVersion:1,kind:'synthetic_falsification_only',
    modelImport:'products/gold-forecast/models.mjs',
    fixedProtocol:{length:N,selectionBoundary:SPLIT,warmup:WARMUP,nonoverlapStride:'h',horizons:HORIZONS,models:MODELS,
      scenarios:{iid:'independent Gaussian log returns',momentum:'AR(1) phi=+0.50',regime_flip:'AR(1) phi +0.55 to -0.55 at selection boundary'},
      criterion:'choose minimum selection MAE; audit once without retuning',
      uncertainty:'path-level bootstrap (400 draws); descriptive, not a calibrated confidence interval for markets'},
    results,limits:['Synthetic prices are not gold prices',
      'Audit paths are generated by a fixed simulator, not an unseen real-world holdout',
      'Non-overlap within a path does not imply statistical independence',
      'Selection and audit use the same process family except the explicit regime flip',
      'No investment, predictive-skill, or model-promotion conclusion']};
}
function seedForCI(scenario,h) {return (0x5eeda11 ^ ((SCENARIOS.indexOf(scenario)+1)*65537) ^ h) >>> 0;}

if (process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href) {
  const allowed = process.argv.slice(2);
  if (allowed.some(a=>a!=='--json'&&!/^--seeds=\d+$/.test(a))) throw Error('Usage: node gold_regime_stress.mjs [--seeds=12] [--json]');
  const match = allowed.find(a=>a.startsWith('--seeds='));
  const report = run({seeds:match ? Number(match.split('=')[1]) : 12});
  if (allowed.includes('--json')) console.log(JSON.stringify(report,null,2));
  else {
    console.log('Synthetic falsification challenge (NOT a market backtest)');
    for (const r of report.results) console.log(`${r.scenario.padEnd(12)} h=${String(r.horizon).padStart(2)} paths=${r.independentPaths} selection=${r.originsPerPath.selection} audit=${r.originsPerPath.audit} mean audit skill=${r.meanAuditSkillPct.toFixed(2)}% CI=[${r.bootstrap95Pct.map(x=>x.toFixed(2)).join(', ')}] nonbaseline failures=${r.selectionWinnerFailsAudit}/${r.nonBaselineSelections}`);
  }
}
