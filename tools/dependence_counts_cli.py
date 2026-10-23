"""Offline JSON command-line adapter for the experimental exact-count solver.

Usage: python -m tools.dependence_counts_cli input.json
       cat input.json | python -m tools.dependence_counts_cli -
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from .dependence_counts_exact import all_fail_bounds_from_counts

MAX_INPUT_BYTES = 2_000_000
MAX_MODES = 4096
MAX_EDGES = 8192


def _integer(value, label):
    if type(value) is not int:
        raise ValueError(f"{label} must be a JSON integer (not bool or float)")
    return value


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def evaluate_document(doc):
    """Validate an explicit same-population count document and return exact bounds."""
    if not isinstance(doc, dict) or set(doc) != {"total", "marginal_counts", "pairwise_counts"}:
        raise ValueError("document must have exactly total, marginal_counts, pairwise_counts")
    total = _integer(doc["total"], "total")
    marginal = doc["marginal_counts"]
    pairs = doc["pairwise_counts"]
    if not isinstance(marginal, list) or not 1 <= len(marginal) <= MAX_MODES:
        raise ValueError(f"marginal_counts must be a list of 1..{MAX_MODES} counts")
    if not isinstance(pairs, list) or len(pairs) > MAX_EDGES:
        raise ValueError(f"pairwise_counts must be a list of at most {MAX_EDGES} entries")
    marginal = [_integer(v, f"marginal_counts[{i}]") for i, v in enumerate(marginal)]
    edges = {}
    for index, row in enumerate(pairs):
        if not isinstance(row, dict) or set(row) != {"i", "j", "count"}:
            raise ValueError(f"pairwise_counts[{index}] must have exactly i, j, count")
        i = _integer(row["i"], f"pairwise_counts[{index}].i")
        j = _integer(row["j"], f"pairwise_counts[{index}].j")
        count = _integer(row["count"], f"pairwise_counts[{index}].count")
        if not 0 <= i < j < len(marginal):
            raise ValueError(f"pairwise_counts[{index}] requires 0 <= i < j < number of modes")
        if (i, j) in edges:
            raise ValueError(f"duplicate pairwise constraint ({i},{j})")
        edges[i, j] = count
    lo, hi = all_fail_bounds_from_counts(total, marginal, edges)
    return {
        "all_fail": {"lower": str(lo), "upper": str(hi)},
        "any_survives": {"lower": str(1 - hi), "upper": str(1 - lo)},
        "mode_count": len(marginal),
        "pairwise_constraint_count": len(edges),
        "total": total,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON file path, or - for standard input")
    args = parser.parse_args(argv)
    try:
        if args.input == "-":
            data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        else:
            with Path(args.input).open("rb") as f:
                data = f.read(MAX_INPUT_BYTES + 1)
        if len(data) > MAX_INPUT_BYTES:
            raise ValueError(f"JSON input exceeds {MAX_INPUT_BYTES} bytes")
        document = json.loads(data.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
        result = evaluate_document(document)
        result["input_sha256"] = hashlib.sha256(data).hexdigest()
    except (OSError, UnicodeError, ValueError, TypeError, NotImplementedError, RecursionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
