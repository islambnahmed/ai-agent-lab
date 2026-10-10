"""Audit fresh-origin forecast evidence separately from raw coverage.
Passing this sample-size gate does not demonstrate predictive skill.
"""
import statistics
from tools.gold_point_in_time import evaluate


def audit(rows, horizon=7, train_min=120, stride=None):
    report = evaluate(rows, horizon=horizon, train_min=train_min, stride=stride)
    predictions = report['results']
    fresh = [r for r in predictions if r['last_observed_date'] == r['origin_date']]
    attempted = len(predictions) + report['skipped']
    base_mae = statistics.mean(r['baseline_abs_error'] for r in fresh) if fresh else None
    model_mae = statistics.mean(r['candidate_abs_error'] for r in fresh) if fresh else None
    report.update({
        'fresh_origin_windows': len(fresh),
        'fresh_origin_coverage_pct': 100 * len(fresh) / attempted if attempted else 0.0,
        'fresh_baseline_mae': base_mae,
        'fresh_candidate_mae': model_mae,
        'fresh_improvement_pct': 100 * (base_mae - model_mae) / base_mae if base_mae else None,
        'quality_status': 'ready_for_holdout' if len(fresh) >= 20 else 'insufficient_fresh_windows',
        'quality_warning': 'Raw MAE includes stale-origin windows. Fresh metrics are descriptive, not validated trading performance. Verify timestamps and use an untouched holdout.',
    })
    if len(fresh) != len(predictions) and report['status'] == 'evaluation_ready':
        report['status'] = 'descriptive_only'
    return report
