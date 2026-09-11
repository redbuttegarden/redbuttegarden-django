"""Safely probe public image URLs for the concert ticket interface."""

from __future__ import annotations

import ipaddress
import re
import socket
import ssl
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit, urlunsplit

import urllib3
from django.utils.encoding import iri_to_uri
from urllib3 import HTTPConnectionPool, HTTPSConnectionPool
from urllib3.response import BaseHTTPResponse
from urllib3.util import Timeout

MAX_IMAGE_URL_LENGTH: int = 2048
MAX_REDIRECTS: int = 3
PROBE_DEADLINE_SECONDS: float = 5.0
REDIRECT_STATUSES: frozenset[int] = frozenset({301, 302, 303, 307, 308})
DNS_RESOLVER_WORKERS: int = 4
_POSITIVE_DECIMAL = re.compile(r"[0-9]+")
_DNS_CAPACITY = threading.BoundedSemaphore(DNS_RESOLVER_WORKERS)
_DNS_EXECUTOR = ThreadPoolExecutor(
    max_workers=DNS_RESOLVER_WORKERS,
    thread_name_prefix="concert-image-dns",
)


@dataclass(frozen=True)
class ImageProbeResult:
    """Describe a public image URL that passed the bounded HEAD probe."""

    final_url: str


@dataclass(frozen=True)
class _PinnedTarget:
    url: str
    scheme: str
    hostname: str
    address: str
    port: int
    host_header: str
    request_target: str


@dataclass(frozen=True)
class _HeadResult:
    status: int
    location: str | None
    content_length: str | None


def probe_public_image_url(image_url: str) -> ImageProbeResult | None:
    """Return the final URL when a public image passes a bounded HEAD probe.

    DNS is resolved and checked before every request. The selected public IP
    address is then used directly for the connection so a second DNS lookup
    cannot redirect the request to a private network. Redirects are followed
    manually and receive the same validation.
    """

    deadline = time.monotonic() + PROBE_DEADLINE_SECONDS
    current_url = image_url

    try:
        for redirect_count in range(MAX_REDIRECTS + 1):
            _remaining_seconds(deadline)
            target = _resolve_public_target(current_url, deadline)
            result = _head(target, _remaining_seconds(deadline))

            if result.status in REDIRECT_STATUSES:
                if redirect_count == MAX_REDIRECTS or not result.location:
                    return None
                current_url = urljoin(target.url, result.location)
                continue

            if not 200 <= result.status < 300:
                return None
            if not _has_positive_decimal_length(result.content_length):
                return None
            return ImageProbeResult(final_url=target.url)
    except Exception:
        # Invalid URLs, DNS errors, TLS failures, and exhausted deadlines all
        # fail closed to the placeholder rendered by the caller.
        return None

    return None


def _resolve_public_target(url: str, deadline: float) -> _PinnedTarget:
    normalized_url = iri_to_uri(url)
    if len(normalized_url) > MAX_IMAGE_URL_LENGTH:
        raise ValueError("Image URL is too long.")
    if any(ord(character) < 32 or ord(character) == 127 for character in normalized_url):
        raise ValueError("Image URL contains a control character.")

    parsed = urlsplit(normalized_url)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not parsed.netloc or not parsed.hostname:
        raise ValueError("Image URL must be an absolute HTTP(S) URL.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Image URL credentials are not allowed.")

    hostname = _ascii_hostname(parsed.hostname)
    if "%" in hostname:
        raise ValueError("Scoped IP addresses are not allowed.")
    port = parsed.port or (443 if scheme == "https" else 80)
    addresses = _resolve_addresses(hostname, port, deadline)
    if not addresses or any(not _is_public_address(address) for address in addresses):
        raise ValueError("Image URL must resolve only to public addresses.")

    request_target = urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
    return _PinnedTarget(
        url=normalized_url,
        scheme=scheme,
        hostname=hostname,
        address=addresses[0],
        port=port,
        host_header=_host_header(hostname, port, scheme),
        request_target=request_target,
    )


def _ascii_hostname(hostname: str) -> str:
    try:
        return str(ipaddress.ip_address(hostname))
    except ValueError:
        return hostname.encode("idna").decode("ascii").lower()


def _resolve_addresses(hostname: str, port: int, deadline: float) -> list[str]:
    capacity = _DNS_CAPACITY
    if not capacity.acquire(blocking=False):
        raise urllib3.exceptions.TimeoutError("Image probe DNS capacity is exhausted.")

    try:
        future = _DNS_EXECUTOR.submit(
            socket.getaddrinfo,
            hostname,
            port,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
        )
    except Exception:
        capacity.release()
        raise

    # A timed-out resolver cannot be forcibly stopped. Its slot remains held
    # until it exits, preventing abandoned lookups from building an unbounded
    # executor queue or creating more resolver threads.
    future.add_done_callback(lambda _future: capacity.release())
    try:
        address_info = future.result(timeout=_remaining_seconds(deadline))
    except FutureTimeoutError as error:
        future.cancel()
        raise urllib3.exceptions.TimeoutError("Image probe DNS lookup timed out.") from error

    return list(dict.fromkeys(str(item[4][0]) for item in address_info))


def _is_public_address(address: str) -> bool:
    parsed = ipaddress.ip_address(address)
    return (
        parsed.is_global
        and not parsed.is_private
        and not parsed.is_loopback
        and not parsed.is_link_local
        and not parsed.is_multicast
        and not parsed.is_reserved
        and not parsed.is_unspecified
        and not getattr(parsed, "is_site_local", False)
    )


def _host_header(hostname: str, port: int, scheme: str) -> str:
    try:
        is_ipv6 = ipaddress.ip_address(hostname).version == 6
    except ValueError:
        is_ipv6 = False

    formatted_hostname = f"[{hostname}]" if is_ipv6 else hostname
    default_port = 443 if scheme == "https" else 80
    return formatted_hostname if port == default_port else f"{formatted_hostname}:{port}"


def _head(target: _PinnedTarget, remaining_seconds: float) -> _HeadResult:
    timeout = Timeout(total=remaining_seconds)
    pool: HTTPConnectionPool
    if target.scheme == "https":
        pool = HTTPSConnectionPool(
            target.address,
            target.port,
            cert_reqs=ssl.CERT_REQUIRED,
            assert_hostname=target.hostname,
            server_hostname=target.hostname,
        )
    else:
        pool = HTTPConnectionPool(target.address, target.port)

    response: BaseHTTPResponse | None = None
    try:
        response = pool.urlopen(
            "HEAD",
            target.request_target,
            headers={"Host": target.host_header, "Accept": "image/*"},
            redirect=False,
            retries=False,
            timeout=timeout,
            preload_content=False,
        )
        return _HeadResult(
            status=response.status,
            location=response.headers.get("Location"),
            content_length=response.headers.get("Content-Length"),
        )
    finally:
        if response is not None:
            response.release_conn()
        pool.close()


def _remaining_seconds(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise urllib3.exceptions.TimeoutError("Image probe deadline expired.")
    return remaining


def _has_positive_decimal_length(content_length: str | None) -> bool:
    return bool(
        content_length
        and _POSITIVE_DECIMAL.fullmatch(content_length)
        and int(content_length) > 0
    )
