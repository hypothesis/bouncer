import re
from urllib.parse import urlparse

"""
Hardcoded URL patterns where client is assumed to be embedded.

Only the hostname and path are included in the pattern. The path must be
specified.

These are regular expressions so periods must be escaped.
"""
PATTERNS = [
    "h\.readthedocs\.io/.*",
    "web\.hypothes\.is/blog/.*",
]

COMPILED_PATTERNS = [re.compile(pat) for pat in PATTERNS]


def url_embeds_client(url):
    """
    Test whether ``url`` is known to embed the client.

    This currently just tests the URL against the hardcoded regex list
    ``PATTERNS``.

    Only the hostname and path of the URL are tested. Returns false for non-HTTP
    URLs.

    :return: True if the URL matches a pattern.
    """
    parsed_url = urlparse(url)
    if not parsed_url.scheme.startswith("http"):
        return False

    path = parsed_url.path
    if not path:
        path = "/"
    netloc_and_path = parsed_url.netloc + path

    for pat in COMPILED_PATTERNS:
        if pat.fullmatch(netloc_and_path):
            return True
    return False
