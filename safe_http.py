"""Protect SitePulse's remote audit fetches from non-public URL targets.

Checks the target of every redirect as well as the initial URL. DNS rebinding
remains a deployment-level concern, so outbound network policy is recommended.
"""
import ipaddress
import socket
from urllib.parse import urljoin, urlsplit

import requests


_REDIRECTS = {301, 302, 303, 307, 308}
_BLOCKED_SUFFIXES = (".localhost", ".local", ".internal", ".test", ".invalid")


def is_public_url(url):
    """Permit only HTTP(S) URLs whose currently resolved addresses are public."""
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
        if parsed.scheme not in ("http", "https") or not host:
            return False
        if parsed.username is not None or parsed.password is not None:
            return False
        if "%" in host or any(ord(c) < 33 for c in host):
            return False
        host = host.rstrip(".").lower()
        if host == "localhost" or host.endswith(_BLOCKED_SUFFIXES):
            return False
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        try:
            literal = ipaddress.ip_address(host)
        except ValueError:
            if "." not in host:
                return False
            literal = None
        if literal is not None and not literal.is_global:
            return False
        resolved = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        return bool(resolved) and all(
            ipaddress.ip_address(address[4][0]).is_global for address in resolved
        )
    except (ValueError, OSError, UnicodeError):
        return False


def guarded_request(method, url, headers=None, timeout=12, max_redirects=5):
    """Request a public page, rejecting private targets on redirect hops."""
    target = url
    history = []
    session = requests.Session()
    session.trust_env = False
    try:
        for attempt in range(max_redirects + 1):
            if not is_public_url(target):
                raise requests.exceptions.InvalidURL(
                    "Audit URL must resolve only to public network addresses"
                )
            response = session.request(
                method, target, headers=headers, timeout=timeout,
                allow_redirects=False,
            )
            location = response.headers.get("Location")
            if response.status_code in _REDIRECTS and location:
                response.close()
                if attempt >= max_redirects:
                    raise requests.exceptions.TooManyRedirects("Too many audit redirects")
                history.append(response)
                target = urljoin(target, location)
                continue
            response.history = history
            return response
        raise requests.exceptions.TooManyRedirects("Too many audit redirects")
    finally:
        session.close()
