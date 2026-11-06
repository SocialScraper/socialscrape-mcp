"""The hosted MCP server: MCP "streamable HTTP" over a stateless ASGI app.

    POST /mcp      JSON-RPC in, JSON out (202 for notifications)
    GET  /healthz  liveness
    GET  /         a few lines for humans who open the URL in a browser

Authentication is the user's own SocialScrape API key, sent as `x-api-key` or
`Authorization: Bearer <key>`. The key is forwarded to the API on each call and
never stored or logged here; credits are charged to its team by the API.
Discovery (initialize, tools/list) works without a key so directories and
clients can list the tools; a tool call without one explains how to add it.

Narrow the tool list per connection with query parameters on the URL:

    /mcp?platforms=github,threads     only those platform tools (and platform choices)
    /mcp?toolsets=core                 only the cross-platform and account tools
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any

import anyio
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from . import __version__
from .catalog import Catalog, load_catalog
from .client import ApiClient
from .protocol import INVALID_REQUEST, PARSE_ERROR, McpServer, _error
from .settings import Settings
from .tools import ToolFilter

MAX_BODY_BYTES = 1_000_000
MAX_BATCH = 20  # JSON-RPC batch items per request; each tool call holds a worker thread


def extract_key(request: Request) -> str | None:
    key = request.headers.get("x-api-key", "").strip()
    if key:
        return key
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return None


def extract_filter(request: Request) -> ToolFilter:
    q = request.query_params
    return ToolFilter.parse(q.get("platforms") or request.headers.get("x-socialscrape-platforms"),
                            q.get("toolsets") or request.headers.get("x-socialscrape-toolsets"))


def create_app(settings: Settings | None = None, catalog: Catalog | None = None,
               client: ApiClient | None = None) -> Starlette:
    settings = settings or Settings.from_env()
    # The hosted server acts only on the caller's own key. A key left in this
    # process's environment (SOCIALSCRAPE_API_KEY, meant for stdio) must never
    # become the identity of anonymous callers, so it is dropped here.
    settings = dataclasses.replace(settings, api_key=None)
    server = McpServer(catalog or load_catalog(), settings, client)
    origins = settings.allowed_origins

    async def mcp(request: Request) -> Response:
        if request.method != "POST":
            return Response(status_code=405, headers={"Allow": "POST, OPTIONS"})
        origin = request.headers.get("origin")
        if origins and origin and origin not in origins:
            return JSONResponse(_error(None, INVALID_REQUEST, "origin not allowed"), status_code=403)
        raw = await request.body()
        if len(raw) > MAX_BODY_BYTES:
            return JSONResponse(_error(None, INVALID_REQUEST, "request too large"), status_code=413)
        try:
            msg = json.loads(raw)
        except ValueError:
            return JSONResponse(_error(None, PARSE_ERROR, "invalid JSON"), status_code=400)
        key, filt = extract_key(request), extract_filter(request)
        batch = msg if isinstance(msg, list) else [msg]
        if not batch:
            return JSONResponse(_error(None, INVALID_REQUEST, "empty batch"), status_code=400)
        if len(batch) > MAX_BATCH:
            return JSONResponse(_error(None, INVALID_REQUEST, f"at most {MAX_BATCH} messages per request"), status_code=400)

        def run_all() -> list[dict[str, Any]]:
            return [a for a in (server.handle(m, api_key=key, filt=filt) for m in batch) if a is not None]

        answers = await anyio.to_thread.run_sync(run_all)
        if not answers:
            return Response(status_code=202)
        return JSONResponse(answers if isinstance(msg, list) else answers[0])

    async def health(_: Request) -> Response:
        return JSONResponse({"status": "ok", "version": __version__})

    async def index(_: Request) -> Response:
        return JSONResponse({
            "name": "SocialScrape MCP server", "version": __version__, "endpoint": "/mcp",
            "transport": "streamable-http", "auth": "x-api-key header or Authorization: Bearer <key>",
            "docs": "https://socialscrape.dev/docs/mcp", "tools": len(server.tools(ToolFilter())),
        })

    app = Starlette(
        routes=[Route("/mcp", mcp, methods=["GET", "POST", "DELETE"]), Route("/healthz", health), Route("/", index)],
        middleware=[Middleware(
            CORSMiddleware, allow_origins=list(origins) or ["*"], allow_methods=["POST", "GET", "DELETE", "OPTIONS"],
            allow_headers=["content-type", "x-api-key", "authorization", "mcp-protocol-version", "mcp-session-id",
                           "x-socialscrape-platforms", "x-socialscrape-toolsets"],
        )],
    )
    app.state.mcp = server
    return app


def app_from_env() -> Starlette:
    """`uvicorn socialscrape_mcp.http_app:app_from_env --factory --host 0.0.0.0 --port 8080`"""
    return create_app()
