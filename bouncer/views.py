import json

import elasticsearch
from elasticsearch import exceptions
from pyramid import httpexceptions
from pyramid import view
from statsd.defaults.env import statsd


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
            raise httpexceptions.HTTPNotFound()

        annotation_id = document["_id"]
        document_uri = document["_source"]["uri"]

        # FIXME: Strip query params, anchors from document_uri here?

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


@view.notfound_view_config(
    append_slash=True,
    renderer='bouncer:templates/notfound.html.jinja2')
def notfound(request):
    request.response.status_int = 404
    return {}


def includeme(config):
    config.add_route("index", "/")
    config.add_route("annotation_with_url", "/{id}/*url")
    config.add_route("annotation_without_url", "/{id}/")
    config.scan(__name__)
