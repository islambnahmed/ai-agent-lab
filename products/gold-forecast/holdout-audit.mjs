/**
 * Disjoint-target-window diagnostic for the gold MVP.
 * Does not assert statistical independence or future predictive skill.
 * Model choice is inherited from the MVP's earlier validation split.
 */
import {forecast, normalize, predict} from "./forecast.mjs";

const average = xs => xs.reduce((a, b) => a + b, 0) / xs.length;

export function auditDisjointHoldout(raw, horizon = 7, minimumWindows = 10) {
  if (!Number.isInteger(minimumWindows) || minimumWindows < 1) {
    throw new Error("minimumWindows must be a positive integer");
  }
  const series = normalize(raw);
  const selected = forecast(series, horizon);
  const prices = series.map(row => row.price);
  const split = Math.floor(series.length * 0.8);
  const windows = [];
  for (let origin = split; origin + horizon <= prices.length; origin += horizon) {
    const training = prices.slice(0, origin);
    const target = origin + horizon - 1;
    const actual = prices[target];
    const baseline = training.at(-1);
    const candidate = predict(training, horizon, selected.model);
    windows.push({
      origin_date: series[origin - 1].date,
      target_date: series[target].date,
      baseline_abs_error: Math.abs(baseline - actual),
      candidate_abs_error: Math.abs(candidate - actual)
    });
  }
  const baselineMae = windows.length ? average(windows.map(x => x.baseline_abs_error)) : null;
  const candidateMae = windows.length ? average(windows.map(x => x.candidate_abs_error)) : null;
  const sufficient = windows.length >= minimumWindows;
  return {
    model: selected.model,
    horizon_sessions: horizon,
    holdout_start: series[split].date,
    overlapping_audit_count: selected.audit.n,
    disjoint_window_count: windows.length,
    minimum_windows: minimumWindows,
    status: sufficient ? "descriptive_disjoint_audit" : "insufficient_disjoint_windows",
    baseline_mae: baselineMae,
    candidate_mae: candidateMae,
    descriptive_better_than_baseline: sufficient ? candidateMae < baselineMae : null,
    windows,
    caveat: "Non-overlapping targets reduce mechanical overlap, but market windows are not statistically independent. No predictive-skill claim."
  };
}
