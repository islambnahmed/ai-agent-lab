# Khepri experiment 418 — Approval receipt equality-spoofing cross-review

**Date:** 2026-10-24. **Authorized scope:** `islambnahmed/ai-agent-lab`; no external actions by the prototype. **Status:** verified local counterexample and narrow prototype mitigation; not production security.

## Question

Experiment 417 described its approvals as *opaque in-memory object identities* and reported that forged receipts were rejected. Does its use of Python `dict.pop(receipt)` actually enforce **identity**, or merely dictionary key **hash/equality** semantics?

## Evidence and reproducibility

- Inspected `experiments/khepri/exp417/approval_receipts.py` on branch `khepri/exp417-approval-receipts-20261024` using the GitHub connector. The local reproduction is **byte-for-byte identical** to the original Git blob SHA `a82acd6be64ceaa574fc4d723c7b90a95a3dd475` (4,127 bytes), verified by computing the Git blob hash. The original source is *not* duplicated in this experiment's committed files; it is already present in the branch's parent.
- `Executor.simulate` calls `self._state.pending.pop(receipt, None)` before checking receipt type. A forged object with a matching `__hash__` and an `__eq__` returning `True` is treated as the original `object()` dictionary key, even though `fake is not receipt`. It is then accepted if the approved plan and payload match.
- The forged object does **not** hold the original receipt; this constructed attack assumes the attacker learns the receipt's hash. This is a **conditional counterexample**, not a demonstration of a practical external exploit without an information leak.
- An unhashable list triggers `TypeError` on the original nonempty registry, and custom hash/equality methods can raise exceptions. This is a robustness failure even without a hash leak.
- `identity_receipts.py` adds `StrictExecutor`, which rejects anything whose `type(receipt) is not object` *before* dictionary lookup. This is valid for exp417's issuer because it creates only `object()` receipts. It rejects crafted keys without invoking their hash/equality methods. The exact-type check is deliberately narrow and would need revalidation if receipt type changes.

## Reproduce

From this directory, with Python 3.10+ standard library and the exp417 sibling directory present:

```bash
python -m unittest -v test_identity_receipts.py
python benchmark.py
```

**Observed local result:** 12/12 unit tests passed. In 10,000 synthetic attempts (5,000 original + 5,000 strict; half GitHub-issue-like payloads, half SEO-HTML-like payloads):

| Condition | Original exp417 | Strict adapter |
|---|---:|---:|
| Forged receipt accepted (given matching hash) | 5,000 / 5,000 | 0 / 5,000 |
| Legitimate receipt still accepted after forged attempt | 0 / 5,000 | 5,000 / 5,000 |

The benchmark's `elapsed_seconds_observed` is a single local measurement, not a reliable performance comparison. Cases intentionally exercise the vulnerable behavior and do not estimate prevalence in real systems.

## Corrections to exp417

Exp417's conclusion about arbitrary **forged Python objects** is too broad: its checks demonstrate that random strings and copied plain `object()` instances fail, but a custom equality/hash object can impersonate an existing dictionary key given its hash. The original experiment's core conclusion about post-approval payload binding still holds for its narrower tested inputs. This review **does not** show that an attacker can discover an unpredictable receipt hash or execute arbitrary Python code across a proper trust boundary.

## Limits and production direction

1. The adapter still shares an in-process `_state` and is **not** an access-control boundary against arbitrary code execution, reflection, compromised issuer, leaked genuine receipt, or attacker control of issuance.
2. It retains the intentional availability issue: possession of a genuine receipt allows it to be consumed with the wrong payload.
3. It does not address concurrency, process crashes, replay after restart, remote authentication, or prompt injection.
4. A production system should use process isolation, authenticated issuance, unpredictable server-side identifiers, strict serialization/schema checks before lookup, atomic single-use redemption, and tool-side authorization. These are recommendations, not implemented or tested here.

## Transferable lesson

**A value described as an identity token must be compared by identity, not by extensible equality/hash behavior on untrusted objects.** Place type and shape checks *before* touching a hash table keyed by authority-bearing objects. Cross-reviewing an earlier artifact produced a concrete falsification instead of a new untested design.
