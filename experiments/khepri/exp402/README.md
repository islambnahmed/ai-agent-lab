# Khepri exp402 — Cross-runtime intent payload hashing (restricted JSON profile)

## Question and motivation
Exp401 found that Python `json.dumps({"v":1.0})` and JavaScript `JSON.stringify({v:1.0})` yield different bytes (`1.0` vs `1`). An idempotency destination that compares payload digests may reject a valid retry across runtimes or, with unsafe numeric parsing, conflate distinct inputs. Can a deliberately restricted, explicit payload profile yield matching hashes without implementing all of RFC 8785/JCS?

## Prototype
`canonical.py` and `canonical.mjs` implement the same strict profile: only null, boolean, Unicode strings, arrays, and objects with ASCII letter-leading keys. Object keys are sorted. **All JSON numbers are prohibited**, including integers: exact amounts and counts must be supplied as strings. Values are serialized as UTF-8 JSON with no whitespace. Unpaired surrogates, invalid keys, >24 levels, >10,000 nodes, and >1 MiB are rejected. Gold receipt and SEO publication constructors demonstrate exact decimal-string normalization. Unicode content is **not normalized**; visually similar NFC/NFD strings remain distinct intents.

## Evidence
Python 3.13.5 and Node 22.16.0, deterministic random seed 402. `python3 -m unittest -v test_canonical.py`: **16/16 passed**. `python3 benchmark.py`: **1,823 paired Python/Node cases, 1,723 accepted and 100 rejected, zero cross-runtime accept/reject or digest mismatches**. Cases include Arabic, emoji, combining characters, CJK, control characters, different object insertion orders, very large decimal strings, invalid decimals, floats, unsafe keys, and malformed Unicode. Gold and SEO cases are both included. The naive `{v:1.0}` counterexample is reproduced. All inputs are local and synthetic.

## Important counterexample / remaining risk
**Duplicate raw JSON object keys are silently collapsed before canonicalization** by ordinary JSON parsers. `{"Id":"first","Id":"second"}` is indistinguishable from `{"Id":"second"}` after parsing. This profile therefore cannot prove integrity of untrusted raw JSON; ingress must reject duplicate keys before object construction, or accept only a trusted structured producer. Also, the decimal constructors do not implement business-level validation (e.g. sign, permissible scale, URL/currency constraints). Unicode normalization policy is intentionally strict, so two visually identical strings may be different payloads. This is **not** a full RFC 8785 implementation and is not proven equivalent to third-party canonicalizers.

## Reproduce
Run from this directory with Python 3.10+ and Node 22+ (standard libraries only):

```sh
python3 -m unittest -v test_canonical.py
python3 benchmark.py
```

## Deployment decision
Research prototype only. Do not replace an existing ledger or activate production idempotency without schema migration, duplicate-key-rejecting ingestion, language/runtime conformance tests, domain validators, and an atomic downstream idempotency guarantee (exp401). No external side effects; `main` remains unchanged.
