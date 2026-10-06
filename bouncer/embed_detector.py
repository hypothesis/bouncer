import fnmatch
import re
import time
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
    # BioRxiv
    "biotome.hypothes.is/*",
    "www.biorxiv.org/*",
    "www.medrxiv.org/*",
]

COMPILED_PATTERNS = [re.compile(fnmatch.translate(pat)) for pat in PATTERNS]

#: Byte strings whose presence in a page indicates that it embeds the client.
EMBEDDED_CLIENT_MARKERS = (
    b"hypothes.is/embed.js",
    b"cdn.hypothes.is/hypothesis",
    b"js-hypothesis-config",
)

#: Size of each chunk read from the page when looking for the markers.
CHUNK_SIZE = 64 * 1024

#: Never read more than this many bytes of a page.
MAX_BYTES_TO_CHECK = 1024 * 1024

#: Never spend more than this many seconds reading a page, in total.
MAX_SECONDS_TO_CHECK = 3.0


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


# Cache up to 10,000 page-lookups, but never for more than 24 hours
@cached(cache=TTLCache(maxsize=10000, ttl=86400))
def page_embeds_client(page: str) -> bool:
    """
    Checks if the client is embedded in provided page
    - Request is streamed to avoid trying to download a huge file unnecessarily
    - The page must be html to be evaluated. Anything else is ignored
    - We wait a maximum of 1.5 seconds between bytes from the server
    - We will not read more than ``MAX_BYTES_TO_CHECK`` bytes of the response
    - We will not spend more than ``MAX_SECONDS_TO_CHECK`` seconds reading it

    The response is scanned in fixed-size chunks rather than line by line.
    ``Response.iter_lines()`` re-joins its buffer on every 512-byte read, which
    is quadratic for very long lines: a single multi-megabyte line (e.g. a
    self-contained HTML page with inlined images) could take tens of seconds
    of CPU, tying up a worker until it was killed. Because the worker was
    killed before returning, the result was never cached either.
    """

    request_timeout = 1.5
    headers = {"User-Agent": "Hypothesis/1.0 (bouncer)"}
    deadline = time.monotonic() + MAX_SECONDS_TO_CHECK
    # Keep the tail of the previous chunk so we still find a marker that is
    # split across two chunks.
    overlap = max(len(marker) for marker in EMBEDDED_CLIENT_MARKERS) - 1

    try:
        with requests.get(
            page, stream=True, timeout=request_timeout, headers=headers
        ) as r:
            if (
                r.status_code != 200
                or "text/html" not in r.headers.get("Content-Type", "").lower()
            ):
                return False

            bytes_read = 0
            tail = b""
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if not chunk:
                    continue

                window = tail + chunk
                if any(marker in window for marker in EMBEDDED_CLIENT_MARKERS):
                    return True

                bytes_read += len(chunk)
                if bytes_read >= MAX_BYTES_TO_CHECK or time.monotonic() > deadline:
                    break

                tail = window[-overlap:]
    except Exception:
        # If the request fails in any way, we simply ignore the error and
        # continue as if the client was not embedded in the page
        return False

    return False
