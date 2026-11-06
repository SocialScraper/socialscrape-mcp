"""Turn an API envelope into an MCP tool result.

Every result starts with one line an agent can read at a glance: what it cost
and what is left. The structured copy carries the same numbers as fields.
"""

from __future__ import annotations

import json
from typing import Any

from .catalog import Catalog
from .client import ApiResponse

ListKeys = ("items", "results")

HINTS = {
    "unauthorized": "The API key is missing or wrong. Create one at {dash} and set SOCIALSCRAPE_API_KEY "
                    "(stdio) or send it in the x-api-key header (HTTP mode).",
    "insufficient_credits": "Out of credits. Buy a pack or switch plan at {dash}. get_credits shows the balance for free.",
    "forbidden": "This key or its team is suspended. Contact support@socialscrape.dev.",
    "invalid_params": "Call describe with this platform and resource to see the exact parameters.",
    "unsupported_url": "Call describe with this platform and resource to see which URLs it accepts.",
    "rate_limited": "Too many requests for this plan. Wait for the time in Retry-After, then try again.",
    "not_implemented": "That endpoint is not built yet. Call describe to see what is available.",
}


def compact(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=str)


def result(text: str, structured: dict | None = None, *, error: bool = False) -> dict[str, Any]:
    out: dict[str, Any] = {"content": [{"type": "text", "text": text}], "isError": error}
    if structured is not None:
        out["structuredContent"] = structured
    return out


def error_result(message: str, *, code: str = "invalid_params", retryable: bool = False, cat: Catalog | None = None,
                 request_id: str | None = None) -> dict[str, Any]:
    dash = (cat.api.get("dashboard_url") if cat else None) or "https://socialscrape.dev/app"
    hint = HINTS.get(code, "").format(dash=dash)
    lines = [f"error: {code}: {message}", f"retryable: {'yes' if retryable else 'no'} | credits charged: 0"]
    if hint:
        lines.append(hint)
    structured = {"ok": False, "error": {"code": code, "message": message, "retryable": retryable},
                  "credits_charged": 0, "request_id": request_id}
    return result("\n".join(lines), structured, error=True)


def fit(payload: Any, max_chars: int) -> tuple[Any, dict | None]:
    """Make `payload` serialise within max_chars by dropping trailing list
    items (a page of results is still valid JSON afterwards). Returns the
    payload and a note about what was dropped, or None when nothing was."""
    if len(compact(payload)) <= max_chars:
        return payload, None
    if isinstance(payload, dict):
        for key in ListKeys:
            seq = payload.get(key)
            if isinstance(seq, list) and seq:
                lo, hi = 0, len(seq)
                while lo < hi:  # the most items that still fit
                    mid = (lo + hi + 1) // 2
                    if len(compact({**payload, key: seq[:mid]})) <= max_chars:
                        lo = mid
                    else:
                        hi = mid - 1
                note = {"kept": lo, "total": len(seq), "field": key}
                return {**payload, key: seq[:lo]}, note
    text = compact(payload)
    return {"truncated_json": text[:max_chars]}, {"kept_chars": max_chars, "total_chars": len(text)}


def render_response(resp: ApiResponse, cat: Catalog, *, max_chars: int, label: str = "") -> dict[str, Any]:
    body = resp.body
    rid = body.get("request_id")
    if not body.get("ok"):
        err = body.get("error") or {}
        out = error_result(str(err.get("message", "request failed")), code=str(err.get("code", "internal")),
                           retryable=bool(err.get("retryable")), cat=cat, request_id=rid)
        if resp.headers.get("retry-after"):
            out["content"][0]["text"] += f"\nRetry-After: {resp.headers['retry-after']} seconds"
        return out
    data = body.get("data")
    payload: Any = data
    if "raw" in body:
        payload = {"data": data, "raw": body["raw"]}
    payload, dropped = fit(payload, max_chars)
    head = _head(body, resp.status)
    lines = [head]
    if isinstance(data, dict) and data.get("object") == "job":
        lines.append(f"The job is still running. Call get_job with job_id={data.get('job_id')} in a few seconds "
                     "(polling is free; the charge happens once, when it finishes).")
    page = _page_line(body, data)
    if page:
        lines.append(page)
    if dropped:
        lines.append(f"output shortened to fit: {json.dumps(dropped)}. Ask for fewer items (limit) or use the cursor.")
    lines.append(compact(payload))
    structured = {k: body.get(k) for k in ("ok", "credits_charged", "credits_remaining", "cached", "cached_at",
                                           "request_id", "cursor", "has_more")}
    structured["data"] = payload
    if dropped:
        structured["truncated"] = dropped
    return result("\n".join(lines), structured)


def _head(body: dict, status: int) -> str:
    bits = ["ok"]
    if status == 202:
        bits.append("accepted (async job)")
    bits.append(f"credits charged: {body.get('credits_charged', 0)}")
    if body.get("credits_remaining") is not None:
        bits.append(f"credits remaining: {body['credits_remaining']}")
    if body.get("cached"):
        bits.append(f"cached (free) from {body.get('cached_at')}")
    return " | ".join(bits)


def _page_line(body: dict, data: Any) -> str:
    if not isinstance(data, dict) or data.get("object") != "list":
        return ""
    n = len(data.get("items") or [])
    more = body.get("has_more")
    line = f"{n} items | has_more: {str(bool(more)).lower()}"
    if body.get("cursor"):
        line += f" | next cursor: {body['cursor']} (pass it back as `cursor` for the next page; each page costs credits)"
    return line
