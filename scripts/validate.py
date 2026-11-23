"""Validate the API package contract and the release tag."""

import json
import os
import re
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def validate_section(section, keys):
    require(isinstance(section, dict) and set(section) == keys, "invalid fields")
    for key, value in section.items():
        require(isinstance(value, str), f"invalid {key}")
        pattern = r"(?:/[a-zA-Z0-9_-]+)+/?" if key == "path" else r"[a-zA-Z_][a-zA-Z0-9_]{0,31}"
        require(len(value) <= 128 and re.fullmatch(pattern, value), f"invalid {key}")


raw = (Path(__file__).resolve().parents[1] / "hongputao-api.json").read_bytes()
require(len(raw) <= 16_384, "package too large")
data = json.loads(raw)
require(set(data) == {"schema", "version", "search", "recommendations", "playback"}, "invalid package fields")
require(type(data["schema"]) is int and data["schema"] == 1, "unsupported schema")
version = data["version"]
require(isinstance(version, str) and re.fullmatch(r"(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})", version), "invalid version")
validate_section(data["search"], {"path", "keyword", "page", "items", "currentPage", "totalPages", "total"})
validate_section(data["recommendations"], {"path", "series", "group", "items"})
require(data["search"]["keyword"] != data["search"]["page"], "duplicate query fields")
require("aid" not in [data["search"]["keyword"], data["search"]["page"]], "reserved query field")
providers = data["playback"]
require(isinstance(providers, list) and 1 <= len(providers) <= 2, "invalid playback providers")
require(all(value in ("openhongguo", "legacy") for value in providers) and len(set(providers)) == len(providers), "invalid playback providers")
if os.environ.get("GITHUB_REF_TYPE") == "tag":
    require(os.environ.get("GITHUB_REF_NAME") == f"v{version}", "tag must match package version")
print(f"API package {version} validated")
