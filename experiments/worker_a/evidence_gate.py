#!/usr/bin/env python3
"""Conservative, source-aware gold forecast evidence audit (no price download).

Usage: python evidence_gate.py report1.json [report2.json ...]
       python evidence_gate.py --test

A descriptive diagnostic, not a proof of calibration or predictive skill.
"""
import argparse
import json
import math
import sys
import unittest

NOMINAL = 0.80
MIN_DISJOINT = 30  # policy threshold, not a statistical theorem


def wilson(successes, n, z=1.959963984540054):
    if not isinstance(n, int) or n <= 0 or not 0 <= successes <= n:
        raise ValueError('invalid binomial counts')
    p = successes / n
    d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    r = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return [round(c-r, 4), round(c+r, 4)]


def counts(coverage_pct, n):
    if not isinstance(n, int) or n <= 0 or not isinstance(coverage_pct, (int,float)) or not math.isfinite(coverage_pct) or not 0 <= coverage_pct <= 100:
        raise ValueError('invalid coverage')
    estimated = n * coverage_pct / 100
    k = round(estimated)
    if abs(estimated-k) > 1e-5:
        raise ValueError('coverage not consistent with integer outcomes')
    return k


def audit(report):
    if not isinstance(report, dict) or not isinstance(report.get('source'), str) or not report['source'].strip():
        raise ValueError('source provenance required')
    entries = report.get('priceBenchmarks', report.get('horizons'))
    if not isinstance(entries, list) or not entries:
        raise ValueError('missing horizon evaluations')
    result = {'source': report['source'], 'measurement': report.get('measurement'),
              'audit_origin': report.get('runAt'), 'evidence_type': 'retrospective',
              'horizons': [], 'automatic_promotion_allowed': False}
    for row in entries:
        h = row['horizon']
        if h not in (1,7,30):
            raise ValueError('unsupported horizon')
        n = row['audit']['n']
        k = counts(row['coverage'], n)
        phases = row['disjoint']['phases']
        if len(phases) != h or any(p['offset'] != i for i,p in enumerate(phases)):
            raise ValueError('invalid phase partition')
        if sum(p['n'] for p in phases) != n:
            raise ValueError('phase counts do not partition audit')
        for p in phases:
            counts(p['coverage'], p['n'])
        disjoint_n = row['disjoint']['candidate']['n']
        if disjoint_n != phases[0]['n']:
            raise ValueError('disjoint count does not match first phase')
        flags = []
        if disjoint_n < MIN_DISJOINT:
            flags.append('few_nonoverlapping_windows')
        if row['coverage'] / 100 < NOMINAL:
            flags.append('descriptive_undercoverage')
        if h == 1:
            ci = wilson(k,n)
            if ci[1] < NOMINAL:
                flags.append('undercoverage_even_under_iid_binomial_assumption')
        else:
            ci = None  # Overlapping horizons: ordinary binomial CI is invalid.
        result['horizons'].append({
            'horizon':h, 'model':row.get('model'), 'n_overlapping':n,
            'covered':k, 'coverage_pct':round(row['coverage'],2),
            'nonoverlapping_first_phase_n':disjoint_n,
            'phase_coverage_range_pct':[round(min(p['coverage'] for p in phases),2),round(max(p['coverage'] for p in phases),2)],
            'iid_wilson95_h1_only':ci, 'flags':flags,
            'model_mae':row['audit']['mae'], 'baseline_mae':row['baseline']['mae'],
            'skill_pct':row.get('skillPct')})
    return result


def compare(a,b):
    # Even identical names can refer to different measurements or time windows.
    if a['source'] != b['source'] or a['measurement'] != b['measurement']:
        return {'status':'not_comparable','reason':'different price source or measurement'}
    if a['audit_origin'] != b['audit_origin']:
        return {'status':'not_comparable','reason':'different report run; audit window not proven identical'}
    return {'status':'same_report_provenance_only',
            'reason':'identical origin is not proof of identical price rows or evaluation design'}


def main(paths):
    reports = []
    for path in paths:
        with open(path, encoding='utf-8') as f:
            reports.append(audit(json.load(f)))
    return {'nominal_coverage':NOMINAL,'min_disjoint_policy':MIN_DISJOINT,
            'reports':reports,
            'pairwise':[{'left':i,'right':j,**compare(reports[i],reports[j])}
                        for i in range(len(reports)) for j in range(i+1,len(reports))],
            'caveat':'Retrospective, inspected periods; overlapping targets and serial dependence preclude naive binomial confidence intervals. h1 Wilson is illustrative under an iid assumption only. No prospective skill claim.'}


class TestEvidenceGate(unittest.TestCase):
    def fixture(self,h=1,n=50,k=40):
        phases=[{'offset':i,'n':len(list(range(i,n,h))),
                 'coverage':100*sum(j<k for j in range(i,n,h))/len(list(range(i,n,h)))}
                for i in range(h)]
        row={'horizon':h,'model':'persistence','coverage':100*k/n,
             'audit':{'n':n,'mae':10},'baseline':{'mae':10},
             'disjoint':{'candidate':{'n':phases[0]['n']},'phases':phases}}
        return {'source':'S','runAt':'2026-10-12T00:00:00Z','horizons':[row]}
    def test_wilson(self):
        self.assertEqual(wilson(0,10)[0],0)
        self.assertLess(wilson(0,10)[1],0.3)
    def test_coverage_count(self):
        self.assertEqual(counts(64.8062015503876,645),418)
    def test_reject_noninteger_coverage(self):
        with self.assertRaises(ValueError): counts(50.1,10)
    def test_reject_missing_provenance(self):
        with self.assertRaises(ValueError): audit({'horizons':[]})
    def test_short_disjoint(self):
        self.assertIn('few_nonoverlapping_windows',audit(self.fixture(30,60,45))['horizons'][0]['flags'])
    def test_no_ci_for_overlaps(self):
        self.assertIsNone(audit(self.fixture(7,70,56))['horizons'][0]['iid_wilson95_h1_only'])
    def test_reject_bad_phase_partition(self):
        x=self.fixture(7,70,56);x['horizons'][0]['disjoint']['phases'][0]['n']=99
        with self.assertRaises(ValueError): audit(x)
    def test_cross_source_no_comparison(self):
        a=audit(self.fixture());b=audit(self.fixture());b['source']='Other'
        self.assertEqual(compare(a,b)['status'],'not_comparable')
    def test_no_promotion_from_retro(self):
        self.assertFalse(audit(self.fixture())['automatic_promotion_allowed'])
    def test_h1_undercovers(self):
        r=audit(self.fixture(1,645,418))['horizons'][0]
        self.assertIn('undercoverage_even_under_iid_binomial_assumption',r['flags'])


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('reports',nargs='*');p.add_argument('--test',action='store_true');args=p.parse_args()
    if args.test:
        unittest.main(argv=[sys.argv[0]])
    else:
        if not args.reports:p.error('supply at least one JSON report')
        print(json.dumps(main(args.reports),indent=2,ensure_ascii=False))
