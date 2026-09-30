"""Template for promoting a verified experiment into a reusable capability.

Copy this only when an experiment produced behavior worth reusing.
Delete sections that do not apply. Keep the public API small.
"""
from __future__ import annotations

__capability__ = {
    "name": "replace-me",
    "origin": "experiment-or-evidence-path",
    "status": "candidate",
    "verified_on": [],
    "known_limits": [],
}

def run(value):
    """Small stable entry point. Replace with the actual reusable behavior."""
    raise NotImplementedError("Implement only after evidence justifies promotion.")
