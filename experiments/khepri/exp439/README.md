# Khepri exp439 — semantic-boundary authorization

**2026-10-25 | local, synthetic, Python standard library | no remote side effects**

## Research question

Exp438 binds a single-use permit to the *request object*. What happens if the component checking a request and the component executing it disagree about how to interpret its bytes? Can two parsers interpret the same JSON differently, or can a downstream path decoder turn an apparently in-scope string into a different path?

**Answer (in deliberately constructed local adapters): yes.** A first-key-wins JSON checker interprets `{"kind":"paragraph","kind":"command","text":"hello"}` differently from a last-key-wins parser. A lexical path-prefix checker accepts `experiments/khepri/%2e%2e/%2e%2e/outside.md`, while a synthetic percent-decoding/normalizing executor interprets it outside that prefix. **Neither case claims that the real Notion or GitHub API behaves this way.** The previous exp438 gate did not enforce a content schema; it intentionally documents that limitation. Directly replaying the exp438 code from its prior local ZIP confirmed it permits the duplicate-key Notion payload (issue and simulated execute both returned success). This is a concrete demonstration of its documented limitation, not a new break of its advertised guarantees.

## New capability

`semantic_boundary.py` is a conservative, **toy** execution-boundary contract:

1. A trusted, versioned adapter prepares the exact target, method, path and wire-body bytes.
2. JSON is parsed with duplicate-key rejection (including nested objects), finite-number checking, bounded input and an explicit sample schema. Equivalent JSON key order yields the same canonical wire bytes.
3. Repository paths are rejected if ambiguous (percent-encoded paths, dot segments, backslashes, repeated separators, non-NFC Unicode); target/branch are checked against a narrow illustrative allowlist.
4. A single-use permit binds the **prepared** action, including adapter revision, and is checked atomically immediately before a simulated effect. Adapter-version drift, payload substitution and replay are rejected.

The actual authorized lab is broader than this illustrative write policy. This prototype does not establish real descendant authorization, protect against a malicious trusted adapter, validate arbitrary content semantics, or solve the crash window between permit consumption and an external effect.

## Reproduce

```sh
python -m unittest -v test_semantic_boundary.py
python benchmark.py
```

## Verified evidence

- **20/20 unit tests passed**, including nested duplicate keys, parser disagreement, canonical JSON equivalence, invalid Unicode, excessive input, path aliases, adapter drift, expiry, payload swap, replay and 50 concurrent replay attempts.
- **12,000 deterministic synthetic benchmark cases:** 2,000 legitimate GitHub requests accepted; 2,000 legitimate Notion requests accepted; 2,000 ambiguous duplicate-key payloads rejected; 2,000 percent-encoded path aliases rejected; 2,000 payload substitutions rejected; 2,000 adapter-version drifts rejected. All 2,000 intentionally constructed JSON examples made the two toy parsers disagree, and all 2,000 toy path examples escaped the sample prefix *after synthetic decoding*. The numbers are scenario counts, **not empirical detection rates**.
- **6,000 local simulated effects**, including legitimate executions following rejected substitutions. No real tool write was performed by the benchmark.

## Counterexamples / costs

- The strict path rule rejects a decomposed Unicode filename even if a real service would accept it; fail-closed behavior can cost legitimate operations. Real adapters should specify the actual platform contract rather than copying this rule blindly.
- An adapter with a compromised implementation can prepare one representation and execute another; a digest alone cannot defend against that. The adapter and executor must share a trusted contract and transport implementation.
- The simulated executor consumes a permit before appending a local effect; **it still does not guarantee exactly-once remote delivery after a crash** (see exp429/438). Combine with a durable outbox and destination idempotency or outcome reconciliation.

## Transferable lesson

Binding approval to raw request fields is necessary but not sufficient when downstream parsers, serializers or API adapters can reinterpret the request. Authorize the **same prepared semantic/wire action that the executor will send**, reject ambiguous encodings, version the adapter contract, and explicitly test parser disagreement and adapter drift. For production, measure against real platform behavior and enforce trusted adapter isolation.
