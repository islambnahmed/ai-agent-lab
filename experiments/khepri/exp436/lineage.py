"""Offline bitemporal join and dependency-closure guard (no network, stdlib only)."""
from dataclasses import dataclass
from typing import Dict, Tuple


class ProvenanceError(ValueError):
    pass


@dataclass(frozen=True)
class Artifact:
    name: str
    captured_at: int  # independently recorded first access, NOT publisher-declared
    parents: Tuple[str, ...] = ()
    effective_at: int = 0  # event/business time; not evidence of access


@dataclass(frozen=True)
class Revision:
    revision_id: str
    effective_at: int
    captured_at: int
    priority: int
    selected_alias: str


def choose_revision(revisions, decision: int, *, enforce_capture: bool):
    """Choose latest *valid* mapping as known by decision time; fail closed if absent.

    effective_at determines business validity; captured_at determines
    historical knowledge. priority is a tie breaker, not a time oracle.
    """
    eligible = [r for r in revisions if r.effective_at <= decision and
                (not enforce_capture or r.captured_at <= decision)]
    if not eligible:
        return None
    return max(eligible, key=lambda r: (r.effective_at, r.priority, r.revision_id))


def lineage_ready(nodes: Dict[str, Artifact], target: str, decision: int):
    """Return (is_ready, max_readiness_time) for the complete provenance DAG.

    Raises on missing nodes, cycles, or impossible negative timestamps.
    Does NOT authenticate captured_at, nor assert the recorded DAG is complete.
    """
    visiting, done = set(), {}

    def visit(name):
        if name in done:
            return done[name]
        if name in visiting:
            raise ProvenanceError('cycle: ' + name)
        if name not in nodes:
            raise ProvenanceError('missing parent: ' + name)
        node = nodes[name]
        if node.captured_at < 0 or node.effective_at < 0:
            raise ProvenanceError('negative timestamp: ' + name)
        visiting.add(name)
        readiness = max(node.captured_at, node.effective_at)
        for parent in node.parents:
            readiness = max(readiness, visit(parent))
        visiting.remove(name)
        done[name] = readiness
        return readiness

    cutoff = visit(target)
    return cutoff <= decision, cutoff


def guarded_join(revisions, artifacts, decision):
    """Select mapping and validate its entire dependency closure.

    An alias's raw row may be early while its mapping was only captured later.
    """
    candidates = [r for r in revisions if r.effective_at <= decision and r.captured_at <= decision]
    candidates.sort(key=lambda r: (r.effective_at, r.priority, r.revision_id), reverse=True)
    for revision in candidates:
        ready, _ = lineage_ready(artifacts, 'join_' + revision.revision_id, decision)
        if ready:
            return revision.selected_alias
    return None
