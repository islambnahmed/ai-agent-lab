"""Offline robots.txt decision aid: explicit evidence and conservative uncertainty.

This is a bounded RFC 9309-style evaluator, NOT a complete search-engine emulator.
Only local text and paths are accepted; no network calls or crawler execution.
Unknown/invalid input produces an abstention rather than a guessed permission.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import urlsplit

MAX_BYTES = 500 * 1024
_UNRESERVED = frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~')
_HEX = frozenset('0123456789abcdefABCDEF')

@dataclass(frozen=True)
class Decision:
    status: str  # allowed, disallowed, unknown
    group: str | None
    rule: str | None
    reason: str


def _canonical(s: str, *, uri_target: bool = False) -> str:
    """Normalize unreserved escapes and UTF-8 for robots rule or URI.

    URI literals '*' and '$' must be encoded before matching: in a robots
    rule these are pattern operators, but in a requested URI they are data.
    Percent-encoded reserved bytes remain encoded in either context.
    Malformed percent escapes are rejected conservatively.
    """
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == '%':
            if i + 2 >= len(s) or s[i + 1] not in _HEX or s[i + 2] not in _HEX:
                raise ValueError('malformed percent escape')
            value = int(s[i+1:i+3], 16)
            char = chr(value)
            out.append(char if char in _UNRESERVED else f'%{value:02X}')
            i += 3
            continue
        if uri_target and c in '*$':
            out.append(f'%{ord(c):02X}')
        elif ord(c) < 128:
            out.append(c)
        else:
            out.extend(f'%{b:02X}' for b in c.encode('utf-8'))
        i += 1
    return ''.join(out)


def _glob_matches(core: str, target: str, anchored: bool) -> bool:
    """Greedy glob matcher for '*' with bounded linear scan; no regex backtracking."""
    i = j = 0
    star = -1
    retry = 0
    while i < len(target):
        if j == len(core) and not anchored:
            return True
        if j < len(core) and core[j] == target[i]:
            i += 1
            j += 1
        elif j < len(core) and core[j] == '*':
            star = j
            j += 1
            retry = i
        elif star >= 0:
            j = star + 1
            retry += 1
            i = retry
        else:
            return False
    while j < len(core) and core[j] == '*':
        j += 1
    return j == len(core)


def parse_groups(robots: str):
    if not isinstance(robots, str):
        raise ValueError('robots text required')
    if len(robots.encode('utf-8')) > MAX_BYTES:
        raise ValueError('file exceeds bounded 500 KiB inspection limit')
    # Google ignores a UTF-8 BOM at the beginning of robots.txt. Without
    # stripping it, the first User-agent directive is silently discarded.
    robots = robots.removeprefix('\ufeff')
    groups = []
    agents, rules = [], []
    saw_rule_line = False
    for line_number, raw in enumerate(robots.splitlines(), 1):
        line = raw.split('#', 1)[0].strip()
        if not line or ':' not in line:
            continue
        key, value = line.split(':', 1)
        key, value = key.strip().lower(), value.strip()
        if key == 'user-agent':
            if not value or not re.fullmatch(r'[A-Za-z0-9_.-]+|\*', value):
                raise ValueError(f'invalid user-agent at line {line_number}')
            if agents and saw_rule_line:
                groups.append((tuple(agents), tuple(rules)))
                agents, rules = [], []
                saw_rule_line = False
            agents.append(value.lower())
        elif key in ('allow', 'disallow'):
            if not agents:
                continue
            # Even an empty Allow/Disallow is a syntactic rule line, so the
            # following User-agent starts a new group (RFC 9309, §2.2).
            saw_rule_line = True
            if not value:
                continue  # empty Disallow/Allow has no matching path
            if not value.startswith('/') or len(value) > 8192:
                raise ValueError(f'unsupported rule path at line {line_number}')
            # Only a terminal '$' and '*' wildcards are supported.
            if '$' in value.rstrip('$'):
                raise ValueError(f'unsupported dollar anchor at line {line_number}')
            rules.append((key, _canonical(value), line_number))
        # Sitemap, Crawl-delay and extensions are ignored, not permission rules.
    if agents:
        groups.append((tuple(agents), tuple(rules)))
    return groups


def decide(robots: str, product_token: str, url_or_path: str) -> Decision:
    try:
        if not isinstance(product_token, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+', product_token):
            raise ValueError('product token must be a single valid token')
        if not isinstance(url_or_path, str):
            raise ValueError('URL/path required')
        if '://' in url_or_path:
            parsed = urlsplit(url_or_path)
            if parsed.scheme.lower() not in ('http', 'https') or not parsed.netloc or parsed.username or parsed.password:
                raise ValueError('unsupported URL form')
            target = parsed.path or '/'
            if parsed.query:
                target += '?' + parsed.query
        else:
            target = url_or_path
        if len(target) > 8192 or not target.startswith('/') or '#' in target:
            raise ValueError('absolute path required without fragment')
        if target.split('?', 1)[0] == '/robots.txt':
            return Decision('allowed', None, None, 'robots.txt is implicitly allowed')
        target = _canonical(target, uri_target=True)
        groups = parse_groups(robots)
        token = product_token.lower()
        specific = [(agents, rules) for agents, rules in groups if any(a != '*' and a in token for a in agents)]
        if specific:
            max_len = max(len(a) for agents, _ in specific for a in agents if a != '*' and a in token)
            applicable = [(agents, rules) for agents, rules in specific if any(a != '*' and a in token and len(a) == max_len for a in agents)]
            selected = '/'.join(sorted({a for agents, _ in applicable for a in agents if a != '*' and a in token and len(a) == max_len}))
        else:
            applicable = [(agents, rules) for agents, rules in groups if '*' in agents]
            selected = '*' if applicable else None
        matches = []
        for _, rules in applicable:
            for kind, pattern, line in rules:
                anchored = pattern.endswith('$')
                core = pattern[:-1] if anchored else pattern
                if _glob_matches(core, target, anchored):
                    # Published Google precedence examples count wildcard/anchor
                    # syntax in the rule's length. Omitting '*' or '$'
                    # misclassifies /*.htm vs /page and /$ vs /.
                    score = len(pattern.encode('utf-8'))
                    matches.append((score, kind == 'allow', kind, pattern, line))
        if not matches:
            return Decision('allowed', selected, None, 'no matching allow/disallow rule')
        best = max(matches, key=lambda r: (r[0], r[1]))
        return Decision('allowed' if best[1] else 'disallowed', selected,
                        f'{best[2]}: {best[3]} (line {best[4]})', 'longest matching rule pattern; allow wins ties')
    except (ValueError, UnicodeError) as exc:
        return Decision('unknown', None, None, str(exc))
