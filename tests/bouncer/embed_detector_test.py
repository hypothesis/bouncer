import pytest

from bouncer.embed_detector import url_embeds_client


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
