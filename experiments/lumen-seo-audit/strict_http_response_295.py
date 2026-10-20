"""Conservative HTTP/1.x wire guard for Lumen's loopback-only SEO fixtures.

Not a general-purpose HTTP client. Reject ambiguous response headers, incomplete
chunk termination, extensions and trailers rather than silently normalize them.
"""
import http.client
import re

_MAX_HEADER_BYTES = 16_384
_MAX_STATUS_BYTES = 4_096
_MAX_INTERIM_RESPONSES = 3
_TOKEN = re.compile(rb"[!#$%&'*+.^_`|~0-9A-Za-z-]+\Z")


class _GuardedHeaderReader:
    def __init__(self, wrapped):
        self._wrapped = wrapped
        self._mode = 'status'
        self._bytes = 0
        self._interim = 0
        self._current_interim = False

    def readline(self, size=-1):
        line = self._wrapped.readline(size)
        if self._mode == 'body':
            return line
        if not line.endswith(b'\r\n'):
            raise ValueError('Non-CRLF HTTP status/header line')
        if self._mode == 'status':
            if len(line) > _MAX_STATUS_BYTES:
                raise ValueError('HTTP status line too large')
            self._current_interim = bool(re.match(rb'HTTP/1\.[01] 100(?: |\r\n)', line))
            self._mode = 'headers'
            self._bytes = len(line)
            return line
        self._bytes += len(line)
        if self._bytes > _MAX_HEADER_BYTES:
            raise ValueError('HTTP response headers too large')
        if line == b'\r\n':
            if self._current_interim:
                self._interim += 1
                if self._interim > _MAX_INTERIM_RESPONSES:
                    raise ValueError('Too many interim HTTP responses')
                self._mode = 'status'
            else:
                self._mode = 'body'
            return line
        if line[:1] in (b' ', b'\t'):
            raise ValueError('Folded HTTP header line rejected')
        key, sep, value = line[:-2].partition(b':')
        if not sep or not _TOKEN.fullmatch(key):
            raise ValueError('Invalid HTTP header field name')
        if any((b < 32 and b != 9) or b == 127 for b in value):
            raise ValueError('Control byte in HTTP header value')
        return line

    def __getattr__(self, attr):
        return getattr(self._wrapped, attr)


class StrictHTTPResponse(http.client.HTTPResponse):
    def begin(self):
        if self.headers is None and not isinstance(self.fp, _GuardedHeaderReader):
            self.fp = _GuardedHeaderReader(self.fp)
        return super().begin()

    def _read_next_chunk_size(self):
        line = self.fp.readline(82)
        if not re.fullmatch(rb'[0-9A-Fa-f]{1,16}\r\n', line):
            raise ValueError('Invalid chunk size line')
        return int(line[:-2], 16)

    def _read_and_discard_trailer(self):
        if self.fp.readline(82) != b'\r\n':
            raise ValueError('Missing final CRLF or unsupported chunk trailer')

    def _get_chunk_left(self):
        remaining = self.chunk_left
        if not remaining:
            if remaining is not None and self._safe_read(2) != b'\r\n':
                raise ValueError('Invalid chunk data terminator')
            remaining = self._read_next_chunk_size()
            if remaining == 0:
                self._read_and_discard_trailer()
                self._close_conn()
                remaining = None
            self.chunk_left = remaining
        return remaining
