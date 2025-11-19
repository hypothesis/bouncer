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
