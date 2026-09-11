"""Regression tests for the SSRF-safe concert image probe."""

from __future__ import annotations

import socket
import ssl
from collections.abc import Mapping
from concurrent.futures import TimeoutError as FutureTimeoutError
from unittest.mock import MagicMock, patch

from concerts.services.image_probe import probe_public_image_url


class _Response:
    def __init__(self, status: int, headers: Mapping[str, str]) -> None:
        self.status = status
        self.headers = headers
        self.released = False

    def release_conn(self) -> None:
        self.released = True


def _address_info(*addresses: str) -> list[tuple[int, int, int, str, tuple[str, int]]]:
    return [
        (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (address, 443))
        for address in addresses
    ]


def _pool(response: _Response) -> MagicMock:
    pool = MagicMock()
    pool.urlopen.return_value = response
    return pool


def test_probe_rejects_private_addresses_without_connecting() -> None:
    with (
        patch(
            "concerts.services.image_probe.socket.getaddrinfo",
            return_value=_address_info("127.0.0.1"),
        ),
        patch("concerts.services.image_probe.HTTPSConnectionPool") as pool_factory,
    ):
        result = probe_public_image_url("https://example.com/image.jpg")

    assert result is None
    pool_factory.assert_not_called()


def test_probe_rejects_hostname_with_mixed_public_and_private_addresses() -> None:
    with (
        patch(
            "concerts.services.image_probe.socket.getaddrinfo",
            return_value=_address_info("93.184.216.34", "10.0.0.8"),
        ),
        patch("concerts.services.image_probe.HTTPSConnectionPool") as pool_factory,
    ):
        result = probe_public_image_url("https://example.com/image.jpg")

    assert result is None
    pool_factory.assert_not_called()


def test_probe_bounds_dns_deadline_and_rejects_work_when_resolver_is_full() -> None:
    future = MagicMock()
    future.result.side_effect = FutureTimeoutError
    executor = MagicMock()
    executor.submit.return_value = future
    capacity = MagicMock()
    capacity.acquire.side_effect = [True, False]

    with (
        patch("concerts.services.image_probe._DNS_EXECUTOR", executor),
        patch("concerts.services.image_probe._DNS_CAPACITY", capacity),
        patch(
            "concerts.services.image_probe.time.monotonic",
            side_effect=[100.0, 101.0, 102.0, 200.0, 201.0],
        ),
    ):
        timed_out_result = probe_public_image_url("https://example.com/image.jpg")
        capacity_result = probe_public_image_url("https://example.com/image.jpg")

    assert timed_out_result is None
    assert capacity_result is None
    future.result.assert_called_once_with(timeout=3.0)
    future.cancel.assert_called_once_with()
    executor.submit.assert_called_once()

    # The capacity is intentionally retained while the abandoned lookup is
    # running, then released by its completion callback.
    capacity.release.assert_not_called()
    completion_callback = future.add_done_callback.call_args.args[0]
    completion_callback(future)
    capacity.release.assert_called_once_with()


def test_probe_pins_connection_to_validated_ip_and_preserves_tls_hostname() -> None:
    response = _Response(200, {"Content-Length": "42"})
    pool = _pool(response)
    with (
        patch(
            "concerts.services.image_probe.socket.getaddrinfo",
            return_value=_address_info("93.184.216.34"),
        ),
        patch("concerts.services.image_probe.HTTPSConnectionPool", return_value=pool) as pool_factory,
    ):
        result = probe_public_image_url("https://example.com/images/promo.jpg?size=large")

    assert result is not None
    assert result.final_url == "https://example.com/images/promo.jpg?size=large"
    pool_factory.assert_called_once_with(
        "93.184.216.34",
        443,
        cert_reqs=ssl.CERT_REQUIRED,
        assert_hostname="example.com",
        server_hostname="example.com",
    )
    pool.urlopen.assert_called_once()
    request_args, request_kwargs = pool.urlopen.call_args
    assert request_args == ("HEAD", "/images/promo.jpg?size=large")
    assert request_kwargs["headers"]["Host"] == "example.com"
    assert request_kwargs["redirect"] is False
    assert request_kwargs["retries"] is False
    assert response.released is True
    pool.close.assert_called_once_with()


def test_probe_validates_redirect_target_and_returns_final_url() -> None:
    redirect_response = _Response(302, {"Location": "https://cdn.example.net/final.jpg"})
    image_response = _Response(204, {"Content-Length": "12"})
    first_pool = _pool(redirect_response)
    second_pool = _pool(image_response)

    with (
        patch(
            "concerts.services.image_probe.socket.getaddrinfo",
            side_effect=[_address_info("93.184.216.34"), _address_info("1.1.1.1")],
        ),
        patch(
            "concerts.services.image_probe.HTTPSConnectionPool",
            side_effect=[first_pool, second_pool],
        ) as pool_factory,
    ):
        result = probe_public_image_url("https://example.com/original.jpg")

    assert result is not None
    assert result.final_url == "https://cdn.example.net/final.jpg"
    assert [call.args[0] for call in pool_factory.call_args_list] == [
        "93.184.216.34",
        "1.1.1.1",
    ]


def test_probe_rejects_redirect_to_private_address() -> None:
    first_pool = _pool(_Response(302, {"Location": "http://169.254.169.254/latest/meta-data/"}))
    with (
        patch(
            "concerts.services.image_probe.socket.getaddrinfo",
            side_effect=[_address_info("93.184.216.34"), _address_info("169.254.169.254")],
        ),
        patch("concerts.services.image_probe.HTTPSConnectionPool", return_value=first_pool),
        patch("concerts.services.image_probe.HTTPConnectionPool") as http_pool_factory,
    ):
        result = probe_public_image_url("https://example.com/image.jpg")

    assert result is None
    http_pool_factory.assert_not_called()


def test_probe_rejects_more_than_three_redirects() -> None:
    pools = [
        _pool(_Response(302, {"Location": f"/redirect-{index}.jpg"}))
        for index in range(4)
    ]
    with (
        patch(
            "concerts.services.image_probe.socket.getaddrinfo",
            side_effect=[_address_info("93.184.216.34")] * 4,
        ),
        patch(
            "concerts.services.image_probe.HTTPSConnectionPool",
            side_effect=pools,
        ) as pool_factory,
    ):
        result = probe_public_image_url("https://example.com/image.jpg")

    assert result is None
    assert pool_factory.call_count == 4


def test_probe_requires_strictly_positive_decimal_content_length() -> None:
    for invalid_length in (None, "", "0", " 12", "+12", "12, 12"):
        response = _Response(200, {} if invalid_length is None else {"Content-Length": invalid_length})
        with (
            patch(
                "concerts.services.image_probe.socket.getaddrinfo",
                return_value=_address_info("93.184.216.34"),
            ),
            patch("concerts.services.image_probe.HTTPSConnectionPool", return_value=_pool(response)),
        ):
            assert probe_public_image_url("https://example.com/image.jpg") is None


def test_probe_reuses_one_decreasing_deadline_across_redirects() -> None:
    first_pool = _pool(_Response(302, {"Location": "/final.jpg"}))
    second_pool = _pool(_Response(200, {"Content-Length": "1"}))
    with (
        patch(
            "concerts.services.image_probe.socket.getaddrinfo",
            side_effect=[_address_info("93.184.216.34"), _address_info("93.184.216.34")],
        ),
        patch(
            "concerts.services.image_probe.HTTPSConnectionPool",
            side_effect=[first_pool, second_pool],
        ),
        patch(
            "concerts.services.image_probe.time.monotonic",
            side_effect=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
        ),
    ):
        result = probe_public_image_url("https://example.com/image.jpg")

    assert result is not None
    assert first_pool.urlopen.call_args.kwargs["timeout"].total == 4.7
    assert second_pool.urlopen.call_args.kwargs["timeout"].total == 4.4
