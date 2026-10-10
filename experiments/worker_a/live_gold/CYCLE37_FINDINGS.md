# Worker A cycle 37 — capture delay counterexample

2026-10-11 UTC. Synthetic-only evidence.

Earlier walk-forward evaluation accepted a provider-timestamped target captured hours late. Controlled seven-observation fixture: prior implementation scored 3 forecasts and accepted a target captured 2 hours late; revised implementation scored 2 and reported `targetCaptureLate: 1`.

The fix adds `maxTargetCaptureDelayMs` (default 300000) independent of `targetToleranceMs`, reports separate provider and capture lag, and does not select a replacement observation when earliest provider target was captured too late. 125 local tests passed, including 8 new adversarial cases. The tests are not evidence of CI success.

Capture timestamps are untrusted claims. No real XAU/USD validation, independent time anchor, or prospective registration occurred. Next: freeze protocol, independently witness pre-target records, and collect authorized real quotes.
