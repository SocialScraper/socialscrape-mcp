"""MCP over stdio: one JSON-RPC message per line on stdin, answers on stdout.

stdout is the protocol channel, so everything else (logs) goes to stderr.
"""

from __future__ import annotations

import json
import sys
from typing import IO

from .protocol import INVALID_REQUEST, PARSE_ERROR, McpServer, _error
from .tools import ToolFilter


def serve_stdio(server: McpServer, filt: ToolFilter, stdin: IO[str] | None = None, stdout: IO[str] | None = None) -> None:
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            _write(stdout, _error(None, PARSE_ERROR, "invalid JSON"))
            continue
        batch = msg if isinstance(msg, list) else [msg]
        if not batch:
            _write(stdout, _error(None, INVALID_REQUEST, "empty batch"))
            continue
        answers = [a for a in (server.handle(m, filt=filt) for m in batch) if a is not None]
        if answers:
            _write(stdout, answers if isinstance(msg, list) else answers[0])


def _write(out: IO[str], obj: object) -> None:
    out.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")
    out.flush()
