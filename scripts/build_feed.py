"""Publish an atomic static feed for clients without GitHub CLI."""

import base64
import hashlib
import json
from pathlib import Path

from validate import data, raw

site = Path("_site")
site.mkdir(exist_ok=True)
feed = {
    "version": data["version"],
    "digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
    "body": base64.b64encode(raw).decode("ascii"),
}
(site / "feed.json").write_text(json.dumps(feed, ensure_ascii=False) + "\n", encoding="utf8")
(site / "hongputao-api.json").write_bytes(raw)
