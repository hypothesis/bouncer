from urllib import parse
from pyramid import i18n
import jinja2


_ = i18n.TranslationStringFactory(__package__)


#: The maximum length that the "netloc" (the www.example.com part in
#: http://www.example.com/example) can be in the pretty URL that is displayed
#: to the user before it gets truncated.
NETLOC_MAX_LENGTH = 30


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

    :param document: the Elasticsearch annotation document to parse
    :type document: dict

    :rtype: 2-tuple of annotation ID (string) and document URI (string)

    """
    # We assume that Elasticsearch documents always have "_id" and "_source".
    annotation_id = document["_id"]
    annotation = document["_source"]

    # And that annotations always have "group" and "shared"
    group = annotation["group"]
    is_shared = annotation["shared"] is True

    can_reveal_metadata = is_shared and group == "__world__"

    document_uri = None
    quote = None
    text = annotation.get('text', make_boilerplate_text())
    if text == "":
        text = make_boilerplate_text()

    try:
        targets = annotation["target"]
        if targets:
            document_uri = targets[0]["source"]
            if 'selector' in targets[0]:
                selectors = targets[0]["selector"]
                for selector in selectors:
                    if selector.get('type') != "TextQuoteSelector":
                        continue
                    quote = selector.get("exact")
    except KeyError:
        pass

    if quote is None:
        quote = make_boilerplate_quote(document_uri)

    if text is None:
        text = make_boilerplate_text()

    if isinstance(document_uri, str) and document_uri.startswith("urn:x-pdf:"):
        try:
            web_uri = annotation["document"]["web_uri"]
            if web_uri:
                document_uri = web_uri
        except KeyError:
            pass

    if document_uri is None:
        raise InvalidAnnotationError(
            _("The annotation has no URI"), "annotation_has_no_uri")

    if not isinstance(document_uri, str):
        raise InvalidAnnotationError(
            _("The annotation has an invalid document URI"),
            "uri_not_a_string")

    return {
            "annotation_id": annotation_id,
            "document_uri": document_uri,
            "can_reveal_metadata": can_reveal_metadata,
            "quote": quote,
            "text": text
            }


def make_pretty_url(url):
    """
    Return the domain name from `url` for display.
    """
    try:
        parsed_url = parse.urlparse(url)
        pretty_url = parsed_url.netloc[:NETLOC_MAX_LENGTH]
        if len(parsed_url.netloc) > NETLOC_MAX_LENGTH:
            pretty_url = pretty_url + jinja2.Markup("&hellip;")
    except:
        return "CannotParseURL"
    return pretty_url


def make_boilerplate_quote(document_uri):
    if document_uri is None:
        return "Hypothesis annotation"
    else:
        pretty_url = make_pretty_url(document_uri)
        return "Hypothesis annotation for {site}".format(site=pretty_url)

def make_boilerplate_text():
    return 'Follow this link to see the annotation in context'
