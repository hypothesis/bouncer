import json
from urllib import parse

import h_pyramid_sentry
from elasticsearch import Elasticsearch, exceptions
from pyramid import httpexceptions, i18n, view
from pyramid.httpexceptions import HTTPNoContent
from sentry_sdk import capture_message

from bouncer import util
from bouncer.embed_detector import url_embeds_client

_ = i18n.TranslationStringFactory(__package__)


class FailedHealthcheck(Exception):
    """An exception raised when the healthcheck fails."""


@view.view_defaults(renderer="bouncer:templates/annotation.html.jinja2")
class AnnotationController(object):
    def __init__(self, request):
        self.request = request

    @view.view_config(route_name="annotation_with_url")
    @view.view_config(route_name="annotation_without_url")
    def annotation(self):
        settings = self.request.registry.settings

        try:
            es7_or_later = _es_server_version(self.request.es) >= 7
            document = self.request.es.get(
                index=settings["elasticsearch_index"],
                # Set `doc_type` to the name of the mapping type used by h
                # when talking to an ES 6 server, or the endpoint name "_doc"
                # in ES 7+.
                #
                # See https://www.elastic.co/guide/en/elasticsearch/reference/7.17/removal-of-types.html
                doc_type="_doc" if es7_or_later else "annotation",
                id=self.request.matchdict["id"],
            )
        except exceptions.NotFoundError:
            raise httpexceptions.HTTPNotFound(_("Annotation not found"))

        try:
            parsed_document = util.parse_document(document)
            authority = parsed_document["authority"]
            annotation_id = parsed_document["annotation_id"]
            document_uri = parsed_document["document_uri"]
            show_metadata = parsed_document["show_metadata"]
            quote = parsed_document["quote"]
            text = parsed_document["text"]
            has_media_time = parsed_document["has_media_time"]

        except util.DeletedAnnotationError:
            raise httpexceptions.HTTPNotFound(_("Annotation not found"))

        except util.InvalidAnnotationError as exc:
            raise httpexceptions.HTTPUnprocessableEntity(str(exc))

        # Remove any existing #fragment identifier from the URI before we
        # append our own.
        document_uri = parse.urldefrag(document_uri)[0]

        if not _is_valid_http_url(document_uri):
            raise httpexceptions.HTTPUnprocessableEntity(
                _(
                    "Sorry, but it looks like this annotation was made on a "
                    "document that is not publicly available."
                )
            )

        via_url = None
        if _can_use_proxy(settings, authority=authority) and not url_embeds_client(
            document_uri
        ):
            via_url = "{via_base_url}/{uri}#annotations:{id}".format(
                via_base_url=settings["via_base_url"],
                uri=document_uri,
                id=annotation_id,
            )

        extension_url = "{uri}#annotations:{id}".format(
            uri=document_uri, id=annotation_id
        )

        pretty_url = util.get_pretty_url(document_uri)

        title = util.get_boilerplate_quote(document_uri)

        default_extension = settings["chrome_extension_id"]["default"]
        extension_id = settings["chrome_extension_id"].get(authority, default_extension)

        # If a YouTube annotation has a media time associated, this means it
        # was made using Via's transcript annotation tool.
        #
        # This means we force the use of Via, even if the extension is
        # installed.
        always_use_via = False
        if document_uri.startswith("https://www.youtube.com") and has_media_time:
            always_use_via = True

        return {
            "data": json.dumps(
                {
                    # Warning: variable names change from python_style to
                    # javaScriptStyle here!
                    "alwaysUseVia": always_use_via,
                    "chromeExtensionId": extension_id,
                    "extensionUrl": extension_url,
                    "viaUrl": via_url,
                }
            ),
            "show_metadata": show_metadata,
            "pretty_url": pretty_url,
            "quote": quote,
            "text": text,
            "title": title,
        }


def _es_server_version(es: Elasticsearch) -> int:
    """Return the major version of the Elasticsearch server."""
    server_version = es.info()["version"]["number"]
    major, *other = server_version.split(".")
    return int(major)


@view.view_config(renderer="bouncer:templates/index.html.jinja2", route_name="index")
def index(request):  # pragma: nocover
    raise httpexceptions.HTTPFound(location=request.registry.settings["hypothesis_url"])


@view.view_config(
    renderer="bouncer:templates/annotation.html.jinja2", route_name="goto_url"
)
def goto_url(request):
    """
    Redirect the user to a specified URL with the annotation client layer
    activated. This provides a URL-sharing mechanism.

    Optional querystring parameters can refine the behavior of the annotation
    client at the target url by identifying:

       * "group" - a group to focus; OR
       * "q" a query to populate the client search with
    """
    settings = request.registry.settings
    url = request.params.get("url")

    if url is None:
        raise httpexceptions.HTTPBadRequest('"url" parameter is missing')

    if not _is_valid_http_url(url):
        raise httpexceptions.HTTPBadRequest(
            _(
                "Sorry, but this service can only show annotations on "
                "valid HTTP or HTTPs URLs."
            )
        )

    # Remove any existing #fragment identifier from the URI before we
    # append our own.
    url = parse.urldefrag(url)[0]

    group = request.params.get("group", "")
    query = parse.quote(request.params.get("q", ""))

    # Translate any refining querystring parameters into a URL fragment
    # syntax understood by the client
    fragment = "annotations:"

    # group will supersede query (q) if both are present
    if group:
        # focus a specific group in the client
        fragment = fragment + "group:{group}".format(group=group)
    else:
        # populate the client search with a query
        fragment = fragment + "query:{query}".format(query=query)

    if not url_embeds_client(url):
        via_url = "{via_base_url}/{url}#{fragment}".format(
            via_base_url=settings["via_base_url"], url=url, fragment=fragment
        )
    else:
        via_url = None

    extension_url = "{url}#{fragment}".format(url=url, fragment=fragment)

    pretty_url = util.get_pretty_url(url)

    return {
        "data": json.dumps(
            {
                # nb. We always use the default extension ID here, because we
                # don't have an annotation to determine the authority.
                "chromeExtensionId": settings["chrome_extension_id"]["default"],
                "viaUrl": via_url,
                "extensionUrl": extension_url,
            }
        ),
        "pretty_url": pretty_url,
    }


@view.view_config(route_name="crash")
def crash(request):  # pragma: nocover
    """Crash if requested to for testing purposes."""

    # Ensure that no conceivable accident could cause this to be triggered
    if request.params.get("cid", "") == "a751bb01":
        raise ValueError("Something has gone wrong")

    return HTTPNoContent()


@view.view_defaults(renderer="bouncer:templates/error.html.jinja2")
class ErrorController(object):
    def __init__(self, exc, request):
        self.exc = exc
        self.request = request

    @view.view_config(context=httpexceptions.HTTPError)
    @view.view_config(context=httpexceptions.HTTPServerError)
    def httperror(self):
        self.request.response.status_int = self.exc.status_int
        # If code raises an HTTPError or HTTPServerError we assume this was
        # deliberately raised and:
        # 1. Show the user an error page including specific error message
        # 2. _Do not_ report the error to Sentry.
        return {"message": str(self.exc)}

    @view.view_config(context=Exception)
    def error(self):
        # If code raises a non-HTTPException exception we assume it was a bug
        # and:
        # 1. Show the user a generic error page
        # 2. Report the details of the error to Sentry.
        self.request.response.status_int = 500

        h_pyramid_sentry.report_exception()

        # In debug mode re-raise exceptions so that they get printed in the
        # terminal.
        if self.request.registry.settings["debug"]:
            raise

        return {
            "message": _(
                "Sorry, but something went wrong with the link. "
                "The issue has been reported and we'll try to "
                "fix it."
            )
        }


@view.view_config(route_name="healthcheck", renderer="json", http_cache=0)
def healthcheck(request):
    index = request.registry.settings["elasticsearch_index"]
    try:
        status = request.es.cluster.health(index=index)["status"]
    except exceptions.ElasticsearchException as exc:
        raise FailedHealthcheck("elasticsearch exception") from exc

    if status not in ("yellow", "green"):
        raise FailedHealthcheck("cluster status was {!r}".format(status))

    if "sentry" in request.params:
        capture_message("Test message from the healthcheck() view")

    return {"status": "okay"}


def _is_valid_http_url(url):
    """
    Return `True` if `url` is a valid HTTP or HTTPS URL.

    Parsing is currently very lenient as the URL only has to be accepted by
    `urlparse()`.
    """
    try:
        parsed_url = parse.urlparse(url)
        return parsed_url.scheme == "http" or parsed_url.scheme == "https"
    except Exception:
        return False


def _can_use_proxy(settings, authority):
    """
    Return `True` if an annotation can be shown via the proxy service.

    This currently only considers the authority but in future it could also
    incorporate checks for whether the target page embeds Hypothesis.

    :param settings: App settings dict
    :param authority: Authority of annotation's user
    """

    # The proxy service can only be used with pages that use first party
    # accounts, because third-party accounts require the host page to supply
    # login information to the client, which in turn relies on the user's cookie
    # session and therefore does not work properly through the proxy.
    return settings["hypothesis_authority"] == authority


def includeme(config):  # pragma: nocover
    config.add_route("index", "/")
    config.add_route("healthcheck", "/_status")
    config.add_route("crash", "/_crash")
    config.add_route("goto_url", "/go")
    config.add_route("annotation_with_url", "/{id}/*url")
    config.add_route("annotation_without_url", "/{id}")
    config.scan(__name__)
