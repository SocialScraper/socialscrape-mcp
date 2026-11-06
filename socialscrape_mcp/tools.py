"""MCP tools, built from the catalog.

Agents cope badly with hundreds of tools, so the catalog is grouped:

* one tool per platform (`github`, `facebook`, ...) with a
  `resource` argument that picks the data (`user`, `profile.videos`, ...);
* a few cross-platform tools for the jobs agents do most: `get_transcript`,
  `search`, `get_profile`, `get_post`, `get_comments`;
* `describe` (free, no API call) for exact parameters, `call_endpoint` for any
  endpoint by id, and the account tools (`get_credits`, `get_job`, `batch`,
  `monitors`).

Which tools exist depends only on what is in the catalog, so a platform appears
when its first endpoint leaves `stub` and the next regeneration picks it up.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from .catalog import Catalog, Endpoint, Param
from .client import ApiClient
from .render import compact, error_result, render_response, result
from .settings import Settings

TOOLSETS = ("core", "platforms")
STANDARD_DESC = {
    "handle": "Username, with or without the leading @.",
    "url": "URL of the item the resource is about (profile, post, video, event...).",
    "id": "The platform's id for the item, where a URL is not used.",
    "query": "Search terms.",
    "cursor": "Cursor from the previous page; pass it back unchanged.",
    "limit": "Upper bound on items returned.",
    "sort": "Order of results; changing it restarts the cursor chain.",
    "region": "Two-letter country code.",
    "language": "Language code, e.g. en.",
    "max_age_days": "Accept a cached copy fetched within this many days, for 0 credits (0 to 30).",
}
STANDARD_FLAT = ("handle", "url", "id", "query", "cursor", "limit", "sort", "region", "language", "max_age_days")
OBJECT_ARGS = ("resource", "params")
HINT_ARGS = ("limit", "sort", "region", "language")
MONITOR_ACTIONS = {
    "create": "monitors.post", "list": "monitors", "delete": "monitors.by_id.delete",
    "test": "monitors.by_id.test.post", "deliveries": "monitors.by_id.deliveries",
    "events": "monitors.events", "redeliver": "monitors.events.by_id.redeliver.post",
}


class ToolInputError(Exception):
    """The caller's arguments are wrong; the message tells them how to fix it."""


@dataclass(frozen=True)
class ToolFilter:
    """Which tools a connection sees. `platforms` limits platform tools (and the
    platform choices of cross-platform tools); None means all."""

    platforms: frozenset[str] | None = None
    toolsets: frozenset[str] = frozenset(TOOLSETS)

    @classmethod
    def parse(cls, platforms: str | None = None, toolsets: str | None = None) -> "ToolFilter":
        plats = frozenset(p.strip().lower().replace("-", "_") for p in (platforms or "").split(",") if p.strip())
        sets = frozenset(s.strip().lower() for s in (toolsets or "").split(",") if s.strip())
        if "all" in sets or not sets:
            sets = frozenset(TOOLSETS)
        return cls(plats or None, sets & frozenset(TOOLSETS) or frozenset(TOOLSETS))

    def allows_platform(self, key: str) -> bool:
        return self.platforms is None or key in self.platforms


@dataclass
class CallContext:
    client: ApiClient
    settings: Settings
    api_key: str | None


@dataclass
class Tool:
    name: str
    title: str
    description: str
    input_schema: dict[str, Any]
    toolset: str
    run: Callable[[dict[str, Any], CallContext], dict[str, Any]]
    read_only: bool = True

    def listing(self) -> dict[str, Any]:
        return {
            "name": self.name, "title": self.title, "description": self.description,
            "inputSchema": self.input_schema,
            "annotations": {"title": self.title, "readOnlyHint": self.read_only, "destructiveHint": False,
                            "idempotentHint": self.read_only, "openWorldHint": True},
        }


# ------------------------------------------------------------------ arguments


def _clean(args: dict[str, Any]) -> dict[str, Any]:
    """Models send nulls and empty strings for what they do not use."""
    return {k: v for k, v in args.items() if v is not None and v != ""}


def _merge(args: dict[str, Any], drop: tuple[str, ...]) -> dict[str, Any]:
    flat = {k: v for k, v in _clean(args).items() if k not in drop and k != "params"}
    extra = args.get("params")
    if extra is not None and not isinstance(extra, dict):
        raise ToolInputError("`params` must be an object such as {\"start_date\": \"2026-01-01\"}")
    for k, v in _clean(extra or {}).items():
        flat.setdefault(k, v)
    return flat


def _coerce(p: Param, v: Any) -> Any:
    if isinstance(v, str):
        s = v.strip()
        try:
            if p.type == "integer":
                return int(s)
            if p.type == "number":
                f = float(s)
                return int(f) if f.is_integer() else f
        except ValueError:
            return v
        if p.type == "boolean" and s.lower() in ("true", "false"):
            return s.lower() == "true"
        if p.type in ("array", "object"):
            try:
                return json.loads(s)
            except ValueError:
                return v
    if p.type == "number" and isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def prepare(ep: Endpoint, given: dict[str, Any], settings: Settings) -> tuple[dict, Any, dict]:
    """Check `given` against the endpoint and split it into (query, body, path params)."""
    known: dict[str, Any] = {}
    for name, value in given.items():
        p = ep.param(name)
        if p is None:
            names = ", ".join(q.name for q in ep.params if not q.common) or "none"
            raise ToolInputError(f"{ep.id} has no parameter `{name}`. Its parameters: {names} "
                                 "(plus trim, raw, max_age_days).")
        known[p.name] = _coerce(p, value)
    missing = [p.name for p in ep.params if p.required and known.get(p.name) in (None, "")]
    if missing:
        raise ToolInputError(f"{ep.id} needs: {', '.join(missing)}.")
    for group in ep.one_of:
        if not any(known.get(n) not in (None, "") for n in group):
            raise ToolInputError(f"{ep.id} needs one of: {' or '.join(group)}.")
    if "trim" not in known and settings.trim and ep.param("trim") is not None:
        known["trim"] = True
    query: dict[str, Any] = {}
    body: dict[str, Any] = {}
    path_params: dict[str, str] = {}
    for name, value in known.items():
        loc = ep.param(name).location  # type: ignore[union-attr]
        if loc == "path":
            path_params[name] = str(value)
        elif loc == "body":
            body[name] = value
        else:
            query[name] = value
    return query, (body if body or ep.method == "POST" else None), path_params


def run_endpoint(ep: Endpoint, given: dict[str, Any], ctx: CallContext, cat: Catalog) -> dict[str, Any]:
    if not ctx.api_key:
        return error_result("no API key. Set SOCIALSCRAPE_API_KEY (stdio) or send the x-api-key header (HTTP mode). "
                            "Get a key at " + cat.api["dashboard_url"], code="unauthorized", cat=cat)
    try:
        query, body, path_params = prepare(ep, given, ctx.settings)
    except ToolInputError as e:
        return error_result(str(e), code="invalid_params", cat=cat)
    resp = ctx.client.request(ep.method, ep.path, api_key=ctx.api_key, query=query, body=body,
                              path_params=path_params)
    return render_response(resp, cat, max_chars=ctx.settings.max_chars)


# ------------------------------------------------------------------ schemas and text


def _flat_properties(eps: list[Endpoint]) -> dict[str, dict[str, Any]]:
    """Top-level arguments of a platform tool: the standard names plus any
    parameter two or more of its resources share, when their types agree.
    Everything else goes in `params`."""
    seen: dict[str, list[tuple[Endpoint, Param]]] = {}
    for ep in eps:
        for p in ep.own_params:
            seen.setdefault(p.name, []).append((ep, p))
    props: dict[str, dict[str, Any]] = {}
    for name, uses in seen.items():
        if name not in STANDARD_FLAT and len(uses) < 2:
            continue
        if len({p.type for _, p in uses}) != 1:
            continue
        first = uses[0][1]
        schema = first.json_schema()
        enums = [set(p.enum) for _, p in uses if p.enum]
        if len(enums) == len(uses):
            allowed = sorted(set().union(*enums))
            schema["enum"] = allowed
        else:
            schema.pop("enum", None)
        texts = {p.description for _, p in uses}
        desc = first.description.rstrip(".") if len(texts) == 1 else STANDARD_DESC.get(name, first.description).rstrip(".")
        if len(uses) < len(eps) and name not in ("cursor", "max_age_days"):
            shown = ", ".join(e.resource for e, _ in uses[:6]) + (", ..." if len(uses) > 6 else "")
            desc += f". Used by: {shown}"
        if any(p.enum for _, p in uses) and len({p.enum for _, p in uses}) > 1:
            desc += ". Allowed values vary by resource (describe shows them)"
        schema["description"] = desc
        props[name] = schema
    return props


def _resource_line(cat: Catalog, ep: Endpoint, flat: set[str]) -> str:
    sig = ep.signature()
    in_sig = {n for g in ep.one_of for n in g}
    extras = [p.name for p in ep.own_params if not p.required and p.name not in in_sig and p.name != "cursor"
              and p.name not in {q for q in flat if q in STANDARD_FLAT}]
    line = f"- {ep.resource}({sig}): {ep.summary}. {cat.credit_text(ep)}."
    if ep.paginated:
        line += " Paged."
    if extras:
        line += " Optional: " + ", ".join(extras[:7]) + (", ..." if len(extras) > 7 else "") + "."
    return line


def _platform_tool(cat: Catalog, key: str, eps: list[Endpoint]) -> Tool:
    group = cat.group(key)
    assert group is not None
    flat = _flat_properties(eps)
    resources = [e.resource for e in eps]
    props: dict[str, Any] = {
        "resource": {"type": "string", "enum": resources,
                     "description": f"Which {group.title} data to fetch. The tool description lists what each needs."},
        **flat,
        "max_age_days": {"type": "number", "minimum": 0, "maximum": 30, "description": STANDARD_DESC["max_age_days"]},
        "params": {"type": "object", "additionalProperties": True,
                   "description": "Any other parameter for the chosen resource, by name, e.g. {\"start_date\": "
                                  "\"2026-01-01\"}. Optional parameters of each resource are in the tool description; "
                                  "call describe for types and allowed values."},
    }
    desc = [
        group.description,
        "",
        "Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the "
        "credits shown below and the result says what was charged and what is left; failures are free. List "
        "resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached "
        "copy for free.",
        "",
        "Resources:",
        *[_resource_line(cat, e, set(flat)) for e in eps],
    ]
    schema = {"type": "object", "properties": props, "required": ["resource"], "additionalProperties": True}

    def run(args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        name = args.get("resource")
        ep = next((e for e in eps if e.resource == name), None)
        if ep is None:
            return error_result(f"unknown resource {name!r} for {key}. Choose one of: {', '.join(resources)}.", cat=cat)
        try:
            given = _merge(args, OBJECT_ARGS)
        except ToolInputError as e:
            return error_result(str(e), cat=cat)
        return run_endpoint(ep, given, ctx, cat)

    return Tool(key, group.title, "\n".join(desc), schema, "platforms", run)


# ------------------------------------------------------------------ cross-platform tools


def _role_tool(cat: Catalog, filt: ToolFilter, *, name: str, title: str, role: str, blurb: str,
               props: dict[str, Any], required: tuple[str, ...] = ("platform",)) -> Tool | None:
    table = cat.roles.get(role, {})
    keys = [k for k in table if filt.allows_platform(k)]
    if not keys:
        return None
    titles = {g.key: g.title for g in cat.groups}
    schema = {
        "type": "object",
        "properties": {
            "platform": {"type": "string", "enum": keys, "description": "Which platform."},
            **props,
            "params": {"type": "object", "additionalProperties": True,
                       "description": "Any other parameter of the underlying endpoint (call describe)."},
        },
        "required": list(required), "additionalProperties": True,
    }
    where = ", ".join(f"{titles[k]}" for k in keys)
    prices = set()
    for k in keys:
        entry = table[k]
        for eid in ([entry] if isinstance(entry, str) else entry["kinds"].values()):
            prices.add(cat.credit_text(cat.by_id[eid]))
    price = next(iter(prices)) if len(prices) == 1 else "price depends on the platform (describe shows it)"
    desc = f"{blurb} Platforms: {where}. Price: {price} per call (failures free, cached repeats free with max_age_days). " \
           "For anything beyond this, use the platform's own tool."

    def run(args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        plat = args.get("platform")
        if plat not in keys:
            return error_result(f"platform must be one of: {', '.join(keys)}.", cat=cat)
        entry = table[plat]
        eid = entry if isinstance(entry, str) else _search_target(entry, args)
        if eid is None:
            kinds = ", ".join(entry["kinds"])
            return error_result(f"kind must be one of: {kinds}.", cat=cat)
        try:
            given = _merge(args, ("platform", "kind", *OBJECT_ARGS))
        except ToolInputError as e:
            return error_result(str(e), cat=cat)
        target = cat.by_id[eid]
        # The shared schema offers limit/sort/region/language to every platform; most endpoints take only some.
        # They only shape a result, so one a platform lacks is dropped (and said so) instead of failing the call.
        ignored = [h for h in HINT_ARGS if h in given and target.param(h) is None]
        for h in ignored:
            del given[h]
        out = run_endpoint(target, given, ctx, cat)
        if ignored and not out.get("isError"):
            note = f"ignored (not supported by {target.id}): {', '.join(ignored)}"
            out["content"][0]["text"] = out["content"][0]["text"].replace("\n", f"\n{note}\n", 1)
            out.setdefault("structuredContent", {})["ignored"] = ignored
        return out

    return Tool(name, title, desc, schema, "core", run)


def _search_target(entry: dict, args: dict[str, Any]) -> str | None:
    kind = args.get("kind") or entry["default"]
    return entry["kinds"].get(kind)


def _search_tool(cat: Catalog, filt: ToolFilter) -> Tool | None:
    table = {k: v for k, v in cat.roles.get("search", {}).items() if filt.allows_platform(k)}
    kinds = sorted({k for v in table.values() for k in v["kinds"]})
    if not table:
        return None
    t = _role_tool(cat, filt, name="search", title="Search a platform", role="search",
                   blurb="Search one platform for posts, videos, users or other items by keyword.",
                   props={
                       "query": {"type": "string", "description": "Search terms."},
                       "kind": {"type": "string", "enum": kinds,
                                "description": "What to search, when the platform has several (search.users, "
                                               "search.posts, ...). Defaults to the platform's main search."},
                       "cursor": {"type": "string", "description": "Cursor from the previous page."},
                       "limit": {"type": "integer", "minimum": 1, "description": "Upper bound on items returned."},
                       "sort": {"type": "string", "description": "Order, where the platform supports it."},
                       "region": {"type": "string", "description": "Two-letter country code, where supported."},
                   }, required=("platform", "query"))
    if t is not None:
        extra = "; ".join(f"{k}: {', '.join(v['kinds'])}" for k, v in table.items() if len(v["kinds"]) > 1)
        if extra:
            t.description += f" Kinds per platform: {extra}."
    return t


def _transcript_tool(cat: Catalog) -> Tool | None:
    ep = cat.by_id.get("transcript")
    if ep is None:
        return None
    price = cat.credit_text(ep)
    schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "format": "uri",
                    "description": "Link to the video or post: YouTube, TikTok, Instagram, X, Facebook, LinkedIn, "
                                   "Reddit, Twitch or Kick clips, Rumble."},
            "language": {"type": "string", "description": "Preferred language code such as en. Optional."},
            "include_timestamps": {"type": "boolean", "default": False,
                                   "description": "Also return segments with start times. Doubles the size; "
                                                  "leave off unless you need timings."},
            "offset": {"type": "integer", "minimum": 0, "default": 0,
                       "description": "Character offset to continue a long transcript from (use next_offset from the "
                                      "previous answer). Continuations are served from cache for free."},
            "max_chars": {"type": "integer", "minimum": 1000,
                          "description": "Longest piece of text to return in one answer."},
            "allow_long_transcription": {"type": "boolean", "default": False,
                                         "description": "Transcribe audio past 2 minutes with AI, at 5 credits per "
                                                        "started minute of the whole video (10 minutes = 50). Without "
                                                        "it, such a video with no captions answers transcript_unavailable "
                                                        "for free. Ask before spending this on a long video."},
        },
        "required": ["url"],
    }
    desc = ("Get the transcript of a video or audio post from its URL. The platform is detected from the link. "
            "Uses the platform's captions when they exist and falls back to AI transcription of the audio. "
            f"Price: {price}. Returns text, language, source (captions | auto_captions | ai) and duration. "
            "Long transcripts come back in pieces: when `text_window.next_offset` is set, call again with that offset.")

    def run(args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        given = {k: v for k, v in _clean(args).items() if k in ("url", "language", "max_age_days", "allow_long_transcription")}
        try:
            offset = int(args.get("offset") or 0)
            max_chars = int(args.get("max_chars") or 0)
        except (TypeError, ValueError):
            return error_result("`offset` and `max_chars` must be whole numbers.", cat=cat)
        if offset < 0 or max_chars < 0:
            return error_result("`offset` and `max_chars` cannot be negative.", cat=cat)
        if offset > 0:
            given.setdefault("max_age_days", 30)  # the first call cached it; reading on should not charge again
        out = run_endpoint(ep, given, ctx, cat)
        data = (out.get("structuredContent") or {}).get("data")
        if out.get("isError") or not isinstance(data, dict) or not isinstance(data.get("text"), str):
            return out
        limit = max_chars or ctx.settings.max_chars
        text = data["text"]
        window = {"offset": offset, "returned": len(text[offset:offset + limit]), "total_chars": len(text),
                  "next_offset": offset + limit if offset + limit < len(text) else None}
        shaped = dict(data)
        shaped["text"] = text[offset:offset + limit]
        if not args.get("include_timestamps"):
            shaped.pop("segments", None)
        elif offset or window["next_offset"]:
            shaped.pop("segments", None)  # segments cannot be windowed with the text; ask without a window
            window["note"] = "segments omitted for a windowed transcript"
        shaped["text_window"] = window
        structured = dict(out["structuredContent"], data=shaped)
        head = out["content"][0]["text"].split("\n", 1)[0]
        extra = f"\ntext {offset}-{offset + window['returned']} of {window['total_chars']} characters"
        if window["next_offset"] is not None:
            extra += f"; more: call again with offset={window['next_offset']}"
        return result(head + extra + "\n" + compact(shaped), structured)

    return Tool("get_transcript", "Get a transcript", desc, schema, "core", run)


def example_id(cat: Catalog, *, paginated: bool = False) -> str:
    """An endpoint id to use in descriptions, taken from what is built (never a hand-kept name)."""
    for role in ("search", "profile"):
        for entry in cat.roles.get(role, {}).values():
            eid = entry if isinstance(entry, str) else entry["kinds"][entry["default"]]
            if cat.by_id[eid].paginated == paginated:
                return eid
    return next((e.id for e in cat.endpoints if e.kind == "platform" and e.paginated == paginated), "platform.resource")


def _call_tool(cat: Catalog) -> Tool:
    ids = [e.id for e in cat.endpoints if e.kind in ("platform", "router") and e.method == "GET"]
    schema = {
        "type": "object",
        "properties": {
            "endpoint": {"type": "string", "description": f"Endpoint id as describe prints it, e.g. {example_id(cat)}."},
            "params": {"type": "object", "additionalProperties": True,
                       "description": "Parameters by name, as in describe's example arguments."},
        },
        "required": ["endpoint"],
    }
    desc = (f"Run any SocialScrape data endpoint by its id (for example `{example_id(cat)}`). Same behaviour and "
            "price as the platform tools; use it when you already know the id, or when only the core tools are "
            f"enabled. {len(ids)} endpoints; call describe to list them.")

    def run(args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        ep = resolve(cat, str(args.get("endpoint") or ""))
        if ep is None or ep.id not in ids:
            return error_result(f"unknown endpoint {args.get('endpoint')!r}. Call describe to list endpoint ids.", cat=cat)
        try:
            given = _merge({"params": args.get("params")}, ())
        except ToolInputError as e:
            return error_result(str(e), cat=cat)
        return run_endpoint(ep, given, ctx, cat)

    return Tool("call_endpoint", "Call any endpoint", desc, schema, "core", run)


def resolve(cat: Catalog, name: str) -> Endpoint | None:
    """An endpoint by id, or by 'group.resource' / 'group/resource' as the platform tools name it."""
    name = name.strip().strip("/")
    if name in cat.by_id:
        return cat.by_id[name]
    for sep in (".", "/", ":"):
        if sep in name:
            g, r = name.split(sep, 1)
            g = g.replace("-", "_")
            hit = cat.find(g, r.replace("-", "."))  or cat.find(g, r)
            if hit:
                return hit
    return None


# ------------------------------------------------------------------ describe (no API call)


def _param_line(p: Param) -> str:
    bits = [f"{p.name} ({p.type}{', required' if p.required else ''})"]
    bits.append(p.description.rstrip("."))
    if p.enum:
        bits.append("one of: " + ", ".join(p.enum))
    if p.hosts:
        bits.append("host: " + ", ".join(p.hosts))
    if p.minimum is not None or p.maximum is not None:
        bits.append(f"range {p.minimum if p.minimum is not None else ''}..{p.maximum if p.maximum is not None else ''}")
    if p.aliases:
        bits.append("also accepted as: " + ", ".join(p.aliases[:4]))
    return "- " + "; ".join(bits)


def _returns(cat: Catalog, ep: Endpoint) -> str:
    inner = ep.response.split("[")[-1].rstrip("]").split(" | ")[0]
    fields = cat.models.get(inner)
    return f"returns: {ep.response}" + (f" with fields {', '.join(fields)}" if fields else "")


def describe_endpoint(cat: Catalog, ep: Endpoint) -> tuple[str, dict]:
    where = f"tool: {ep.group}  resource: {ep.resource}" if ep.kind == "platform" else "tool: call_endpoint or the account tools"
    price = f"price: {cat.credit_text(ep)}" + (" | paged (cursor)" if ep.paginated else "") \
        + (" | async job: poll get_job" if ep.mode == "async" else "")
    lines = [f"{ep.id}: {ep.summary}", where, price, _returns(cat, ep)]
    if ep.description:
        lines.append(ep.description)
    if ep.one_of:
        lines.append("needs one of: " + "; ".join(" or ".join(g) for g in ep.one_of))
    lines.append("parameters:")
    lines += [_param_line(p) for p in ep.params if not p.common] or ["- none"]
    lines.append("also: trim (default on here), raw (add the platform's original object), max_age_days (free cached copy)")
    if ep.examples:
        lines.append("example arguments: " + compact(ep.examples[0]))
    info = {"id": ep.id, "group": ep.group, "resource": ep.resource, "summary": ep.summary, "response": ep.response,
            "paginated": ep.paginated, "price": cat.credit_text(ep), "one_of": [list(g) for g in ep.one_of],
            "params": [{"name": p.name, "type": p.type, "required": p.required, "description": p.description,
                        **({"enum": list(p.enum)} if p.enum else {})} for p in ep.params if not p.common],
            "examples": list(ep.examples)}
    return "\n".join(lines), info


def _describe_tool(cat: Catalog, filt: ToolFilter) -> Tool:
    keys = [g.key for g in cat.groups if filt.allows_platform(g.key)]
    schema = {
        "type": "object",
        "properties": {
            "platform": {"type": "string", "description": "A platform tool name such as github. Omit to list "
                                                          "them all."},
            "resource": {"type": "string", "description": "A resource of that platform. Omit to list its resources."},
            "endpoint": {"type": "string", "description": f"Or an endpoint id such as {example_id(cat, paginated=True)}."},
        },
    }
    desc = ("Look up what SocialScrape can fetch, with exact parameters, allowed values, price and example arguments. "
            "Free and instant (no API call, no credits). With no arguments it lists every platform; with `platform` "
            "its resources; with `platform` and `resource` (or `endpoint`) the full parameter list.")

    def run(args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        a = _clean(args)
        if "endpoint" in a or ("platform" in a and "resource" in a):
            ep = resolve(cat, a["endpoint"]) if "endpoint" in a else cat.find(str(a["platform"]).replace("-", "_"),
                                                                              str(a["resource"]))
            if ep is None:
                return error_result("no such endpoint. Call describe with just `platform` to list its resources.", cat=cat)
            text, info = describe_endpoint(cat, ep)
            return result(text, info)
        if "platform" in a:
            key = str(a["platform"]).replace("-", "_")
            g = cat.group(key)
            if g is None or not filt.allows_platform(key):
                return error_result(f"unknown platform {a['platform']!r}. Known: {', '.join(keys)}.", cat=cat)
            eps = cat.group_endpoints(key)
            lines = [f"{g.title}: {g.description}"]
            lines += [f"- {e.resource}({e.signature()}): {e.summary}. {cat.credit_text(e)}. Returns {e.response}."
                      for e in eps]
            return result("\n".join(lines), {"platform": key, "resources": [
                {"resource": e.resource, "id": e.id, "summary": e.summary, "needs": e.signature(),
                 "price": cat.credit_text(e), "returns": e.response} for e in eps]})
        rows = []
        for g in cat.groups:
            if not filt.allows_platform(g.key):
                continue
            eps = cat.group_endpoints(g.key)
            rows.append({"platform": g.key, "title": g.title, "resources": [e.resource for e in eps]})
        lines = [f"{r['platform']} ({r['title']}): {', '.join(r['resources'])}" for r in rows]
        lines.append("Cross-platform: get_transcript, search, get_profile, get_post, get_comments; account: get_credits, "
                     "get_job, batch, monitors. Call describe with a platform for details.")
        return result("\n".join(lines), {"platforms": rows})

    return Tool("describe", "Describe endpoints", desc, schema, "core", run)


# ------------------------------------------------------------------ account tools


def _credits_tool(cat: Catalog) -> Tool | None:
    ep = cat.by_id.get("account.credits")
    if ep is None:
        return None
    schema = {"type": "object", "properties": {}}

    def run(args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        return run_endpoint(ep, {}, ctx, cat)

    return Tool("get_credits", "Check credit balance", "Show how many credits the API key's team has left. Free.",
                schema, "core", run)


def _job_tool(cat: Catalog) -> Tool | None:
    ep = cat.by_id.get("jobs.by_id")
    if ep is None:
        return None
    schema = {"type": "object", "properties": {"job_id": {"type": "string", "description": "The job_id from an "
              "accepted (still running) answer."}}, "required": ["job_id"]}

    def run(args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        return run_endpoint(ep, _clean(args), ctx, cat)

    return Tool("get_job", "Poll a job", "Fetch the result of a request that answered 'accepted' (long jobs such as AI "
                "transcription of a long video). Polling is free; the credit charge happens once, when the job "
                "finishes. If it is still running, wait a few seconds and call again.", schema, "core", run)


def _batch_tool(cat: Catalog) -> Tool | None:
    ep = cat.by_id.get("batch.post")
    if ep is None:
        return None
    limit = 100
    schema = {
        "type": "object",
        "properties": {"requests": {"type": "array", "minItems": 1, "maxItems": limit, "items": {
            "type": "object", "properties": {
                "endpoint": {"type": "string", "description": f"Endpoint id, e.g. {example_id(cat)}."},
                "params": {"type": "object", "additionalProperties": True}},
            "required": ["endpoint"]}, "description": f"Up to {limit} data requests."}},
        "required": ["requests"],
    }
    desc = (f"Run up to {limit} data requests in one call (for example the profile of 30 accounts). Each item is charged "
            "like a single request and failures inside the batch are free; one failing item does not fail the others. "
            "The answer has one result per item, in order.")

    def run(args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        reqs = args.get("requests")
        if not isinstance(reqs, list) or not reqs:
            return error_result("`requests` must be a non-empty list of {endpoint, params}.", cat=cat)
        wire = []
        for i, item in enumerate(reqs):
            target = resolve(cat, str(item.get("endpoint") or "")) if isinstance(item, dict) else None
            if target is None or target.method != "GET" or target.kind == "native":
                return error_result(f"requests[{i}].endpoint is not a data endpoint. Call describe for ids.", cat=cat)
            try:
                query, _, _ = prepare(target, _clean(item.get("params") or {}), ctx.settings)
            except ToolInputError as e:
                return error_result(f"requests[{i}]: {e}", cat=cat)
            wire.append({"path": target.path, "params": query})
        return run_endpoint(ep, {"requests": wire}, ctx, cat)

    return Tool("batch", "Batch requests", desc, schema, "core", run)


def _monitors_tool(cat: Catalog) -> Tool | None:
    actions = {a: cat.by_id[i] for a, i in MONITOR_ACTIONS.items() if i in cat.by_id}
    if "create" not in actions:
        return None
    schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": list(actions), "description": "What to do."},
            "endpoint": {"type": "string", "description": "create: the list endpoint to watch, by id "
                                                           f"(e.g. {example_id(cat, paginated=True)})."},
            "params": {"type": "object", "additionalProperties": True, "description": "create: that endpoint's parameters."},
            "webhook_url": {"type": "string", "format": "uri", "description": "create: https URL that receives signed events."},
            "interval_minutes": {"type": "integer", "minimum": 1, "description": "create: how often to check."},
            "monitor_id": {"type": "string", "description": "delete, test, deliveries; optional filter for events."},
            "event_id": {"type": "string", "description": "redeliver: the event to send again."},
        },
        "required": ["action"],
    }
    desc = ("Watch a list (a profile's posts, a search) and have SocialScrape POST new items to your webhook, signed. "
            "Actions: create, list, delete, test (send a signed test event), deliveries (delivery log), events, "
            "redeliver. Each scheduled check is charged like a normal request to the watched endpoint; creating, "
            "listing and deleting are free. The first check only records a baseline. The create answer shows the "
            "webhook secret once: tell the user to store it.")

    def run(args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        action = args.get("action")
        ep = actions.get(str(action))
        if ep is None:
            return error_result(f"action must be one of: {', '.join(actions)}.", cat=cat)
        a = _clean(args)
        if action == "create":
            target = resolve(cat, str(a.get("endpoint") or ""))
            if target is None or not target.paginated:
                return error_result("`endpoint` must be a list endpoint id (a paged one); call describe.", cat=cat)
            given = {"endpoint": target.path, "params": a.get("params") or {}}
            for k in ("webhook_url", "interval_minutes"):
                if k in a:
                    given[k] = a[k]
            return run_endpoint(ep, given, ctx, cat)
        given = {k: v for k, v in a.items() if k in ("monitor_id", "event_id")}
        return run_endpoint(ep, given, ctx, cat)

    return Tool("monitors", "Monitors and webhooks", desc, schema, "core", run, read_only=False)


# ------------------------------------------------------------------ the list


def build_tools(cat: Catalog, filt: ToolFilter | None = None) -> list[Tool]:
    filt = filt or ToolFilter()
    tools: list[Tool] = []
    if "core" in filt.toolsets:
        core: list[Tool | None] = [
            _transcript_tool(cat),
            _search_tool(cat, filt),
            _role_tool(cat, filt, name="get_profile", title="Get a profile", role="profile",
                       blurb="Get a profile (name, bio, follower counts, links) by handle or URL.",
                       props={"handle": {"type": "string", "description": "Username, with or without @."},
                              "url": {"type": "string", "format": "uri", "description": "Profile URL, instead of handle."}},
                       required=("platform",)),
            _role_tool(cat, filt, name="get_post", title="Get a post", role="post",
                       blurb="Get one post, video, tweet, pin or clip by URL: text, author, stats, media.",
                       props={"url": {"type": "string", "format": "uri", "description": "Link to the post."},
                              "id": {"type": "string", "description": "The platform's id, where URLs are not used."}}),
            _role_tool(cat, filt, name="get_comments", title="Get comments", role="comments",
                       blurb="Get a page of comments on a post or video.",
                       props={"url": {"type": "string", "format": "uri", "description": "Link to the post."},
                              "id": {"type": "string", "description": "The platform's id for the post."},
                              "cursor": {"type": "string", "description": "Cursor from the previous page."},
                              "limit": {"type": "integer", "minimum": 1, "description": "Upper bound on items."}}),
            _describe_tool(cat, filt),
            _call_tool(cat),
            _credits_tool(cat),
            _job_tool(cat),
            _batch_tool(cat),
            _monitors_tool(cat),
        ]
        tools += [t for t in core if t is not None]
    if "platforms" in filt.toolsets:
        for g in cat.groups:
            if not filt.allows_platform(g.key):
                continue
            eps = cat.group_endpoints(g.key)
            if eps:
                tools.append(_platform_tool(cat, g.key, eps))
    names = [t.name for t in tools]
    assert len(names) == len(set(names)), "tool names must be unique"
    return tools
