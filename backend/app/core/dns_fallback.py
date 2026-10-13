"""DNS-over-HTTPS fallback resolver.

Some managed hosts (notably Render) can cache a stale "does not exist" answer
for a hostname that has recently been created or re-pointed. We hit exactly
this during Supabase's pooler DNS cutover: the system resolver returned
NXDOMAIN for a host that public resolvers (8.8.8.8 / 1.1.1.1) resolved fine,
so every database connection failed with ``socket.gaierror: Name or service
not known``.

This module patches ``socket.getaddrinfo`` so that, when the system resolver
fails with ``gaierror``, the lookup is retried against public DNS-over-HTTPS
endpoints (Cloudflare, then Google). Because the app runs ``getaddrinfo`` in a
thread executor, a blocking HTTP lookup here is safe.

Importing the module installs the patch process-wide. It is imported from
``app.core.config`` so both the FastAPI app and the Alembic migrations pick it
up before any database connection is opened.
"""

from __future__ import annotations

import json
import socket
import sys
import urllib.request

_ORIGINAL_GETADDRINFO = socket.getaddrinfo

# (url_template, headers) pairs. "{name}" and "{type}" are substituted.
_DOH_ENDPOINTS: tuple[tuple[str, dict[str, str]], ...] = (
    (
        "https://cloudflare-dns.com/dns-query?name={name}&type={type}",
        {"Accept": "application/dns-json"},
    ),
    (
        "https://dns.google/resolve?name={name}&type={type}",
        {},
    ),
)

_RDTYPE_TO_VALUE = {"A": 1, "AAAA": 28}
_TIMEOUT_SECONDS = 5


def _doh_lookup(name: str, rdtype: str) -> list[str]:
    """Query public DoH endpoints for A/AAAA records; return IPs (may be empty)."""
    expected_value = _RDTYPE_TO_VALUE[rdtype]
    for template, headers in _DOH_ENDPOINTS:
        url = template.format(name=name, type=rdtype)
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
                payload = json.load(response)
        except Exception:
            continue
        ips = [
            answer["data"]
            for answer in payload.get("Answer", [])
            if answer.get("type") == expected_value
        ]
        if ips:
            return ips
    return []


def _getaddrinfo_with_fallback(host, port, family=0, type=0, proto=0, flags=0):
    try:
        return _ORIGINAL_GETADDRINFO(host, port, family, type, proto, flags)
    except socket.gaierror:
        # Only hostnames can be re-resolved via DoH. Skip IP literals (IPv4 is
        # all digits/dots, IPv6 contains ':') and empty hosts, then re-raise.
        if not host or ":" in host or host.replace(".", "").isdigit():
            raise
        ips = _doh_lookup(host, "A") or _doh_lookup(host, "AAAA")
        if not ips:
            raise
        results = []
        for ip in ips:
            addr_family = socket.AF_INET6 if ":" in ip else socket.AF_INET
            sockaddr = (ip, port, 0, 0) if addr_family == socket.AF_INET6 else (ip, port)
            results.append((addr_family, socket.SOCK_STREAM, proto or 0, "", sockaddr))
        print(f"DNS fallback (DoH) resolved {host} -> {ips}", file=sys.stderr)
        return results


_installed = False


def install() -> None:
    """Install the DoH-backed getaddrinfo patch (idempotent)."""
    global _installed
    if _installed:
        return
    socket.getaddrinfo = _getaddrinfo_with_fallback  # type: ignore[assignment]
    _installed = True


install()
