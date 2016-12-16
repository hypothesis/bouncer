import json

from elasticsearch import exceptions
import mock
from pyramid import httpexceptions
from pyramid import testing
import pytest

from bouncer import util
from bouncer import views


@pytest.mark.usefixtures("parse_document")
@pytest.mark.usefixtures("statsd")
class TestAnnotationController(object):

    def test_annotation_calls_get(self):
        request = mock_request()
        views.AnnotationController(request).annotation()

        request.es.get.assert_called_once_with(
            index="hypothesis",
            doc_type="annotation",
            id="AVLlVTs1f9G3pW-EYc6q"
        )

    def test_annotation_increments_stat_if_get_raises_NotFoundError(self, statsd):
        request = mock_request()
        request.es.get.side_effect = exceptions.NotFoundError

        try:
            views.AnnotationController(request).annotation()
        except:
            pass

        statsd.incr.assert_called_once_with(
            "views.annotation.404.annotation_not_found")

    def test_annotation_raises_HTTPNotFound_if_get_raises_NotFoundError(self):
        request = mock_request()
        request.es.get.side_effect = exceptions.NotFoundError

        with pytest.raises(httpexceptions.HTTPNotFound):
            views.AnnotationController(request).annotation()

    def test_annotation_calls_parse_document(self, parse_document):
        request = mock_request()

        views.AnnotationController(request).annotation()

        parse_document.assert_called_once_with(request.es.get.return_value)

    def test_annotation_increments_stat_if_parse_document_raises(self,
                                                                 parse_document,
                                                                 statsd):
        parse_document.side_effect = util.InvalidAnnotationError(
            "error message", "the_reason")

        try:
            views.AnnotationController(mock_request()).annotation()
        except:
            pass

        statsd.incr.assert_called_once_with("views.annotation.422.the_reason")

    def test_annotation_raises_if_parse_document_raises(self, parse_document):
        parse_document.side_effect = util.InvalidAnnotationError(
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

    def test_annotation_returns_chrome_extension_id(self):
        template_data = views.AnnotationController(mock_request()).annotation()

        data = json.loads(template_data["data"])
        assert data["chromeExtensionId"] == "test-extension-id"

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

    def test_annotation_returns_pretty_url(self):
        template_data = views.AnnotationController(mock_request()).annotation()

        assert template_data["pretty_url"] == "www.example.com"

    def test_annotation_truncates_pretty_url(self, parse_document):
        parse_document.return_value[1] = (
            "http://www.abcdefghijklmnopqrst.com/example.html")

        template_data = views.AnnotationController(mock_request()).annotation()

        assert template_data["pretty_url"] == "www.abcdefghijklmnop&hellip;"


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


class TestErrorController(object):

    def test_httperror_sets_status_code(self):
        request = mock_request()

        views.ErrorController(
            httpexceptions.HTTPNotFound(), request).httperror()

        assert request.response.status_int == 404

    def test_httperror_returns_error_message(self):
        exc = httpexceptions.HTTPNotFound("Annotation not found")
        controller = views.ErrorController(exc, mock_request())

        template_data = controller.httperror()

        assert template_data["message"] == "Annotation not found"

    def test_error_sets_status_code(self):
        request = mock_request()

        views.ErrorController(Exception(), request).error()

        assert request.response.status_int == 500

    def test_error_raises_in_debug_mode(self):
        request = mock_request()
        request.registry.settings["debug"] = True

        with pytest.raises(Exception):
            views.ErrorController(Exception(), request).error()

    def test_error_reports_to_sentry(self):
        request = mock_request()

        views.ErrorController(Exception(), request).error()

        request.raven.captureException.assert_called_once_with()

    def test_error_returns_error_message(self):
        controller = views.ErrorController(Exception(), mock_request())

        template_data = controller.error()

        assert template_data["message"].startswith("Sorry, but")


@pytest.fixture
def parse_document(request):
    patcher = mock.patch("bouncer.views.util.parse_document")
    parse_document = patcher.start()
    request.addfinalizer(patcher.stop)
    parse_document.return_value = [
        "AVLlVTs1f9G3pW-EYc6q", "http://www.example.com/example.html"]
    return parse_document


@pytest.fixture
def statsd(request):
    patcher = mock.patch("bouncer.views.statsd")
    statsd = patcher.start()
    request.addfinalizer(patcher.stop)
    return statsd


def mock_request():
    request = testing.DummyRequest()
    request.registry.settings = {"chrome_extension_id": "test-extension-id",
                                 "debug": False,
                                 "elasticsearch_host": "http://localhost/",
                                 "elasticsearch_port": "9200",
                                 "elasticsearch_index": "hypothesis",
                                 "hypothesis_url": "https://hypothes.is",
                                 "via_base_url": "https://via.hypothes.is"}
    request.matchdict = {"id": "AVLlVTs1f9G3pW-EYc6q"}
    request.es = mock.Mock()
    request.es.get.return_value = {
        "_id": "AVLlVTs1f9G3pW-EYc6q",
        "_source": {"uri": "http://www.example.com/example.html"}
    }
    request.raven = mock.Mock()
    return request
