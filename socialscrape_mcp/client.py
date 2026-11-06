"""A small synchronous client for the SocialScrape API.

One job: send a request with the caller's key and hand back the envelope.
It never raises for an API failure (the envelope carries the error); a
network failure becomes a synthetic, retryable error envelope with the same
shape, so callers have one path to handle.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import quote

import httpx

from . import __version__

DEFAULT_API_URL = "https://api.socialscrape.dev"
USER_AGENT = f"socialscrape-mcp/{__version__}"


@dataclass
class ApiResponse:
    status: int
    body: dict[str, Any]
    headers: dict[str, str]

    @property
    def ok(self) -> bool:
        return bool(self.body.get("ok"))


def wire_value(v: Any) -> Any:
    """Query strings carry text: booleans as true/false."""
    if isinstance(v, bool):
        return "true" if v else "false"
    return v


class ApiClient:
    def __init__(self, base_url: str = DEFAULT_API_URL, *, http: httpx.Client | None = None, timeout: float = 70.0,
                 sleep: Callable[[float], None] = time.sleep, max_retry_wait: float = 5.0,
                 user_agent: str = USER_AGENT):
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self._owns_http = http is None
        self.http = http or httpx.Client(timeout=timeout)
        self._sleep = sleep
        self.max_retry_wait = max_retry_wait

    def close(self) -> None:
        if self._owns_http:
            self.http.close()

    def request(self, method: str, path: str, *, api_key: str | None, query: dict[str, Any] | None = None,
                body: Any = None, path_params: dict[str, str] | None = None) -> ApiResponse:
        for name, value in (path_params or {}).items():
            path = path.replace("{" + name + "}", quote(str(value), safe=""))
        headers = {"x-api-key": api_key or "", "user-agent": self.user_agent, "accept": "application/json"}
        params = {k: wire_value(v) for k, v in (query or {}).items() if v is not None}
        attempts = 0
        while True:
            attempts += 1
            resp = self._send(method, path, headers, params, body)
            err = resp.body.get("error") or {}
            if err.get("code") == "rate_limited" and attempts == 1:
                wait = _retry_after(resp.headers)
                if wait is not None and wait <= self.max_retry_wait:
                    self._sleep(wait)  # a failure is free, so one polite retry costs nothing
                    continue
            return resp

    def _send(self, method: str, path: str, headers: dict, params: dict, body: Any) -> ApiResponse:
        try:
            r = self.http.request(method, self.base_url + path, headers=headers, params=params or None,
                                  json=body if body is not None else None)
        except httpx.TimeoutException:
            return _synthetic(504, "upstream_timeout", "the request to the SocialScrape API timed out", True)
        except httpx.HTTPError as e:
            return _synthetic(502, "upstream_error", f"could not reach the SocialScrape API: {type(e).__name__}", True)
        try:
            data = r.json()
        except (json.JSONDecodeError, ValueError):
            data = None
        if not isinstance(data, dict):
            return _synthetic(r.status_code if r.status_code >= 400 else 502, "upstream_error",
                              f"the API answered HTTP {r.status_code} with a body that is not JSON", True)
        return ApiResponse(r.status_code, data, {k.lower(): v for k, v in r.headers.items()})


def _retry_after(headers: dict[str, str]) -> float | None:
    try:
        return float(headers.get("retry-after", ""))
    except ValueError:
        return None


def _synthetic(status: int, code: str, message: str, retryable: bool) -> ApiResponse:
    return ApiResponse(status, {"ok": False, "error": {"code": code, "message": message, "retryable": retryable},
                                "credits_charged": 0, "request_id": None}, {})
