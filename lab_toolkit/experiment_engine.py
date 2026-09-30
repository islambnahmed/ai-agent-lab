"""Optional experiment runner for AI Agent Lab.

No agent is required to use this. It standardizes evidence capture without choosing goals.
"""
from __future__ import annotations
import argparse, hashlib, json, random, statistics
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

@dataclass
class TrialSummary:
    experiment: str
    seed: int
    trials: int
    mean: float
    stdev: float
    minimum: float
    maximum: float
    digest: str
    created_utc: str

def run_trials(name: str, fn: Callable[[random.Random, int], float], trials: int, seed: int) -> TrialSummary:
    if trials < 1:
        raise ValueError("trials must be >= 1")
    rng = random.Random(seed)
    values = [float(fn(rng, i)) for i in range(trials)]
    payload = json.dumps(values, separators=(",", ":")).encode()
    return TrialSummary(
        experiment=name, seed=seed, trials=trials,
        mean=statistics.fmean(values),
        stdev=statistics.pstdev(values),
        minimum=min(values), maximum=max(values),
        digest=hashlib.sha256(payload).hexdigest(),
        created_utc=datetime.now(timezone.utc).isoformat(),
    )

def smoke_trial(rng: random.Random, _: int) -> float:
    return 1.0 if rng.random() < 0.5 else 0.0

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--trials", type=int, default=10000)
    p.add_argument("--seed", type=int, default=20260930)
    p.add_argument("--out")
    a=p.parse_args()
    if not a.smoke:
        raise SystemExit("Library mode: import run_trials(), or use --smoke.")
    result=run_trials("toolkit-smoke", smoke_trial, a.trials, a.seed)
    text=json.dumps(asdict(result), indent=2)
    if a.out:
        Path(a.out).write_text(text+"\n", encoding="utf-8")
    print(text)

if __name__ == "__main__":
    main()
