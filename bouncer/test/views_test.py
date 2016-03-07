import json

from elasticsearch import exceptions
import mock
from pyramid import httpexceptions
from pyramid import testing
import pytest

from bouncer import views


@mock.patch("bouncer.views.elasticsearch")
class TestAnnotationController(object):

    def test_annotation_inits_elasticsearch_client(self, elasticsearch):
        views.AnnotationController(mock_request()).annotation()

        elasticsearch.Elasticsearch.assert_called_once_with(
            host="http://localhost/", port="9200"
        )

    def test_annotation_calls_get(self, elasticsearch):
        views.AnnotationController(mock_request()).annotation()

        elasticsearch.Elasticsearch.return_value.get.assert_called_once_with(
            index="annotator",
            doc_type="annotation",
            id="AVLlVTs1f9G3pW-EYc6q"
        )

    def test_annotation_raises_HTTPNotFound_if_get_raises_NotFoundError(
            self, elasticsearch):
        elasticsearch.Elasticsearch.return_value.get.side_effect = (
            exceptions.NotFoundError)
        with pytest.raises(httpexceptions.HTTPNotFound):
            views.AnnotationController(mock_request()).annotation()

    def test_annotation_returns_via_url(self, elasticsearch):
        elasticsearch.Elasticsearch.return_value.get.return_value = {
            "_id": "AVLlVTs1f9G3pW-EYc6q",
            "_source": {"uri": "http://www.example.com/example.html"}
        }
        template_data = views.AnnotationController(mock_request()).annotation()

        data = json.loads(template_data["data"])
        assert data["viaUrl"] == (
                "https://via.hypothes.is/http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q")

    def test_annotation_returns_extension_url(self, elasticsearch):
        elasticsearch.Elasticsearch.return_value.get.return_value = {
            "_id": "AVLlVTs1f9G3pW-EYc6q",
            "_source": {"uri": "http://www.example.com/example.html"}
        }
        template_data = views.AnnotationController(mock_request()).annotation()

        data = json.loads(template_data["data"])
        assert data["extensionUrl"] == (
                "http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q")


def test_index_redirects_to_hypothesis():
    with pytest.raises(httpexceptions.HTTPFound) as exc:
        views.index(mock_request())
    assert exc.value.location == "https://hypothes.is"


def test_notfound_404s():
    request = testing.DummyRequest()

    views.notfound(request)

    assert request.response.status_int == 404


def mock_request():
    request = testing.DummyRequest()
    request.registry.settings = {"elasticsearch_host": "http://localhost/",
                                 "elasticsearch_port": "9200",
                                 "elasticsearch_index": "annotator",
                                 "sentry_dsn": "{PROTOCOL}://{PUBLIC_KEY}:{SECRET_KEY}@{HOST}/{PATH}{PROJECT_ID}",
                                 "sentry_javascript_dsn": "{PROTOCOL}://{PUBLIC_KEY}@{HOST}/{PATH}{PROJECT_ID}",
                                 "hypothesis_url": "https://hypothes.is",
                                 "via_base_url": "https://via.hypothes.is"}
    request.matchdict = {"id": "AVLlVTs1f9G3pW-EYc6q"}
    return request
