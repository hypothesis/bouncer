import fnmatch
import re
from urllib.parse import urlparse

import requests
from cachetools import TTLCache, cached

# Hardcoded URL patterns where client is assumed to be embedded.
#
# Only the hostname and path are included in the pattern. The path must be
# specified; use "example.com/*" to match all URLs on a particular domain.
#
# Patterns are shell-style wildcards ('*' matches any number of chars, '?'
# matches a single char).
PATTERNS = [
    # Official Hypothesis websites
    "h.readthedocs.io/*",
    "web.hypothes.is/blog/*",
    # Unofficial Hypothesis-affiliated websites
    "docdrop.org/*",  # See https://github.com/hypothesis/bouncer/issues/389
    # Publisher partners
    "psycnet.apa.org/fulltext/*",
    "awspntest.apa.org/fulltext/*",
    "*.semanticscholar.org/reader/*",  # See https://hypothes-is.slack.com/archives/C04F8GLTT7U/p1674065065018549
]

COMPILED_PATTERNS = [re.compile(fnmatch.translate(pat)) for pat in PATTERNS]


def url_embeds_client(url):  # pragma: nocover
    """
    Test whether ``url`` is known to embed the client.

    This currently just tests the URL against the pattern list ``PATTERNS``.

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


# Cache up to 10,000 page-lookups, but never for more than 1 hour
@cached(cache=TTLCache(maxsize=10000, ttl=3600))
def page_embeds_client(page: str) -> bool:
    """
    Checks if the client is embedded in provided page
    - Request is streamed to avoid trying to download a huge file unnecessarily
    - The page must be html to be evaluated. Anything else is ignored
    - We wait a maximum of 1.5 seconds for a response
    - We will not evaluate more than 5000 lines of the response
    """

    request_timeout = 1.5
    max_lines_to_check = 5000
    embedded_client_markers = (
        "hypothes.is/embed.js",
        "cdn.hypothes.is/hypothesis",
        "js-hypothesis-config",
    )
    headers = {"User-Agent": "Hypothesis/1.0 (bouncer)"}

    try:
        with requests.get(
            page, stream=True, timeout=request_timeout, headers=headers
        ) as r:
            if (
                r.status_code != 200
                or "text/html" not in r.headers.get("Content-Type", "").lower()
            ):
                return False

            for line in r.iter_lines():
                if not line:
                    # filter out keep-alive new lines
                    continue

                max_lines_to_check -= 1
                if max_lines_to_check <= 0:
                    break

                decoded_line = line.decode("utf-8")
                if any(marker in decoded_line for marker in embedded_client_markers):
                    return True
    except Exception:
        # If the request fails in any way, we simply ignore the error and
        # continue as if the client was not embedded in the page
        return False

    return False
