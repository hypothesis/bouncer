import json
from urllib import parse

import elasticsearch
from elasticsearch import exceptions
from pyramid import httpexceptions
from pyramid import i18n
from pyramid import view
from statsd.defaults.env import statsd


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

    try:
        document_uri = annotation["uri"]
    except KeyError:
        raise InvalidAnnotationError(
            _("The annotation has no URI"), "annotation_has_no_uri")

    if not isinstance(document_uri, str):
        raise InvalidAnnotationError(
            _("The annotation has an invalid document URI"), "uri_not_a_string")

    return (annotation_id, document_uri)


@view.view_defaults(renderer="bouncer:templates/annotation.html.jinja2")
class AnnotationController(object):

    def __init__(self, request):
        self.request = request

    @view.view_config(route_name="annotation_with_url")
    @view.view_config(route_name="annotation_without_url")
    def annotation(self):
        settings = self.request.registry.settings

        try:
            document = elasticsearch_client(settings).get(
                index=settings["elasticsearch_index"],
                doc_type="annotation",
                id=self.request.matchdict["id"])
        except exceptions.NotFoundError:
            statsd.incr("views.annotation.404.annotation_not_found")
            raise httpexceptions.HTTPNotFound(_("Annotation not found"))

        try:
            annotation_id, document_uri = parse_document(document)
        except InvalidAnnotationError as exc:
            statsd.incr("views.annotation.422.{}".format(exc.reason))
            raise httpexceptions.HTTPUnprocessableEntity(str(exc))

        # Remove any existing #fragment identifier from the URI before we
        # append our own.
        document_uri = parse.urldefrag(document_uri)[0]

        if not (document_uri.startswith("http://") or
                document_uri.startswith("https://")):
            statsd.incr("views.annotation.422.not_an_http_or_https_document")
            raise httpexceptions.HTTPUnprocessableEntity(
                _("Sorry, but it looks like this annotation was made on a "
                  "document that is not publicly available. "
                  "To view it’s annotations, a document's address must start "
                  "with <code>http://</code> or <code>https://</code>."))

        via_url = "{via_base_url}/{uri}#annotations:{id}".format(
            via_base_url=settings["via_base_url"],
            uri=document_uri,
            id=annotation_id)

        extension_url = "{uri}#annotations:{id}".format(
            uri=document_uri, id=annotation_id)

        statsd.incr("views.annotation.200.annotation_found")
        return {
            "data": json.dumps({
                # Warning: variable names change from python_style to
                # javaScriptStyle here!
                "viaUrl": via_url,
                "extensionUrl": extension_url,
            })
        }


def elasticsearch_client(settings):
    return elasticsearch.Elasticsearch(
        host=settings["elasticsearch_host"],
        port=settings["elasticsearch_port"],
    )


@view.view_config(renderer="bouncer:templates/index.html.jinja2",
                  route_name="index")
def index(request):
    statsd.incr("views.index.302.redirected_to_hypothesis")
    raise httpexceptions.HTTPFound(
        location=request.registry.settings["hypothesis_url"])


@view.view_config(
    context=httpexceptions.HTTPException,
    renderer='bouncer:templates/error.html.jinja2')
def httpexception(exc, request):
    request.response.status_int = exc.status_int
    return {"message": str(exc)}


def includeme(config):
    config.add_route("index", "/")
    config.add_route("annotation_with_url", "/{id}/*url")
    config.add_route("annotation_without_url", "/{id}")
    config.scan(__name__)
