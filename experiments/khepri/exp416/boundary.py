"""A small structural trust boundary for an AI Agent Lab tool workflow.

The action is determined exclusively by TrustedIntent, NEVER by ToolResult.
This is a deterministic local simulator, not a substitute for LLM instruction
hierarchy, source verification, or runtime authorization.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from html.parser import HTMLParser
import json
import re
import unicodedata

REPO = 'islambnahmed/ai-agent-lab'
BRANCH = 'khepri/exp416-untrusted-tool-boundary-20261024'
PREFIX = 'experiments/khepri/exp416/'
_ALLOWED = {'read', 'write'}
_COMPONENT = re.compile(r'^[A-Za-z0-9_.-]+$')


@dataclass(frozen=True)
class TrustedIntent:
    operation: str
    repository: str
    branch: str
    path: str


@dataclass(frozen=True)
class ToolResult:
    source: str
    body: str


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    action: tuple[str, str, str, str] | None


def authorize(intent: TrustedIntent) -> Decision:
    """Allow only predeclared experiment-scoped actions, without inspecting data."""
    if not isinstance(intent, TrustedIntent):
        return Decision(False, 'not a trusted intent', None)
    fields = (intent.operation, intent.repository, intent.branch, intent.path)
    if not all(isinstance(v, str) for v in fields):
        return Decision(False, 'invalid field type', None)
    if intent.operation not in _ALLOWED or intent.repository != REPO or intent.branch != BRANCH:
        return Decision(False, 'operation or scope not allowlisted', None)
    path = intent.path
    if path != unicodedata.normalize('NFKC', path):
        return Decision(False, 'noncanonical path', None)
    if not path.startswith(PREFIX) or len(path.encode('utf8')) > 240:
        return Decision(False, 'path outside experiment or too long', None)
    components = path.split('/')
    if any(c in ('', '.', '..') or not _COMPONENT.fullmatch(c) for c in components):
        return Decision(False, 'unsafe path component', None)
    if any(c in ('.git', '.env') or c.startswith('.git') for c in components):
        return Decision(False, 'reserved file', None)
    return Decision(True, 'trusted intent within experiment scope', fields)


def prepare_observation(result: ToolResult, limit: int = 600) -> str:
    """Serialize untrusted material as labeled DATA, never as action metadata.

    UTF-8 length is bounded for predictable downstream resource use. Truncation
    is byte-safe; a digest covers the full body for auditing. JSON encoding is
    not a guarantee that a later language model will ignore instructions.
    """
    if not isinstance(result, ToolResult) or not isinstance(result.source, str) or not isinstance(result.body, str):
        raise ValueError('invalid tool result')
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100_000:
        raise ValueError('invalid byte limit')
    try:
        raw = result.body.encode('utf8')
    except UnicodeEncodeError as exc:
        raise ValueError('invalid Unicode in untrusted body') from exc
    excerpt = raw[:limit].decode('utf8', errors='ignore')
    envelope = {'trust': 'untrusted_data', 'source': result.source[:100],
                'body_excerpt': excerpt, 'truncated': len(raw) > limit,
                'body_sha256': sha256(raw).hexdigest(), 'bytes': len(raw)}
    return json.dumps(envelope, ensure_ascii=True, sort_keys=True)


class _Title(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.title = []

    def handle_starttag(self, tag, attrs):
        if tag == 'title':
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)


def extract_observation(result: ToolResult, domain: str) -> dict:
    """Extract bounded typed facts, not commands, from two synthetic domains."""
    if not isinstance(result, ToolResult):
        raise ValueError('invalid result')
    if domain == 'seo_html':
        parser = _Title()
        parser.feed(result.body[:100_000])
        return {'kind': 'seo_title', 'value': ''.join(parser.title)[:160]}
    if domain == 'github_issue':
        return {'kind': 'issue_first_line', 'value': result.body.splitlines()[0][:160] if result.body else ''}
    raise ValueError('unknown domain')


def route(intent: TrustedIntent, result: ToolResult, domain: str) -> dict:
    """Return a simulated action and observations; never call an external API."""
    decision = authorize(intent)
    return {'decision': decision, 'observation': extract_observation(result, domain),
            'serialized_data': prepare_observation(result)}
