"""Mirror the latest verified public feed into a dedicated static directory."""

import argparse
import base64
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

REPO = "adoin/Hongputao-api"
LIMIT = 32_768
VERS = re.compile(r"(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})")
HOSTS = {"github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"}


class ReleaseRedirect(urllib.request.HTTPRedirectHandler):
    max_redirections = 4

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.scheme != "https" or parsed.hostname not in HOSTS or parsed.port not in (None, 443) or parsed.username:
            raise ValueError("Unexpected release asset redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download():
    gh = shutil.which("gh")
    if gh:
        status = subprocess.run([gh, "auth", "status", "--hostname", "github.com"], capture_output=True, timeout=10)
        if status.returncode == 0:
            return subprocess.check_output(
                [gh, "release", "download", "--repo", REPO, "--pattern", "feed.json", "--output", "-"],
                timeout=20, stderr=subprocess.DEVNULL,
            )
        if b"not logged into any GitHub hosts" not in status.stdout + status.stderr:
            raise RuntimeError("GitHub CLI authentication check failed")
    opener = urllib.request.build_opener(ReleaseRedirect())
    request = urllib.request.Request(
        f"https://github.com/{REPO}/releases/latest/download/feed.json",
        headers={"User-Agent": "Hongputao-API-Mirror"},
    )
    with opener.open(request, timeout=12) as response:
        return response.read(LIMIT + 1)


def verified_version(raw):
    if not 0 < len(raw) <= LIMIT:
        raise ValueError("Invalid feed size")
    feed = json.loads(raw)
    version = feed["version"]
    if not VERS.fullmatch(version):
        raise ValueError("Invalid version")
    payload = base64.b64decode(feed["body"], validate=True)
    if not 0 < len(payload) <= 16_384:
        raise ValueError("Invalid package size")
    if feed["digest"] != "sha256:" + hashlib.sha256(payload).hexdigest():
        raise ValueError("Package checksum mismatch")
    package = json.loads(payload)
    if package["schema"] not in (1, 2) or package["version"] != version:
        raise ValueError("Unsupported package or version mismatch")
    return tuple(map(int, version.split(".")))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path, help="Dedicated public feed.json path")
    args = parser.parse_args()
    target = args.destination
    if not target.is_absolute() or target.name != "feed.json" or not target.parent.is_dir():
        raise ValueError("Expected an existing dedicated static directory")
    raw = download()
    version = verified_version(raw)
    if target.exists():
        try:
            installed = verified_version(target.read_bytes())
        except (ValueError, KeyError, TypeError):
            installed = None
        if installed is not None and version <= installed:
            print("API feed already up to date")
            return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as pending:
            temporary = Path(pending.name)
            pending.write(raw)
        temporary.chmod(0o644)
        temporary.replace(target)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
    print("Mirrored API feed " + ".".join(map(str, version)))


if __name__ == "__main__":
    main()
