"""Independent holdout mutation audit; offline only, no network or file mutations.

Holdout mutations are distinct from the 22 mutants in C327. Evaluates the
unchanged parser against the C326 and C327 tests without training on survivors.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'research' / 'worker_a' / 'c327'))
from run_mutation_benchmark import (SOURCE, CORPUS, TARGETED, module_for,
                                    run_case_suite, run_oracle_suite)
from robots_gate import decide as baseline_decide

# One-at-a-time, manually specified source perturbations; no equivalent mutants
# knowingly included. No C327 mutation needles/replacements are reused.
HOLDOUT = {
    'byte_limit_boundary_inclusive': (
        "len(robots.encode('utf-8')) > MAX_BYTES", "len(robots.encode('utf-8')) >= MAX_BYTES"),
    'target_length_boundary_inclusive': (
        "len(target) > 8192", "len(target) >= 8192"),
    'url_fragment_rejected_only_for_paths': (
        "or '#' in target", "or False"),
    'multi_agent_group_only_first': (
        "agents.append(value.lower())", "agents.append(value.lower()) if not agents else None"),
    'specific_agent_requires_prefix': (
        "if any(a != '*' and a in token for a in agents)]", "if any(a != '*' and token.startswith(a) for a in agents)]"),
    'raw_unicode_not_encoded': (
        "out.extend(f'%{b:02X}' for b in c.encode('utf-8'))", "out.append(c)"),
    'comment_text_not_stripped': (
        "raw.split('#', 1)[0].strip()", "raw.strip()"),
    'colon_in_rule_value_misparsed': (
        "line.split(':', 1)", "line.rsplit(':', 1)"),
    'shortest_specific_agent': (
        "max(len(a) for agents, _ in specific", "min(len(a) for agents, _ in specific"),
    'query_ampersand_truncation': (
        "target += '?' + parsed.query", "target += '?' + parsed.query.split('&')[0]"),
    'http_urls_rejected': (
        "('http', 'https')", "('https',)"),
    'trailing_slash_stripped': (
        "_canonical(target, uri_target=True)", "_canonical(target.rstrip('/'), uri_target=True)"),
    'user_agent_directive_case_sensitive_value': (
        "agents.append(value.lower())", "agents.append(value)"),
    'url_without_path_invalid': (
        "target = parsed.path or '/'", "target = parsed.path"),
}

def prepare_cases(cases):
    """Expand only explicitly declared fixture generators, preserving expected labels."""
    expanded=[]
    for case in cases:
        case=dict(case)
        if "repeat_target_count" in case:
            case["target"] += case.pop("repeat_target_char") * case.pop("repeat_target_count")
        expanded.append(case)
    return expanded


def evaluate(cases=()):
    cases=prepare_cases(cases)
    # A fixture with a wrong expected label can "kill" every mutant.
    # Reject that invalid experiment before reporting any mutation score.
    baseline_failures=run_case_suite(baseline_decide, list(CORPUS)+list(TARGETED)+cases)
    if baseline_failures:
        raise AssertionError('baseline fails expected fixtures: '+repr(baseline_failures[:8]))
    rows=[]
    for name,(needle,replacement) in HOLDOUT.items():
        n=SOURCE.count(needle)
        if n!=1:
            raise ValueError(f'{name}: needle count {n}, expected 1')
        mutated=SOURCE.replace(needle,replacement,1)
        decide=module_for('c328_'+name,mutated).decide
        fails=run_case_suite(decide,list(CORPUS)+list(TARGETED)+cases)
        oracle=None if fails else run_oracle_suite(decide)
        rows.append({'mutant':name,'killed':bool(fails or oracle),
                     'fixture_kills':[f['id'] for f in fails], 'oracle_kill':oracle})
    return {'mutants':len(rows),'killed':sum(x['killed'] for x in rows),
            'survived':[x['mutant'] for x in rows if not x['killed']], 'details':rows}

if __name__=='__main__':
    holdout=evaluate()
    cases=json.loads((Path(__file__).with_name('c328_targeted_cases.json')).read_text(encoding='utf-8'))['cases']
    after=evaluate(cases)
    print(json.dumps({'holdout':holdout,'post_targeted':after,'targeted_cases':len(cases)},indent=2))
