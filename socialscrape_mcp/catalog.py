"""The generated catalog (catalog.json), as plain objects.

`catalog.json` is written by `sdks/mcp/generate.py` from the endpoint registry
and holds only endpoints that are built (never stubs). Everything the server
knows about SocialScrape comes from here, so the server needs no import of the
api's own packages and can run in a small image of its own.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

CATALOG_PATH = Path(__file__).with_name("catalog.json")


@dataclass(frozen=True)
class Param:
    name: str
    type: str
    required: bool
    description: str
    location: str = "query"
    enum: tuple[str, ...] | None = None
    default: Any = None
    example: Any = None
    minimum: float | None = None
    maximum: float | None = None
    hosts: tuple[str, ...] | None = None
    aliases: tuple[str, ...] = ()
    common: bool = False

    @classmethod
    def from_dict(cls, d: dict) -> "Param":
        return cls(
            name=d["name"], type=d["type"], required=d["required"], description=d["description"],
            location=d.get("location", "query"), enum=tuple(d["enum"]) if d.get("enum") else None,
            default=d.get("default"), example=d.get("example"), minimum=d.get("minimum"),
            maximum=d.get("maximum"), hosts=tuple(d["hosts"]) if d.get("hosts") else None,
            aliases=tuple(d.get("aliases", ())), common=bool(d.get("common")),
        )

    def json_schema(self) -> dict[str, Any]:
        t = {"url": "string"}.get(self.type, self.type)
        schema: dict[str, Any] = {"type": t}
        if self.type == "url":
            schema["format"] = "uri"
        if self.enum:
            schema["enum"] = list(self.enum)
        if self.minimum is not None:
            schema["minimum"] = self.minimum
        if self.maximum is not None:
            schema["maximum"] = self.maximum
        return schema


@dataclass(frozen=True)
class Endpoint:
    id: str
    method: str
    path: str
    summary: str
    description: str
    kind: str
    status: str
    mode: str
    response: str
    paginated: bool
    credits: str
    one_of: tuple[tuple[str, ...], ...]
    regional: bool
    timeout_seconds: float
    params: tuple[Param, ...]
    examples: tuple[dict, ...]
    group: str
    resource: str

    @classmethod
    def from_dict(cls, d: dict) -> "Endpoint":
        return cls(
            id=d["id"], method=d["method"], path=d["path"], summary=d["summary"], description=d.get("description", ""),
            kind=d["kind"], status=d["status"], mode=d["mode"], response=d["response"], paginated=d["paginated"],
            credits=d["credits"], one_of=tuple(tuple(g) for g in d["one_of"]), regional=d["regional"],
            timeout_seconds=d["timeout_seconds"], params=tuple(Param.from_dict(p) for p in d["params"]),
            examples=tuple(d["examples"]), group=d["group"], resource=d["resource"],
        )

    def param(self, name: str) -> Param | None:
        """A parameter by its name or any alias the api accepts."""
        for p in self.params:
            if p.name == name or name in p.aliases:
                return p
        return None

    @property
    def own_params(self) -> tuple[Param, ...]:
        """Parameters specific to this endpoint (not trim / raw / max_age_days)."""
        return tuple(p for p in self.params if not p.common)

    def required_names(self) -> list[str]:
        return [p.name for p in self.params if p.required]

    def signature(self) -> str:
        """'handle|url' style: what the caller must supply."""
        parts = [p.name for p in self.params if p.required and p.location != "body"]
        parts += ["|".join(g) for g in self.one_of]
        return ", ".join(parts)


@dataclass(frozen=True)
class Group:
    key: str
    title: str
    description: str
    platform_enum: bool


@dataclass
class Catalog:
    api: dict
    credit_rules: dict[str, str]
    errors: dict[str, dict]
    models: dict[str, list[str]]
    groups: list[Group]
    roles: dict[str, dict]
    endpoints: list[Endpoint]
    by_id: dict[str, Endpoint] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.by_id = {e.id: e for e in self.endpoints}

    @classmethod
    def from_dict(cls, d: dict) -> "Catalog":
        return cls(
            api=d["api"], credit_rules=d["credit_rules"], errors=d["errors"], models=d["models"],
            groups=[Group(g["key"], g["title"], g["description"], g["platform_enum"]) for g in d["groups"]],
            roles=d["roles"], endpoints=[Endpoint.from_dict(e) for e in d["endpoints"]],
        )

    def group_endpoints(self, key: str) -> list[Endpoint]:
        return [e for e in self.endpoints if e.group == key]

    def group(self, key: str) -> Group | None:
        return next((g for g in self.groups if g.key == key), None)

    def find(self, group: str, resource: str) -> Endpoint | None:
        for e in self.endpoints:
            if e.group == group and e.resource == resource:
                return e
        return None

    def credit_text(self, ep: Endpoint) -> str:
        """The price in words, from the registry's credit rule."""
        desc = self.credit_rules.get(ep.credits, ep.credits)
        return {"free": "free", "standard": "1 credit", "transcript": "1 credit (captions); AI transcription 1 credit "
                "up to 2 minutes, then 5 per started minute of the whole video", "per_5_items": "1 credit per 5 items",
                "batch": "the sum of its requests"}.get(ep.credits, desc)


@lru_cache(maxsize=1)
def load_catalog(path: str | None = None) -> Catalog:
    return Catalog.from_dict(json.loads(Path(path).read_text() if path else CATALOG_PATH.read_text()))
