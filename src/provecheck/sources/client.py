"""One HTTP client for every resolver: timeout, polite User-Agent, on-disk cache, offline mode."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from provecheck import __version__

USER_AGENT = f"provecheck/{__version__} (+https://github.com/enestanerr/prove)"
TIMEOUT = 15
MAX_BYTES = 2_000_000
DEFAULT_CACHE = ".provecheck-cache"


@dataclass(frozen=True)
class Response:
    url: str
    status: int | None  # None: no answer (timeout, DNS failure, refused, offline)
    body: str = ""
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.status is not None and 200 <= self.status < 300

    @property
    def missing(self) -> bool:
        return self.status in (404, 410)

    def json(self) -> dict | None:
        try:
            data = json.loads(self.body)
        except ValueError:
            return None
        return data if isinstance(data, dict) else None


class Client:
    def __init__(self, cache_dir: str | Path | None = None, offline: bool = False) -> None:
        self.cache_dir = Path(cache_dir or DEFAULT_CACHE)
        self.offline = offline
        self.user_agent = os.environ.get("PROVECHECK_USER_AGENT") or USER_AGENT

    def _path(self, url: str) -> Path:
        return self.cache_dir / (hashlib.sha256(url.encode("utf-8")).hexdigest()[:32] + ".json")

    def get(self, url: str, accept: str = "*/*") -> Response:
        """GET with redirects followed. Answers are cached; failures to connect are not."""
        cached = self._path(url)
        if cached.is_file():
            data = json.loads(cached.read_text(encoding="utf-8"))
            return Response(url, data["status"], data["body"])
        if self.offline:
            return Response(url, None, error="offline")
        request = urllib.request.Request(
            url, headers={"User-Agent": self.user_agent, "Accept": accept}
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as reply:
                status, raw = reply.status, reply.read(MAX_BYTES)
                charset = reply.headers.get_content_charset() or "utf-8"
        except urllib.error.HTTPError as exc:
            status, raw, charset = exc.code, exc.read(MAX_BYTES), "utf-8"
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            return Response(url, None, error=str(getattr(exc, "reason", exc)))
        try:
            body = raw.decode(charset, errors="replace")
        except LookupError:
            body = raw.decode("utf-8", errors="replace")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        record = {"url": url, "status": status, "body": body}
        cached.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        return Response(url, status, body)
