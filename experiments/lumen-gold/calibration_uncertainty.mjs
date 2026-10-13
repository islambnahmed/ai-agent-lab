#!/usr/bin/env node
import { readFileSync } from 'node:fs';

export function wilson95(k, n) {
  if (!Number.isInteger(k) || !Number.isInteger(n) || n < 1 || k < 0 || k > n) {
    throw new RangeError('Expected integers with 0 <= successes <= n and n >= 1');
  }
  const z = 1.959963984540054;
  const p = k / n;
  const z2 = z * z;
  const den = 1 + z2 / n;
  const center = (p + z2 / (2 * n)) / den;
  const radius = z * Math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / den;
  return [Math.max(0, center - radius), Math.min(1, center + radius)];
}

export function countFromRoundedCoverage(n, percentage) {
  if (!Number.isInteger(n) || n < 1 || !Number.isFinite(percentage) || percentage < 0 || percentage > 100) {
    throw new RangeError('Invalid n or coverage percentage');
  }
  const raw = n * percentage / 100;
  const k = Math.round(raw);
  if (Math.abs(raw - k) > 1e-6) throw new Error('Reported coverage is inconsistent with count');
  return k;
}

export function auditReport(readiness) {
  if (!Array.isArray(readiness?.horizons)) throw new TypeError('Expected horizons array');
  return readiness.horizons.map(row => {
    const phases = row.disjoint?.phases;
    if (!Array.isArray(phases) || !phases.length) throw new TypeError('Missing phases');
    const auditN = row.audit?.n;
    const auditK = countFromRoundedCoverage(auditN, row.coverage);
    const phaseMetrics = phases.map(p => {
      const k = countFromRoundedCoverage(p.n, p.coverage);
      return { offset: p.offset, n: p.n, covered: k, coverage: k / p.n, wilson95: wilson95(k, p.n) };
    });
    if (phaseMetrics.reduce((s,p)=>s+p.n,0) !== auditN ||
        phaseMetrics.reduce((s,p)=>s+p.covered,0) !== auditK) {
      throw new Error('Phase partition disagrees with overall audit');
    }
    if (row.disjoint.candidate.n !== phaseMetrics[0].n) {
      throw new Error('Phase 0 count disagrees with disjoint candidate');
    }
    return {
      horizon: row.horizon, model: row.model,
      overallOverlapping: { n: auditN, covered: auditK, coverage: auditK/auditN },
      phase0: phaseMetrics[0],
      phaseCoverageRange: [Math.min(...phaseMetrics.map(p=>p.coverage)), Math.max(...phaseMetrics.map(p=>p.coverage))],
      phaseMetrics, auditSkillPct: row.skillPct,
      caveat: 'Wilson assumes iid Bernoulli outcomes, NOT established here. Disjoint windows may be dependent; phases overlap each other.'
    };
  });
}

if (process.argv[1] && import.meta.url === new URL('file://' + process.argv[1]).href) {
  if (process.argv.length !== 3) { console.error('Usage: node calibration_uncertainty.mjs readiness.json'); process.exit(2); }
  try { console.log(JSON.stringify(auditReport(JSON.parse(readFileSync(process.argv[2], 'utf8'))),null,2)); }
  catch(e) { console.error(e.message); process.exit(1); }
}