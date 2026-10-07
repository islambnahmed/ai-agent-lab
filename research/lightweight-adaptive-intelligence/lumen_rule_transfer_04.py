"""Lumen experiment 04: expose combinatorial search cost and test beam compression.

Experiment 03 showed composition, but exhaustive enumeration grows exponentially.
This witness measures that failure mode and compares exact enumeration with a
small behavior-deduplicating beam. The beam keeps one shortest representative
per observed behavior on probe inputs, then caps survivors deterministically.
"""

PRIMITIVES = {
    "reverse": lambda x: x[::-1],
    "rotl1": lambda x: x[1:] + x[:1],
    "swap01": lambda x: x[1:2] + x[:1] + x[2:],
}

def apply(program, x):
    for name in program:
        x = PRIMITIVES[name](x)
    return x

def exhaustive_count(depth):
    # Includes empty program.
    n = len(PRIMITIVES)
    return sum(n ** d for d in range(depth + 1))

def dedup_beam(max_depth, probes, width=16):
    beam = [()]
    all_reps = {tuple(probes): ()}
    for _ in range(max_depth):
        candidates = [p + (name,) for p in beam for name in PRIMITIVES]
        by_behavior = {}
        for p in candidates:
            signature = tuple(apply(p, x) for x in probes)
            old = by_behavior.get(signature)
            if old is None or (len(p), p) < (len(old), old):
                by_behavior[signature] = p
        # Shorter/lexicographic ordering makes the cap reproducible.
        beam = sorted(by_behavior.values(), key=lambda p: (len(p), p))[:width]
        for p in beam:
            all_reps[tuple(apply(p, x) for x in probes)] = p
    return set(all_reps.values())

def consistent(programs, examples):
    return {p for p in programs if all(apply(p, x) == y for x, y in examples)}

def run():
    probes = (
        ("a","b","c","d","e"),
        (0,1,2,3,4,5),
    )
    target = ("reverse", "swap01", "rotl1")
    examples = [(x, apply(target, x)) for x in probes]

    # Exact search cost is exponential even before evaluating examples.
    counts = {d: exhaustive_count(d) for d in range(1, 9)}
    assert counts[8] == 9841

    exact = []
    layer = [()]
    exact.extend(layer)
    for _ in range(3):
        layer = [p + (name,) for p in layer for name in PRIMITIVES]
        exact.extend(layer)
    exact_alive = consistent(exact, examples)
    assert exact_alive

    beam = dedup_beam(3, probes, width=16)
    beam_alive = consistent(beam, examples)

    # The compressed search is intentionally lossy: report whether it preserves
    # a valid explanation rather than assuming it must.
    preserved = bool(beam_alive)
    transfer = None
    if preserved:
        held = ("red","blue","green","gold","white")
        expected = apply(target, held)
        outputs = {apply(p, held) for p in beam_alive}
        transfer = len(outputs) == 1 and expected in outputs

    return {
        "exact_candidates_depth8": counts[8],
        "exact_candidates_depth3": exhaustive_count(3),
        "beam_representatives_depth3": len(beam),
        "beam_width": 16,
        "valid_explanation_preserved": preserved,
        "held_out_consensus_transfer": transfer,
        "lesson": "composition is cheap in memory only if search is controlled; beam compression trades completeness for compute",
    }

if __name__ == "__main__":
    print(run())
