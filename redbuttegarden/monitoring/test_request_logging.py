"""Focused tests for privacy-safe request completion logging."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

from django.http import HttpResponse, StreamingHttpResponse
from django.test import RequestFactory, SimpleTestCase

from monitoring.middleware import request_logging
from monitoring.middleware.request_logging import RequestLoggingMiddleware


class RequestLoggingMiddlewareFocusedTests(SimpleTestCase):
    """Exercise request observability without requiring a test database."""

    def setUp(self) -> None:
        """Reset cold-start state and construct requests for each test."""

        self.factory = RequestFactory()
        self.original_cold_start = request_logging._cold_start
        request_logging._cold_start = True

    def tearDown(self) -> None:
        """Restore the process-level cold-start marker after each test."""

        request_logging._cold_start = self.original_cold_start

    def _record_from_log(self, output: str) -> dict[str, object]:
        """Extract the JSON completion record from Django's default log format."""

        _, separator, payload = output.partition("django.request:")
        self.assertTrue(separator)
        return json.loads(payload)

    def test_valid_trace_and_resolved_route_are_logged_without_request_metadata(self) -> None:
        """Use a validated X-Ray root ID and normalized resolver route only."""

        request = self.factory.get(
            "/private/account?email=person@example.com",
            HTTP_USER_AGENT="private-agent",
            HTTP_X_FORWARDED_FOR="203.0.113.8",
            HTTP_X_AMZN_TRACE_ID="Root=1-abcdef01-0123456789abcdef01234567;Parent=abc",
        )
        request.resolver_match = SimpleNamespace(route="garden/<slug:slug>/")
        middleware = RequestLoggingMiddleware(lambda _: HttpResponse("ok"))

        with self.assertLogs("django.request", level="INFO") as logs:
            middleware(request)

        record = self._record_from_log(logs.output[0])
        self.assertEqual(record["route"], "garden/<slug:slug>/")
        self.assertEqual(record["trace_id"], "1-abcdef01-0123456789abcdef01234567")
        self.assertEqual(record["response_size_bytes"], 2)
        self.assertNotIn("private-agent", logs.output[0])
        self.assertNotIn("203.0.113.8", logs.output[0])
        self.assertNotIn("person@example.com", logs.output[0])

    def test_malformed_trace_header_is_not_logged(self) -> None:
        """Reject malformed and newline-bearing X-Ray trace header values."""

        request = self.factory.get(
            "/garden/",
            HTTP_X_AMZN_TRACE_ID="Root=not-a-trace\nprivate-value;Parent=abc",
        )
        middleware = RequestLoggingMiddleware(lambda _: HttpResponse("ok"))

        with self.assertLogs("django.request", level="INFO") as logs:
            middleware(request)

        record = self._record_from_log(logs.output[0])
        self.assertIsNone(record["trace_id"])
        self.assertNotIn("private-value", logs.output[0])

    def test_cold_start_is_consumed_at_request_entry(self) -> None:
        """Mark only the first entered invocation as a cold start."""

        middleware = RequestLoggingMiddleware(lambda _: HttpResponse("ok"))

        with self.assertLogs("django.request", level="INFO") as logs:
            middleware(self.factory.get("/first/"))
            middleware(self.factory.get("/second/"))

        self.assertTrue(self._record_from_log(logs.output[0])["cold_start"])
        self.assertFalse(self._record_from_log(logs.output[1])["cold_start"])

    def test_streaming_response_has_no_eager_size_calculation(self) -> None:
        """Leave streaming response sizes unset instead of consuming the iterator."""

        middleware = RequestLoggingMiddleware(
            lambda _: StreamingHttpResponse(iter([b"stream"]))
        )

        with self.assertLogs("django.request", level="INFO") as logs:
            middleware(self.factory.get("/stream/"))

        self.assertIsNone(self._record_from_log(logs.output[0])["response_size_bytes"])

    def test_downstream_exception_is_reraised_without_completion_log(self) -> None:
        """Keep downstream failures visible and avoid falsely logging completion."""

        def raises(_: object) -> HttpResponse:
            raise ValueError("downstream failure")

        middleware = RequestLoggingMiddleware(raises)
        with patch("monitoring.middleware.request_logging.logger.info") as log_info:
            with self.assertRaisesRegex(ValueError, "downstream failure"):
                middleware(self.factory.get("/failure/"))

        log_info.assert_not_called()
        self.assertFalse(request_logging._cold_start)

    def test_logging_failure_does_not_change_successful_response(self) -> None:
        """Treat logging-handler failures as non-fatal observability failures."""

        response = HttpResponse("ok")
        middleware = RequestLoggingMiddleware(lambda _: response)

        with patch(
            "monitoring.middleware.request_logging.logger.info",
            side_effect=RuntimeError("logger unavailable"),
        ):
            returned_response = middleware(self.factory.get("/garden/"))

        self.assertIs(returned_response, response)
