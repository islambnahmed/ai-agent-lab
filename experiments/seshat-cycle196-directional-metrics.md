# Seshat cycle 196 — directional metric integration attempt

2026-10-16. The existing gold forecast metrics report directionAccuracy as the fraction of exact sign matches. Persistence predicts zero change, so this metric is not comparable to directional models.

Proposed backward-compatible addition: directional.calls, directional.abstentions, directional.hits, directional.flatActual, directional.callRatePct, and directional.hitRateWhenCalledPct (null when no calls). Keep the old metric for consumers, clearly marked legacy.

Four local isolated tests passed. Full project tests were not run. Production update was blocked by safety checks and is not applied. Do not claim model improvement or real-world predictive skill.
