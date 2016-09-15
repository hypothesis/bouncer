import elasticsearch
from pyramid import i18n


_ = i18n.TranslationStringFactory(__package__)


def elasticsearch_client(settings):
    return elasticsearch.Elasticsearch(
        host=settings["elasticsearch_host"],
        port=settings["elasticsearch_port"],
    )


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
    Return the ID and URI from the given Elasticsearch annotation document.

    Return the annotation ID and the annotated document's URI from the given
    Elasticsearch annotation document.

    :param document: the Elasticsearch annotation document to parse
    :type document: dict

    :rtype: 2-tuple of annotation ID (string) and document URI (string)

    """
    # We assume that Elasticsearch documents always have "_id" and "_source".
    annotation_id = document["_id"]
    annotation = document["_source"]

    document_uri = None

    try:
        targets = annotation["target"]
        if targets:
            document_uri = targets[0]["source"]
    except KeyError:
        pass

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

    return (annotation_id, document_uri)
