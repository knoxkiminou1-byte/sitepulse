import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from audit import audit_site  # noqa: E402

WEB_MAX_PAGES = 3
WEB_TIMEOUT = 6
WEB_LINK_CAP = 10
MAX_URL_LEN = 2048


def _json(handler, status, payload):
    body = json.dumps(payload).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        _json(self, 200, {
            "service": "sitepulse-audit",
            "usage": 'POST {"url": "https://example.com"}',
            "limits": {
                "max_pages": WEB_MAX_PAGES,
                "fetch_timeout_s": WEB_TIMEOUT,
                "link_cap": WEB_LINK_CAP,
            },
        })

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > 8192:
            _json(self, 400, {"error": "Send JSON body: {\"url\": \"https://example.com\"}"})
            return
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            _json(self, 400, {"error": "Invalid JSON body."})
            return

        url = (body.get("url") or "").strip()
        if not url or len(url) > MAX_URL_LEN:
            _json(self, 400, {"error": "Provide a URL, e.g. {\"url\": \"https://example.com\"}"})
            return
        parsed = urlparse(url if urlparse(url).scheme else "https://" + url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            _json(self, 400, {"error": "URL must be http(s), e.g. https://example.com"})
            return

        started = time.time()
        try:
            site = audit_site(url, max_pages=WEB_MAX_PAGES,
                              timeout=WEB_TIMEOUT, link_cap=WEB_LINK_CAP)
        except Exception as e:
            _json(self, 502, {"error": "Audit failed: " + type(e).__name__})
            return

        _json(self, 200, {
            "audited_url": site["audited_url"],
            "audited_at": site["audited_at"],
            "engine": site["engine"],
            "pages_crawled": site["pages_crawled"],
            "score": site["score"],
            "grade": site["grade"],
            "counts": site["counts"],
            "elapsed_total": site["elapsed_total"],
            "findings": site["findings"],
            "notes": site["notes"],
            "limits": {
                "max_pages": WEB_MAX_PAGES,
                "note": "Web audits are capped for speed. Run the CLI for deeper crawls.",
            },
            "server_time": round(time.time() - started, 1),
        })

    def log_message(self, *args):
        pass
