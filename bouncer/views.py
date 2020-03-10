import json
from urllib import parse

from elasticsearch import exceptions
from pyramid import httpexceptions, i18n, view

from bouncer import __version__ as bouncer_version
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
            document = self.request.es.get(
                index=settings["elasticsearch_index"],
                doc_type="annotation",
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

        return {
            "data": json.dumps(
                {
                    # Warning: variable names change from python_style to
                    # javaScriptStyle here!
                    "chromeExtensionId": settings["chrome_extension_id"],
                    "viaUrl": via_url,
                    "extensionUrl": extension_url,
                }
            ),
            "show_metadata": show_metadata,
            "pretty_url": pretty_url,
            "quote": quote,
            "text": text,
            "title": title,
        }


@view.view_config(renderer="bouncer:templates/index.html.jinja2", route_name="index")
def index(request):
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
                "chromeExtensionId": settings["chrome_extension_id"],
                "viaUrl": via_url,
                "extensionUrl": extension_url,
            }
        ),
        "pretty_url": pretty_url,
    }


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
        # In debug mode re-raise exceptions so that they get printed in the
        # terminal.
        if self.request.registry.settings["debug"]:
            raise

        self.request.response.status_int = 500

        # If code raises a non-HTTPException exception we assume it was a bug
        # and:
        # 1. Show the user a generic error page
        # 2. Report the details of the error to Sentry.
        self.request.raven.captureException()
        return {
            "message": _(
                "Sorry, but something went wrong with the link. "
                "The issue has been reported and we'll try to "
                "fix it."
            )
        }


@view.view_config(route_name="healthcheck", renderer="json")
def healthcheck(request):
    index = request.registry.settings["elasticsearch_index"]
    try:
        status = request.es.cluster.health(index=index)["status"]
    except exceptions.ElasticsearchException as exc:
        raise FailedHealthcheck("elasticsearch exception") from exc
    if status not in ("yellow", "green"):
        raise FailedHealthcheck("cluster status was {!r}".format(status))
    return {"status": "ok", "version": bouncer_version}


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


def includeme(config):
    config.add_route("index", "/")
    config.add_route("healthcheck", "/_status")
    config.add_route("goto_url", "/go")
    config.add_route("annotation_with_url", "/{id}/*url")
    config.add_route("annotation_without_url", "/{id}")
    config.scan(__name__)
