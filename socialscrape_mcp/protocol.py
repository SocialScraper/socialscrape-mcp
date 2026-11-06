"""The MCP protocol (JSON-RPC 2.0), small enough to read in one sitting.

SocialScrape exposes tools only, so the server needs initialize, ping,
tools/list and tools/call. Keeping the protocol layer here, independent of the
transport, lets stdio and streamable HTTP share it. It is stateless: no
session is held between requests, which is what lets the hosted server run
as many replicas as it likes.
"""

from __future__ import annotations

import logging
from typing import Any

from . import __version__
from .catalog import Catalog
from .client import ApiClient
from .render import error_result
from .settings import Settings
from .tools import CallContext, Tool, ToolFilter, build_tools

log = logging.getLogger("socialscrape_mcp")

SUPPORTED_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND, INVALID_PARAMS, INTERNAL_ERROR = -32700, -32600, -32601, -32602, -32603

INSTRUCTIONS = (
    "SocialScrape returns social media data (profiles, posts, comments, search, ads, "
    "transcripts) in one normalised shape. Start with get_transcript, search, get_profile, get_post or "
    "get_comments; use a platform tool (github, facebook, ...) for the rest, and describe to see exact parameters. "
    "Every successful call costs credits (the first line of each result says how many and what is left); failures "
    "and cached repeats (max_age_days) are free. Lists are paged: pass the returned cursor back for more, and only "
    "when you need more, since each page costs credits."
)


def _error(id_: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


class McpServer:
    def __init__(self, catalog: Catalog, settings: Settings, client: ApiClient | None = None):
        self.catalog = catalog
        self.settings = settings
        self.client = client or ApiClient(settings.api_url, timeout=settings.timeout)
        self._tools: dict[tuple, list[Tool]] = {}

    def tools(self, filt: ToolFilter) -> list[Tool]:
        # Normalise to platforms that exist: the filter comes from a URL, and
        # arbitrary names must not each add an entry to the cache.
        known = {g.key for g in self.catalog.groups}
        if filt.platforms is not None:
            filt = ToolFilter(frozenset(filt.platforms & known), filt.toolsets)
        key = (filt.platforms, filt.toolsets)
        if key not in self._tools:
            self._tools[key] = build_tools(self.catalog, filt)
        return self._tools[key]

    # ------------------------------------------------------------ dispatch

    def handle(self, message: Any, *, api_key: str | None = None, filt: ToolFilter | None = None) -> dict[str, Any] | None:
        """One JSON-RPC message in, one response out (None for notifications)."""
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            return _error(message.get("id") if isinstance(message, dict) else None, INVALID_REQUEST, "not a JSON-RPC 2.0 message")
        method = message.get("method")
        has_id = "id" in message
        if not isinstance(method, str):
            return None if not has_id else _error(message.get("id"), INVALID_REQUEST, "missing method")
        if not has_id:
            return None  # notifications (initialized, cancelled, ...) need no answer
        id_ = message["id"]
        params = message.get("params") or {}
        if not isinstance(params, dict):
            return _error(id_, INVALID_PARAMS, "params must be an object")
        filt = filt or ToolFilter()
        try:
            if method == "initialize":
                return {"jsonrpc": "2.0", "id": id_, "result": self._initialize(params)}
            if method == "ping":
                return {"jsonrpc": "2.0", "id": id_, "result": {}}
            if method == "tools/list":
                return {"jsonrpc": "2.0", "id": id_, "result": {"tools": [t.listing() for t in self.tools(filt)]}}
            if method == "tools/call":
                return self._call(id_, params, api_key or self.settings.api_key, filt)
        except Exception:  # never let a bug become a stack trace on the wire
            log.exception("mcp request failed: %s", method)
            return _error(id_, INTERNAL_ERROR, "internal error")
        return _error(id_, METHOD_NOT_FOUND, f"method not found: {method}")

    def _initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        asked = params.get("protocolVersion")
        version = asked if asked in SUPPORTED_VERSIONS else SUPPORTED_VERSIONS[0]
        return {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "socialscrape", "title": "SocialScrape", "version": __version__},
            "instructions": INSTRUCTIONS,
        }

    def _call(self, id_: Any, params: dict[str, Any], api_key: str | None, filt: ToolFilter) -> dict[str, Any]:
        name = params.get("name")
        tool = next((t for t in self.tools(filt) if t.name == name), None)
        if tool is None:
            return _error(id_, INVALID_PARAMS, f"unknown tool: {name}")
        args = params.get("arguments") or {}
        if not isinstance(args, dict):
            return _error(id_, INVALID_PARAMS, "arguments must be an object")
        ctx = CallContext(self.client, self.settings, api_key)
        try:
            out = tool.run(args, ctx)
        except Exception:
            log.exception("tool %s failed", name)
            out = error_result("something went wrong inside the MCP server; no credits were charged",
                               code="internal", retryable=True, cat=self.catalog)
        return {"jsonrpc": "2.0", "id": id_, "result": out}
