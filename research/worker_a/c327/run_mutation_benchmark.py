"""Deterministic, offline source-level mutation benchmark for Worker A C327.

Only tests copied local parser code; no network requests, subprocesses, or writes
outside this working directory. All mutations are single textual replacements.
"""
from __future__ import annotations
import json
import sys
import types
import itertools
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ROOT = REPO_ROOT / 'research' / 'worker_a' / 'c326'
PARSER_DIR = REPO_ROOT / 'research' / 'worker_a' / 'c318'
sys.path.insert(0, str(PARSER_DIR))

SOURCE = (PARSER_DIR / 'robots_gate.py').read_text(encoding='utf-8')
CORPUS = json.loads((ROOT / 'c326_offline_seo_corpus.json').read_text(encoding='utf-8'))['cases']

# Mutations are designed to simulate realistic regressions, not equivalent mutants.
MUTANTS = {
 'bom_not_removed': ("robots = robots.removeprefix('\\ufeff')", 'robots = robots'),
 'empty_rule_does_not_split_group': ('saw_rule_line = True', 'saw_rule_line = bool(value)'),
 'allow_loses_tie': ('key=lambda r: (r[0], r[1])', 'key=lambda r: (r[0], not r[1])'),
 'shortest_rule_wins': ('best = max(matches, key=', 'best = min(matches, key='),
 'wildcard_fallback_ignored': ("if '*' in agents]", 'if False]'),
 'star_not_wildcard': ("elif j < len(core) and core[j] == '*':", "elif j < len(core) and core[j] == '\\0':"),
 'anchor_never_enforced': ("anchored = pattern.endswith('$')", 'anchored = False'),
 'skip_uri_literal_escaping': ("if uri_target and c in '*$':", "if False and c in '*$':"),
 'percent_decode_reserved': ("char if char in _UNRESERVED else f'%{value:02X}'", 'char'),
 'malformed_percent_accepted': ("raise ValueError('malformed percent escape')", "return s"),
 'file_limit_disabled': ("if len(robots.encode('utf-8')) > MAX_BYTES:", 'if False:'),
 'robots_txt_not_implicit': ("if target.split('?', 1)[0] == '/robots.txt':", 'if False:'),
 'product_token_case_sensitive': ('token = product_token.lower()', 'token = product_token'),
 'url_query_dropped': ("if parsed.query:\n                target += '?' + parsed.query", 'if False:\n                target += \'?\' + parsed.query'),
 'relative_target_permitted': ("or not target.startswith('/')", 'or False'),
 'rule_names_case_sensitive': ('key.strip().lower(), value.strip()', 'key.strip(), value.strip()'),
 'ignore_user_agent_specificity': ("if specific:", 'if False:'),
 'repeated_dollar_not_rejected': ("if '$' in value[:-1]:", "if '$' in value.rstrip('$'):"),
 'rule_path_without_slash_accepted': ("if not value.startswith('/') or len(value) > 8192:", 'if len(value) > 8192:'),
 'prefix_score_ignores_anchor': ("score = len(pattern.encode('utf-8'))", "score = len(core.replace('*','').encode('utf-8'))"),
 'nonanchored_prefix_requires_fullmatch': ('if j == len(core) and not anchored:', 'if j == len(core) and anchored:'),
 'empty_disallow_blocks_all': ("if not value:\n                continue", "if not value:\n                value = '/'"),
}


def run_case_suite(decide, corpus):
    failures=[]
    for case in corpus:
        robots = case['robots'] + case.get('repeat_char','') * case.get('repeat_count',0)
        try:
            actual=decide(robots,case['agent'],case['target']).status
        except Exception as exc:
            actual='EXCEPTION:'+type(exc).__name__
        if actual!=case['expected']:
            failures.append({'id':case['id'],'expected':case['expected'],'actual':actual})
    return failures


def reference_prefix(rules, target):
    applicable = [(len(prefix), kind == 'Allow') for kind, prefix in rules if target.startswith(prefix)]
    return 'allowed' if not applicable or max(applicable)[1] else 'disallowed'


def reference_glob(pattern, target):
    anchor = pattern.endswith('$')
    core = pattern[:-1] if anchor else pattern
    expression = ''.join('.*' if c == '*' else re.escape(c) for c in core)
    return (re.fullmatch if anchor else re.match)(expression, target) is not None


def run_oracle_suite(decide):
    # Reuse the independent C326 oracles; 21,452 comparisons, no parser internals.
    from itertools import product
    paths=['/'+''.join(s) for n in range(5) for s in product('ab',repeat=n)]
    prefixes=['/'+''.join(s) for n in range(4) for s in product('ab',repeat=n)]
    for a in prefixes:
        for b in prefixes:
            for k1,k2 in [('Allow','Disallow'),('Disallow','Allow')]:
                rules=[(k1,a),(k2,b)]
                robots='User-agent: *\n'+'\n'.join(f'{k}: {p}' for k,p in rules)
                for target in paths:
                    if decide(robots,'ExampleBot',target).status!=reference_prefix(rules,target):
                        return 'prefix_oracle'
    patterns=['/'+''.join(s) for n in range(5) for s in product('ab*',repeat=n)]
    for pattern in patterns:
        for anchor in ('','$'):
            rule=pattern+anchor
            robots='User-agent: *\nDisallow: '+rule
            for target in paths:
                expected='disallowed' if reference_glob(rule,target) else 'allowed'
                if decide(robots,'ExampleBot',target).status!=expected:
                    return 'wildcard_oracle'
    return None


def module_for(name, source):
    module=types.ModuleType('mutant_'+name)
    module.__file__='<in-memory mutant '+name+'>'
    sys.modules[module.__name__]=module
    exec(compile(source,module.__file__,'exec'),module.__dict__)
    return module


TARGETED = json.loads((Path(__file__).with_name('c327_targeted_cases.json')).read_text(encoding='utf-8'))['cases']

def evaluate(corpus=CORPUS):
    report=[]
    for name,(needle,replacement) in MUTANTS.items():
        if SOURCE.count(needle)!=1:
            raise ValueError(f'mutation {name}: expected unique needle, found {SOURCE.count(needle)}')
        source=SOURCE.replace(needle,replacement,1)
        try:
            decide=module_for(name,source).decide
            failures=run_case_suite(decide,corpus)
            oracle=None if failures else run_oracle_suite(decide)
            killed=bool(failures or oracle)
            report.append({'mutant':name,'killed':killed,'fixture_kills':[f['id'] for f in failures],
                           'oracle_kill':oracle})
        except Exception as exc:
            report.append({'mutant':name,'killed':True,'fixture_kills':[],
                           'oracle_kill':'compile_or_runtime_error: '+repr(exc)})
    return {'mutants':len(report),'killed':sum(x['killed'] for x in report),
            'survived':[x['mutant'] for x in report if not x['killed']], 'details':report}

if __name__=='__main__':
    before=evaluate()
    after=evaluate(CORPUS + TARGETED)
    result={'baseline':before,'augmented':after,'added_cases':len(TARGETED)}
    print(json.dumps(result,indent=2))
