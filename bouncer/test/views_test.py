import json

from elasticsearch import exceptions
import mock
from pyramid import httpexceptions
from pyramid import testing
import pytest

from bouncer import views


def test_parse_document_raises_if_no_uri():
    with pytest.raises(views.InvalidAnnotationError) as exc:
        views.parse_document({
            "_id": "annotation_id",
            "_source": {}  # No "uri".
        })
    assert exc.value.reason == "annotation_has_no_uri"


def test_parse_document_raises_if_uri_not_a_string():
    with pytest.raises(views.InvalidAnnotationError) as exc:
        views.parse_document({
            "_id": "annotation_id",
            "_source": {"uri": 52}  # "uri" isn't a string.
        })
    assert exc.value.reason == "uri_not_a_string"


def test_parse_document_returns_annotation_id():
    annotation_id = views.parse_document({
        "_id": "annotation_id",
        "_source": {"uri": "http://example.com/example.html"}
    })[0]

    assert annotation_id == "annotation_id"


def test_parse_document_returns_document_uri():
    document_uri = views.parse_document({
        "_id": "annotation_id",
        "_source": {"uri": "http://example.com/example.html"}
    })[1]

    assert document_uri == "http://example.com/example.html"


@pytest.mark.usefixtures("elasticsearch")
@pytest.mark.usefixtures("parse_document")
@pytest.mark.usefixtures("statsd")
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

    def test_annotation_increments_stat_if_get_raises_NotFoundError(
            self, elasticsearch, statsd):
        elasticsearch.Elasticsearch.return_value.get.side_effect = (
            exceptions.NotFoundError)

        try:
            views.AnnotationController(mock_request()).annotation()
        except:
            pass

        statsd.incr.assert_called_once_with(
            "views.annotation.404.annotation_not_found")

    def test_annotation_raises_HTTPNotFound_if_get_raises_NotFoundError(
            self, elasticsearch):
        elasticsearch.Elasticsearch.return_value.get.side_effect = (
            exceptions.NotFoundError)
        with pytest.raises(httpexceptions.HTTPNotFound):
            views.AnnotationController(mock_request()).annotation()

    def test_annotation_calls_parse_document(self,
                                             elasticsearch,
                                             parse_document):
        views.AnnotationController(mock_request()).annotation()

        parse_document.assert_called_once_with(
            elasticsearch.Elasticsearch.return_value.get.return_value)

    def test_annotation_increments_stat_if_parse_document_raises(self,
                                                                 parse_document,
                                                                 statsd):
        parse_document.side_effect = views.InvalidAnnotationError(
            "error message", "the_reason")

        try:
            views.AnnotationController(mock_request()).annotation()
        except:
            pass

        statsd.incr.assert_called_once_with("views.annotation.422.the_reason")

    def test_annotation_raises_if_parse_document_raises(self, parse_document):
        parse_document.side_effect = views.InvalidAnnotationError(
            "error message", "the_reason")

        with pytest.raises(httpexceptions.HTTPUnprocessableEntity) as exc:
            views.AnnotationController(mock_request()).annotation()
        assert str(exc.value) == "error message"

    def test_annotation_increments_stat_for_file_URLs(
            self, parse_document, statsd):
        parse_document.return_value[1] = "file:///home/seanh/Foo.pdf"

        try:
            views.AnnotationController(mock_request()).annotation()
        except:
            pass

        statsd.incr.assert_called_once_with(
            "views.annotation.422.not_an_http_or_https_document")

    def test_annotation_raises_HTTPUnprocessableEntity_for_file_URLs(
            self, parse_document):
        parse_document.return_value[1] = "file:///home/seanh/Foo.pdf"

        with pytest.raises(httpexceptions.HTTPUnprocessableEntity):
            views.AnnotationController(mock_request()).annotation()

    def test_annotation_increments_stat_when_annotation_found(self, statsd):
        views.AnnotationController(mock_request()).annotation()

        statsd.incr.assert_called_once_with(
            "views.annotation.200.annotation_found")

    def test_annotation_returns_via_url(self):
        template_data = views.AnnotationController(mock_request()).annotation()

        data = json.loads(template_data["data"])
        assert data["viaUrl"] == (
                "https://via.hypothes.is/http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q")

    def test_annotation_returns_extension_url(self):
        template_data = views.AnnotationController(mock_request()).annotation()

        data = json.loads(template_data["data"])
        assert data["extensionUrl"] == (
                "http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q")

    def test_annotation_strips_fragment_identifiers(self, parse_document):
        parse_document.return_value[1] = (
            "http://example.com/example.html#foobar")
        template_data = views.AnnotationController(mock_request()).annotation()

        data = json.loads(template_data["data"])

        assert data["extensionUrl"] == (
            "http://example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q")
        assert data["viaUrl"] == (
                "https://via.hypothes.is/http://example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q")

    def test_annotation_strips_bare_fragment_identifiers(self, parse_document):
        parse_document.return_value[1] = "http://example.com/example.html#"
        template_data = views.AnnotationController(mock_request()).annotation()

        data = json.loads(template_data["data"])

        assert data["extensionUrl"] == (
            "http://example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q")
        assert data["viaUrl"] == (
                "https://via.hypothes.is/http://example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q")


@pytest.mark.usefixtures("statsd")
def test_index_increments_stat(statsd):
    try:
        views.index(mock_request())
    except:
        pass

    statsd.incr.assert_called_once_with(
        "views.index.302.redirected_to_hypothesis")


@pytest.mark.usefixtures("statsd")
def test_index_redirects_to_hypothesis():
    with pytest.raises(httpexceptions.HTTPFound) as exc:
        views.index(mock_request())
    assert exc.value.location == "https://hypothes.is"


def test_httpexception_sets_status_code():
    request = testing.DummyRequest()

    views.httpexception(mock.Mock(status_int=404), request)

    assert request.response.status_int == 404


def test_httpexception_returns_error_message():
    exc = mock.Mock(status_int=404,
                    __str__=lambda self: "Annotation not found")

    template_data = views.httpexception(exc, testing.DummyRequest())

    assert template_data["message"] == "Annotation not found"


@pytest.fixture
def elasticsearch(request):
    patcher = mock.patch("bouncer.views.elasticsearch")
    elasticsearch = patcher.start()
    request.addfinalizer(patcher.stop)
    elasticsearch.Elasticsearch.return_value.get.return_value = {
        "_id": "AVLlVTs1f9G3pW-EYc6q",
        "_source": {"uri": "http://www.example.com/example.html"}
    }
    return elasticsearch


@pytest.fixture
def parse_document(request):
    patcher = mock.patch("bouncer.views.parse_document")
    parse_document = patcher.start()
    parse_document.return_value = [
        "AVLlVTs1f9G3pW-EYc6q", "http://www.example.com/example.html"]
    request.addfinalizer(patcher.stop)
    return parse_document


@pytest.fixture
def statsd(request):
    patcher = mock.patch("bouncer.views.statsd")
    statsd = patcher.start()
    request.addfinalizer(patcher.stop)
    return statsd


def mock_request():
    request = testing.DummyRequest()
    request.registry.settings = {"elasticsearch_host": "http://localhost/",
                                 "elasticsearch_port": "9200",
                                 "elasticsearch_index": "annotator",
                                 "hypothesis_url": "https://hypothes.is",
                                 "via_base_url": "https://via.hypothes.is"}
    request.matchdict = {"id": "AVLlVTs1f9G3pW-EYc6q"}
    return request
