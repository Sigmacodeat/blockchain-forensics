from __future__ import annotations
from urllib.parse import urlparse
import ipaddress
from typing import Iterable


PRIVATE_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
}

LOCAL_TLDS = (".local", ".lan", ".internal", ".intranet")


def _is_private_ip(hostname: str) -> bool:
    try:
        ip = ipaddress.ip_address(hostname)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast
    except ValueError:
        # Not an IP literal
        return False


def _host_matches_allowlist(host: str, allowed_hosts: Iterable[str] | None) -> bool:
    if not allowed_hosts:
        return True
    host = host.lower()
    allowed = {h.lower() for h in allowed_hosts}
    return host in allowed


def is_url_allowed(url: str, *, allowed_hosts: Iterable[str] | None = None) -> bool:
    """
    Lightweight SSRF-Guard: erlaubt nur http(s), blockt private/loopback/link-local IPs,
    blockt localhost/Local-TLDs und optional erzwingt Allowlist-Hosts.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        host = (parsed.hostname or "").strip()
        if not host:
            return False
        # Block obvious locals
        if host in PRIVATE_HOSTNAMES:
            return False
        if any(host.endswith(tld) for tld in LOCAL_TLDS):
            return False
        # Block IP literals in private/reserved ranges
        if _is_private_ip(host):
            return False
        # Optional allowlist enforcement
        if not _host_matches_allowlist(host, allowed_hosts):
            return False
        return True
    except Exception:
        return False
