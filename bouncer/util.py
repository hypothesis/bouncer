from urllib import parse

import jinja2
from pyramid import i18n

_ = i18n.TranslationStringFactory(__package__)


#: The maximum length that the "netloc" (the www.example.com part in
#: http://www.example.com/example) can be in the pretty URL that is displayed
#: to the user before it gets truncated.
NETLOC_MAX_LENGTH = 30

#: The metadata we are populating has fields that play the roles of Title and
#: Description on Twitter and Facebook share cards. We map the annotation's `quote`
#: field to Title. If we lack a quote we try to form one from `document_uri`
#: If that fails, we fall back to this minimal version.
ANNOTATION_BOILERPLATE_QUOTE = _("Hypothesis annotation")

#: We map the annotation's `text` field to Description. If it's empty, we fall back
#: to this minimal version.
ANNOTATION_BOILERPLATE_TEXT = _("Follow this link to see the annotation in context")


class DeletedAnnotationError(Exception):

    """Raised if an annotation has been marked as deleted in Elasticsearch."""


class InvalidAnnotationError(Exception):

    """Raised if an annotation from Elasticsearch can't be parsed."""

    def __init__(self, message, reason):
        """
        Return a new InvalidAnnotationError instance.

        :param message: a user-friendly error message
        :type message: string

        :param reason: a computer-friendly unique string identifying the reason
            the exception was raised
        :type reason: string

        """
        self.message = message
        self.reason = reason

    def __str__(self):
        return self.message


def parse_document(document):
    """
    Return the annotation ID, annotated document's URI, and shared
    status from the given Elasticsearch annotation document.

    Also return annotation quote (if available, else empty) and text
    to enhance the share card.

    Tools for checking how FB and Twitter display share metadata:
      https://developers.facebook.com/tools/debug/sharing/
      https://cards-dev.twitter.com/validator

    :param document: the Elasticsearch annotation document to parse
    :type document: dict

    :returns: A dict with extracted metadata properties

    """
    # We assume that Elasticsearch documents always have "_id" and "_source".
    annotation_id = document["_id"]
    annotation = document["_source"]

    if document["_source"].get("deleted", False) is True:
        raise DeletedAnnotationError()

    authority = annotation["authority"]

    # If an annotation isn't deleted then we assume that it always has "group"
    # and "shared".
    group = annotation["group"]
    is_shared = annotation["shared"] is True

    show_metadata = is_shared and group == "__world__"

    document_uri = None

    # This will fill the Title slot in Twitter/OG metadata
    quote = None

    # This will fill the Description slot in Twitter/OG metadata
    text = annotation.get("text")
    if not text:
        text = ANNOTATION_BOILERPLATE_TEXT

    try:
        targets = annotation["target"]
        if targets:
            document_uri = targets[0]["source"]
            selectors = targets[0].get("selector", [])
            for selector in selectors:
                if selector.get("type") != "TextQuoteSelector":
                    continue
                quote = selector.get("exact")
    except KeyError:
        pass

    # If the annotation has no selectors, quote is still None so apply boilerplate
    if quote is None:
        quote = get_boilerplate_quote(document_uri)

    if isinstance(document_uri, str) and document_uri.startswith("urn:x-pdf:"):
        try:
            web_uri = annotation["document"]["web_uri"]
            if web_uri:
                document_uri = web_uri
        except KeyError:
            pass

    if document_uri is None:
        raise InvalidAnnotationError(
            _("The annotation has no URI"), "annotation_has_no_uri"
        )

    if not isinstance(document_uri, str):
        raise InvalidAnnotationError(
            _("The annotation has an invalid document URI"), "uri_not_a_string"
        )

    return {
        "authority": authority,
        "annotation_id": annotation_id,
        "document_uri": document_uri,
        "show_metadata": show_metadata,
        "quote": _escape_quotes(quote),
        "text": _escape_quotes(text),
    }


def get_pretty_url(url):
    """
    Return the domain name from `url` for display.
    """
    try:
        parsed_url = parse.urlparse(url)
    except (AttributeError, ValueError):
        return None

    pretty_url = parsed_url.netloc[:NETLOC_MAX_LENGTH]
    if len(parsed_url.netloc) > NETLOC_MAX_LENGTH:
        pretty_url += jinja2.Markup("&hellip;")
    return pretty_url


def get_boilerplate_quote(document_uri):
    pretty_url = get_pretty_url(document_uri)
    if pretty_url:
        return _("Hypothesis annotation for {site}".format(site=pretty_url))
    else:
        return ANNOTATION_BOILERPLATE_QUOTE


def _escape_quotes(string):
    return string.replace('"', "\u0022").replace("'", "\u0027")
