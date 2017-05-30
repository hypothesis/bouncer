from pyramid import i18n


_ = i18n.TranslationStringFactory(__package__)


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
    Return the ID, URI, quote, and text from the given Elasticsearch
    annotation document.

    Return the annotation ID and the annotated document's URI from the given
    Elasticsearch annotation document.

    Also return quote (if available) and text to enhance the share card.

    :param document: the Elasticsearch annotation document to parse
    :type document: dict

    :rtype: 2-tuple of annotation ID (string) and document URI (string)

    """
    # We assume that Elasticsearch documents always have "_id" and "_source".

    annotation_id = document["_id"]
    annotation = document["_source"]

    document_uri = None

    quote = None
    if annotation["text"] == "":
        text = "Follow this link to see the annotation on the original page."
    else:
        text = annotation["text"]

    try:
        targets = annotation["target"]
        if targets:
            document_uri = targets[0]["source"]
            selectors = targets[0]["selector"]
            for selector in selectors:
                if selector["type"] == "TextQuoteSelector":
                    quote = selector["exact"]
    except KeyError:
        pass

    if isinstance(document_uri, str) and document_uri.startswith("urn:x-pdf:"):
        try:
            web_uri = annotation["document"]["web_uri"]
            if web_uri:
                document_uri = web_uri
        except KeyError:
            pass

    if quote is None:
        quote = "Annotation for " + document_uri

    if document_uri is None:
        raise InvalidAnnotationError(
            _("The annotation has no URI"), "annotation_has_no_uri")

    if not isinstance(document_uri, str):
        raise InvalidAnnotationError(
            _("The annotation has an invalid document URI"),
            "uri_not_a_string")

    return (annotation_id, document_uri, quote, text)
