from unittest.mock import MagicMock, patch

import pytest

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
            assert page_embeds_client("") is False

    def test_page_embeds_client_for_non_html_response(self):
        mock_get = response_mock([], "application/pdf")
        with patch("bouncer.embed_detector.requests.get", return_value=mock_get):
            assert page_embeds_client("") is False

    def test_page_embeds_client_for_non_embedded_client(self):
        mock_get = response_mock(["<html>", "</html>"])
        with patch("bouncer.embed_detector.requests.get", return_value=mock_get):
            assert page_embeds_client("") is False
            assert page_embeds_client("") is False

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
            assert page_embeds_client("") is True

    def test_page_embeds_client_for_too_many_lines(self):
        lines = (
            ["<html>"]
            + ["some line" for _ in range(5000)]
            # This would usually match, but it's further down the maximum amount of lines
            + ['<script src="https://hypothes.is/embed.js"></script>', "</html>"]
        )
        mock_get = response_mock(lines)
        with patch("bouncer.embed_detector.requests.get", return_value=mock_get):
            assert page_embeds_client("") is False

    def test_page_embeds_client_with_raised_error(self):
        with patch(
            "bouncer.embed_detector.requests.get", side_effect=RuntimeError("fail")
        ):
            assert page_embeds_client("") is False


def response_mock(
    lines: list[str], content_type="text/html", status_code=200
) -> MagicMock:
    """
    Mock a response to return from requests.get
    """
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"Content-Type": content_type}
    resp.iter_lines.return_value = [
        ln if ln is None else ln.encode("utf-8") for ln in lines
    ]

    # Make the response usable as a context manager: `with ...:`
    cm = MagicMock()
    cm.__enter__.return_value = resp
    cm.__exit__.return_value = None

    return cm
