"""Lumen experiment 05: adaptive probes prevent false behavioral equivalence.

Behavior-deduplication is only sound relative to its probes. This witness shows
two distinct programs that collide on fixed length-5/6 probes but diverge at
length 3, then chooses a distinguishing probe from a tiny candidate pool.
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

def signature(program, probes):
    return tuple(apply(program, x) for x in probes)

def choose_distinguishing_probe(programs, candidate_probes):
    """Choose the probe producing the most distinct behavior partitions."""
    scored = []
    for probe in candidate_probes:
        partitions = len({apply(p, probe) for p in programs})
        scored.append((partitions, -len(probe), probe))
    best = max(scored)
    return best[2], best[0]

def run():
    # Concrete collision discovered by search over compositions up to depth 4.
    target = ("reverse", "swap01", "reverse", "swap01")
    rival = ("swap01", "reverse", "swap01", "reverse")
    programs = (target, rival)

    fixed = (
        tuple(range(5)),
        tuple(range(6)),
    )
    assert signature(target, fixed) == signature(rival, fixed)

    held = tuple(range(3))
    assert apply(target, held) != apply(rival, held)

    # Fixed-probe deduplication would collapse these two programs and can keep
    # the wrong representative solely because of deterministic tie-breaking.
    fixed_representative = min(programs)
    fixed_generalizes = apply(fixed_representative, held) == apply(target, held)
    assert not fixed_generalizes

    candidates = tuple(tuple(range(n)) for n in range(2, 8))
    probe, partitions = choose_distinguishing_probe(programs, candidates)
    assert partitions == 2
    assert apply(target, probe) != apply(rival, probe)

    augmented = fixed + (probe,)
    assert signature(target, augmented) != signature(rival, augmented)

    return {
        "fixed_probe_lengths": [len(x) for x in fixed],
        "false_equivalence": True,
        "fixed_representative_generalizes": fixed_generalizes,
        "adaptive_probe_length": len(probe),
        "adaptive_partitions": partitions,
        "ambiguity_removed": True,
        "lesson": "behavioral compression needs probes chosen to separate surviving hypotheses; fixed probes can create false certainty",
    }

if __name__ == "__main__":
    print(run())
