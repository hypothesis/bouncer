import io
import secrets
import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from bouncer import embed_detector
from bouncer.embed_detector import page_embeds_client, url_embeds_client


class TestUrlEmbedsClient:
    @pytest.mark.parametrize(
        "url",
        [
            # Matching HTTPS URL.
            "https://web.hypothes.is/blog/article.foo",
            # Matching HTTP URL.
            "http://web.hypothes.is/blog/article.foo",
            # Path omitted.
            "http://h.readthedocs.io",
            # Matching URLs with ignored query string / fragment.
            "http://web.hypothes.is/blog/article.foo?ignore_me=1",
            "http://web.hypothes.is/blog/article.foo#ignoreme",
            # Example matching URLs for various sites on the list.
            "https://docdrop.org/pdf/1Vsd26C0KuMw4Mj1WEBjBz1T8G75vIhWx-gaQEE.pdf/",
            "https://docdrop.org/video/AJXGJYl0wJc/",
            "https://www.semanticscholar.org/reader/5e331bf7887e2e634bf5b12788849d2d2b74bc7f",
            "https://development.semanticscholar.org/reader/5e331bf7887e2e634bf5b12788849d2d2b74bc7f",
            "https://staging.semanticscholar.org/reader/5e331bf7887e2e634bf5b12788849d2d2b74bc7f",
        ],
    )
    def test_returns_true_for_matching_url(self, url):
        assert url_embeds_client(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            # Non-matching domain.
            "http://example.com",
            # Non-matching path.
            "http://web.hypothes.is/help/article.foo",
            # Only HTTP* URLs can match.
            "nothttp://test-domain.com/fulltext",
        ],
    )
    def test_returns_false_for_non_matching_url(self, url):
        assert url_embeds_client(url) is False

    def test_page_embeds_client_for_non_successfull_status_code(self):
        mock_get = response_mock([], status_code=404)
        with patch("bouncer.embed_detector.requests.get", return_value=mock_get):
            assert page_embeds_client(random_string_urlsafe()) is False

    def test_page_embeds_client_for_non_html_response(self):
        mock_get = response_mock([], "application/pdf")
        with patch("bouncer.embed_detector.requests.get", return_value=mock_get):
            assert page_embeds_client(random_string_urlsafe()) is False

    def test_page_embeds_client_for_non_embedded_client(self):
        mock_get = response_mock(["<html>", "</html>"])
        with patch("bouncer.embed_detector.requests.get", return_value=mock_get):
            assert page_embeds_client(random_string_urlsafe()) is False

    @pytest.mark.parametrize(
        "content_block",
        [
            '<script src="https://hypothes.is/embed.js"></script>',
            '<script src="https://cdn.hypothes.is/hypothesis"></script>',
            '<script class="js-hypothesis-config"></script>',
        ],
    )
    def test_page_embeds_client_for_embedded_client(self, content_block):
        # Add an empty line to cover logic to ignore empty lines
        mock_get = response_mock(["<html>", None, content_block, "</html>"])
        with patch("bouncer.embed_detector.requests.get", return_value=mock_get):
            assert page_embeds_client(random_string_urlsafe()) is True

    def test_page_embeds_client_stops_after_max_bytes(self):
        chunks = (
            ["<html>"]
            + ["x" * 1024 for _ in range(embed_detector.MAX_BYTES_TO_CHECK // 1024)]
            # This would usually match, but it's beyond the maximum amount of bytes
            + ['<script src="https://hypothes.is/embed.js"></script>', "</html>"]
        )
        mock_get = response_mock(chunks)
        with patch("bouncer.embed_detector.requests.get", return_value=mock_get):
            assert page_embeds_client(random_string_urlsafe()) is False

    def test_page_embeds_client_stops_after_deadline(self):
        chunks = [
            "<html>",
            "some content",
            # This would usually match, but we run out of time before reaching it
            '<script src="https://hypothes.is/embed.js"></script>',
        ]
        mock_get = response_mock(chunks)
        # First call computes the deadline, subsequent calls are past it.
        clock = iter([0, embed_detector.MAX_SECONDS_TO_CHECK + 1] + [1000] * 10)
        with patch("bouncer.embed_detector.requests.get", return_value=mock_get), patch(
            "bouncer.embed_detector.time.monotonic", side_effect=lambda: next(clock)
        ):
            assert page_embeds_client(random_string_urlsafe()) is False

    def test_page_embeds_client_finds_marker_split_across_chunks(self):
        marker = '<script src="https://hypothes.is/embed.js"></script>'
        chunks = ["<html>" + marker[:20], marker[20:] + "</html>"]
        mock_get = response_mock(chunks)
        with patch("bouncer.embed_detector.requests.get", return_value=mock_get):
            assert page_embeds_client(random_string_urlsafe()) is True

    def test_page_embeds_client_reads_in_large_chunks(self):
        mock_get = response_mock(["<html>", "</html>"])
        with patch("bouncer.embed_detector.requests.get", return_value=mock_get):
            page_embeds_client(random_string_urlsafe())

        resp = mock_get.__enter__.return_value
        resp.iter_content.assert_called_once_with(chunk_size=embed_detector.CHUNK_SIZE)
        resp.iter_lines.assert_not_called()

    def test_page_embeds_client_is_fast_for_huge_single_line(self):
        # Regression test: a page with a multi-megabyte single line (e.g. a
        # self-contained HTML export with inlined images) used to take tens of
        # seconds because `iter_lines()` is quadratic on long lines.
        body = b"<html>" + b"A" * (8 * 1024 * 1024) + b"</html>"
        resp = requests.Response()
        resp.status_code = 200
        resp.headers["Content-Type"] = "text/html"
        resp.raw = io.BytesIO(body)

        cm = MagicMock()
        cm.__enter__.return_value = resp
        with patch("bouncer.embed_detector.requests.get", return_value=cm):
            start = time.monotonic()
            assert page_embeds_client(random_string_urlsafe()) is False
            assert time.monotonic() - start < 1

    def test_page_embeds_client_with_raised_error(self):
        with patch(
            "bouncer.embed_detector.requests.get", side_effect=RuntimeError("fail")
        ):
            assert page_embeds_client(random_string_urlsafe()) is False


def random_string_urlsafe(length: int = 16) -> str:
    """Generate a random string to use when calling page_embeds_client, to bypass the LRU cache"""
    return secrets.token_urlsafe(length)[:length]


def response_mock(
    lines: list[str | None], content_type="text/html", status_code=200
) -> MagicMock:
    """
    Mock a response to return from requests.get
    """
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"Content-Type": content_type}
    resp.iter_content.return_value = [
        chunk if chunk is None else chunk.encode("utf-8") for chunk in lines
    ]

    # Make the response usable as a context manager: `with ...:`
    cm = MagicMock()
    cm.__enter__.return_value = resp
    cm.__exit__.return_value = None

    return cm
