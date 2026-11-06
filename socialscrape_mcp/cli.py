"""`socialscrape-mcp`: run the MCP server.

    socialscrape-mcp                      stdio (what Claude Desktop, Cursor and Claude Code launch)
    socialscrape-mcp http --port 8080     streamable HTTP, to host yourself (needs the [http] extra)
    socialscrape-mcp tools                print the tool list
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys

from . import __version__
from .catalog import load_catalog
from .protocol import McpServer
from .settings import Settings
from .stdio import serve_stdio
from .tools import ToolFilter


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="socialscrape-mcp", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--platforms", default=os.environ.get("SOCIALSCRAPE_PLATFORMS"),
                    help="comma list of platforms to expose (default all); env SOCIALSCRAPE_PLATFORMS")
    ap.add_argument("--toolsets", default=os.environ.get("SOCIALSCRAPE_TOOLSETS"),
                    help="core, platforms or all (default all); env SOCIALSCRAPE_TOOLSETS")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("stdio", help="serve over stdio (the default)")
    http = sub.add_parser("http", help="serve streamable HTTP")
    http.add_argument("--host", default="127.0.0.1")
    http.add_argument("--port", type=int, default=8080)
    sub.add_parser("tools", help="print the tools as JSON")
    args = ap.parse_args(argv)

    logging.basicConfig(level=os.environ.get("SOCIALSCRAPE_LOG_LEVEL", "WARNING"), stream=sys.stderr)
    settings = Settings.from_env()
    filt = ToolFilter.parse(args.platforms, args.toolsets)
    if args.cmd == "tools":
        server = McpServer(load_catalog(), settings)
        print(json.dumps([t.listing() for t in server.tools(filt)], indent=1))
        return 0
    if args.cmd == "http":
        try:
            import uvicorn
        except ImportError:
            print("the http server needs: pip install 'socialscrape-mcp[http]'", file=sys.stderr)
            return 2
        from .http_app import create_app

        uvicorn.run(create_app(settings), host=args.host, port=args.port, log_level="warning")
        return 0
    if not settings.api_key:
        print("socialscrape-mcp: set SOCIALSCRAPE_API_KEY (get a key at https://socialscrape.dev/app). "
              "Starting anyway: tools list, but calls will explain the missing key.", file=sys.stderr)
    serve_stdio(McpServer(load_catalog(), settings), filt)
    return 0
