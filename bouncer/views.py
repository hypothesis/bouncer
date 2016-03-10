import json
from urllib import parse

from elasticsearch import exceptions
from pyramid import httpexceptions
from pyramid import i18n
from pyramid import view
from statsd.defaults.env import statsd

from bouncer import util


_ = i18n.TranslationStringFactory(__package__)


@view.view_defaults(renderer="bouncer:templates/annotation.html.jinja2")
class AnnotationController(object):

    def __init__(self, request):
        self.request = request

    @view.view_config(route_name="annotation_with_url")
    @view.view_config(route_name="annotation_without_url")
    def annotation(self):
        settings = self.request.registry.settings

        try:
            document = util.elasticsearch_client(settings).get(
                index=settings["elasticsearch_index"],
                doc_type="annotation",
                id=self.request.matchdict["id"])
        except exceptions.NotFoundError:
            statsd.incr("views.annotation.404.annotation_not_found")
            raise httpexceptions.HTTPNotFound(_("Annotation not found"))

        try:
            annotation_id, document_uri = util.parse_document(document)
        except util.InvalidAnnotationError as exc:
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
                  "To view its annotations, a document's address must start "
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
                "chromeExtensionId": settings["chrome_extension_id"],
                "viaUrl": via_url,
                "extensionUrl": extension_url,
            })
        }


@view.view_config(renderer="bouncer:templates/index.html.jinja2",
                  route_name="index")
def index(request):
    statsd.incr("views.index.302.redirected_to_hypothesis")
    raise httpexceptions.HTTPFound(
        location=request.registry.settings["hypothesis_url"])


@view.view_defaults(renderer='bouncer:templates/error.html.jinja2')
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
        return {"message": _("Sorry, but something went wrong with the link. "
                             "The issue has been reported and we'll try to "
                             "fix it.")}


def includeme(config):
    config.add_route("index", "/")
    config.add_route("annotation_with_url", "/{id}/*url")
    config.add_route("annotation_without_url", "/{id}")
    config.scan(__name__)
