"""Small executable counterexamples; see audit.py in local reproducible bundle for benchmark."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Version:
    observed: int
    declared: int
    ingested: int
    actual: int  # simulator-only oracle
    revision: int
    value: int


def select(versions, decision=10, policy='declared', skew_bound=2):
    eligible = []
    for v in versions:
        if v.observed > decision:
            continue
        if policy == 'declared':
            accepted = v.declared <= decision
        elif policy == 'ingest':
            accepted = v.declared <= decision and v.ingested <= decision
        elif policy == 'skew_guard':
            accepted = v.declared <= decision and v.ingested + skew_bound <= decision
        elif policy == 'oracle':
            accepted = v.actual <= decision
        else:
            raise ValueError(policy)
        if accepted:
            eligible.append(v)
    return max(eligible, key=lambda v: v.revision) if eligible else None


def verify():
    early = Version(8, 8, 8, 8, 1, 0)
    # A revision first available after decision falsely claims to be early.
    backdated = Version(8, 9, 11, 11, 2, 1)
    assert select([early, backdated], policy='declared').value == 1
    assert select([early, backdated], policy='ingest').value == 0
    # The ingestion clock is two units behind actual time.
    skewed = Version(8, 9, 9, 11, 2, 1)
    assert select([early, skewed], policy='ingest').value == 1
    assert select([early, skewed], policy='skew_guard').value == 0
    # The source was legitimately early, but the archive captured it late.
    archived = Version(8, 8, 12, 8, 2, 1)
    assert select([early, archived], policy='oracle').value == 1
    assert select([early, archived], policy='skew_guard').value == 0
    # A forged capture time defeats even the bounded-skew guard.
    forged = Version(8, 8, 1, 11, 2, 1)
    assert select([early, forged], policy='skew_guard').value == 1
    return 'four verified counterexamples (backdating, skew, recall loss, forged capture)'


if __name__ == '__main__':
    print(verify())
