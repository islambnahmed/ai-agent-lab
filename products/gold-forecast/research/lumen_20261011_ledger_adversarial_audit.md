# Lumen — prospective ledger adversarial audit (2026-10-11)

Scope: gold-forecast research; offline synthetic inputs, not a market-data performance claim.

Reproduced two defects in the prior local ledger_v2 prototype:
1. Horizon values like `constructor`, `toString`, `__proto__` match the accepted identifier regex but `groups={}` collides with inherited Object properties. A valid forecast/outcome pair with horizon `constructor` crashed at `groups[row.horizon].push is not a function`.
2. `JSON.parse` silently keeps the last value for duplicate keys, e.g. `{"point":999,"point":100}`. Such ambiguous audit records are unsuitable for an integrity ledger.

Fix verified locally: use Map for horizon aggregation; scan valid JSONL input for duplicate object keys at all nesting levels before accepting events; expose per-model/per-horizon metrics so models are not conflated.

Evidence: 21/21 Node.js tests passed (14 previous + 7 new), including prototype-collision, nested duplicate-key, escaped key, model partition, and ordinary contract cases. Tests used synthetic values only.

Limitations: neither this experiment nor a local append-only JSONL log proves independent timestamps or source-price authenticity. No claim of real gold forecasting skill. This note is a checkpoint, not evidence of deployed code.

Next: port the patched module and tests into this branch, run CI, and establish externally verified source timestamps before any prospective accuracy claim.
