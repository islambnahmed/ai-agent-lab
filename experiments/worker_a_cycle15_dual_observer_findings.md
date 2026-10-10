# Worker A cycle 15 — two HTTP observers, conflict detection

Date: 2026-10-10. Scope: synthetic loopback HTTP fixture (127.0.0.1) only.

## Experiment
Built a second bounded HEAD-only collector using Python urllib (proxies and redirects disabled), compared it with the existing http.client collector and anchored ledger. Both share the same snapshot parser and server; this is transport diversity, NOT independent origin evidence.

## Verified results
Ran 54/54 Python unittest tests successfully (11 new, 43 previous). On a seven-target local fixture: 5 concordant statuses, 1 conflicting status, 1 unresolved status. An alternating endpoint returned HTTP 404 to A and HTTP 200 to B, correctly flagged as conflict; HTTP 405 remained unresolved. HTTP 302 was observed without following its external Location. Tests rejected external origins, budget overflow, ledger tampering, and incorrect independently retained SHA-256 anchors. No GET requests occurred.

## Counterexample and limits
A synthetic endpoint deliberately labeled as logically missing returned HTTP 200 to BOTH clients; both agreed but were wrong about the intended resource state. Thus agreement between two clients contacting the same server does not prove truth, source independence, or SEO correctness. Observations are time-sensitive, HEAD does not validate GET content, and SHA-256 is not authentication without a separately retained root.

## Reproduction
The full code, 54-test transcript, and prior dependencies are packaged in the conversation artifact `worker_a_cycle15_dual_observer_bundle.zip`, SHA-256 `e810e516bc731b656373fa6f09738e231a826f78db80b4f07e05250267ad0cf3`. This GitHub report does not by itself make the code reproducible from the repo.

## Next experiment
Bounded loopback-only HEAD/GET content corroboration with adversarial soft-404 and time-varying response fixtures. Do not turn concordance into unearned confidence.
