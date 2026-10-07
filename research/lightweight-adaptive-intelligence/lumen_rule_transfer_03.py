"""Lumen experiment 03: compose unseen transformations from tiny primitives.

The target program is not stored as a named rule.  The learner enumerates
short programs over primitives, keeps only programs consistent with examples,
and predicts only when all survivors agree.
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

def programs(max_depth):
    layer = [()]
    out = [()]
    for _ in range(max_depth):
        layer = [p + (name,) for p in layer for name in PRIMITIVES]
        out.extend(layer)
    return out

class ProgramLearner:
    def __init__(self, max_depth=2):
        self.alive = set(programs(max_depth))

    def observe(self, x, y):
        self.alive = {p for p in self.alive if apply(p, x) == y}

    def predict(self, x):
        outputs = {apply(p, x) for p in self.alive}
        return next(iter(outputs)) if len(outputs) == 1 else None

def run():
    # This composite target is deliberately absent as a named rule.
    target = ("reverse", "swap01")
    examples = [
        (("a","b","c","d"), apply(target, ("a","b","c","d"))),
        ((1,2,3,4,5), apply(target, (1,2,3,4,5))),
    ]

    shallow = ProgramLearner(max_depth=1)
    deep = ProgramLearner(max_depth=2)
    for x, y in examples:
        shallow.observe(x, y)
        deep.observe(x, y)

    # Capacity boundary: no one-step primitive explains the observations.
    assert not shallow.alive
    assert deep.alive

    held_out = [
        (("red","blue","green","gold"), apply(target, ("red","blue","green","gold"))),
        (("α","β","γ","δ","ε"), apply(target, ("α","β","γ","δ","ε"))),
        ((10,20,30,40), apply(target, (10,20,30,40))),
    ]
    assert all(deep.predict(x) == y for x, y in held_out)

    return {
        "primitive_count": len(PRIMITIVES),
        "max_depth": 2,
        "enumerated_programs": len(programs(2)),
        "target_stored_as_named_rule": False,
        "shallow_capacity_failure": True,
        "surviving_programs": len(deep.alive),
        "held_out_transfer": 1.0,
    }

if __name__ == "__main__":
    print(run())
