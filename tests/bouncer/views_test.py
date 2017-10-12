import json

from elasticsearch import exceptions as es_exceptions
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

    def test_annotation_increments_stat_if_get_raises_not_found_error(self,
                                                                      statsd):
        request = mock_request()
        request.es.get.side_effect = es_exceptions.NotFoundError

        try:
            views.AnnotationController(request).annotation()
        except:
            pass

        statsd.incr.assert_called_once_with(
            "views.annotation.404.annotation_not_found")

    def test_annotation_raises_http_not_found_if_annotation_deleted(self):
        request = mock_request()
        request.es.get.return_value['_source']['deleted'] = True

        with pytest.raises(httpexceptions.HTTPNotFound):
            views.AnnotationController(request).annotation()

    def test_annotation_raises_http_not_found_if_get_raises_not_found(self):
        request = mock_request()
        request.es.get.side_effect = es_exceptions.NotFoundError

        with pytest.raises(httpexceptions.HTTPNotFound):
            views.AnnotationController(request).annotation()

    def test_annotation_calls_parse_document(self, parse_document):
        request = mock_request()

        views.AnnotationController(request).annotation()

        parse_document.assert_called_once_with(request.es.get.return_value)

    def test_annotation_bumps_stat_if_parse_document_raises(self,
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

    def test_annotation_increments_stat_for_file_urls(
            self, parse_document, statsd):
        parse_document.return_value["document_uri"] = (
            "file:///home/seanh/Foo.pdf")

        try:
            views.AnnotationController(mock_request()).annotation()
        except:
            pass

        statsd.incr.assert_called_once_with(
            "views.annotation.422.not_an_http_or_https_document")

    def test_annotation_raises_http_unprocessable_entity_for_file_urls(
            self, parse_document):
        parse_document.return_value["document_uri"] = (
            "file:///home/seanh/Foo.pdf")

        with pytest.raises(httpexceptions.HTTPUnprocessableEntity):
            views.AnnotationController(mock_request()).annotation()

    def test_annotation_increments_stat_when_annotation_found(self, statsd):
        views.AnnotationController(mock_request()).annotation()

        statsd.incr.assert_called_once_with(
            "views.annotation.200.annotation_found")

    def test_annotation_returns_chrome_extension_id(self):
        template_data = (
            views.AnnotationController(mock_request()).annotation())

        data = json.loads(template_data["data"])
        assert data["chromeExtensionId"] == "test-extension-id"

    def test_annotation_returns_quote(self):
        template_data = (
            views.AnnotationController(mock_request()).annotation())

        quote = template_data["quote"]
        assert quote == "Hypothesis annotation for www.example.com"

    def test_annotation_returns_via_url(self):
        template_data = (
            views.AnnotationController(mock_request()).annotation())

        data = json.loads(template_data["data"])
        assert data["viaUrl"] == (
                "https://via.hypothes.is/http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q")

    def test_annotation_returns_extension_url(self):
        template_data = (
            views.AnnotationController(mock_request()).annotation())

        data = json.loads(template_data["data"])
        assert data["extensionUrl"] == (
                "http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q")

    def test_annotation_strips_fragment_identifiers(self, parse_document):
        parse_document.return_value["document_uri"] = (
            "http://example.com/example.html#foobar")
        template_data = (
            views.AnnotationController(mock_request()).annotation())

        data = json.loads(template_data["data"])

        assert data["extensionUrl"] == (
            "http://example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q")
        assert data["viaUrl"] == (
                "https://via.hypothes.is/http://example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q")

    def test_annotation_strips_bare_fragment_identifiers(self, parse_document):
        parse_document.return_value["document_uri"] = (
           "http://example.com/example.html#")
        template_data = (
            views.AnnotationController(mock_request()).annotation())

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


class TestGotoUrlController(object):

    def test_it_shows_redirect_page(self):
        request = mock_request()
        request.GET['url'] = 'https://example.com/'

        ctx = views.goto_url(request)

        assert ctx == {'data': json.dumps({
                         'chromeExtensionId': 'test-extension-id',
                         'viaUrl': 'https://via.hypothes.is/https://example.com/#annotations:query:',
                         'extensionUrl': 'https://example.com/#annotations:query:'}),
                       'pretty_url': 'example.com'}

    def test_it_sets_query_in_fragment(self):
        request = mock_request()
        request.GET['url'] = 'https://example.com/article.html'
        request.GET['q'] = 'user:jsmith'

        ctx = views.goto_url(request)

        data = json.loads(ctx['data'])
        expected_frag = '#annotations:query:user%3Ajsmith'
        assert data['viaUrl'].endswith(expected_frag)
        assert data['extensionUrl'].endswith(expected_frag)

    def test_it_rejects_invalid_or_missing_urls(self):
        invalid_urls = [None,

                        # Unsupported protocols.
                        'ftp://foo.bar',
                        'doi:10.1.2/345',
                        'file://foo.bar',

                        # Malformed URLs.
                        'http://goo\[g']

        for url in invalid_urls:
            request = mock_request()
            request.GET['url'] = url

            with pytest.raises(httpexceptions.HTTPBadRequest):
                views.goto_url(request)

    def test_it_allows_valid_http_urls(self):
        valid_urls = ['http://publisher.org',
                      'https://publisher.org',
                      'HTTP://PUBLISHER.ORG',
                      'HTTPS://example.com']

        for url in valid_urls:
            request = mock_request()
            request.GET['url'] = url

            views.goto_url(request)

    def test_it_strips_existing_fragment(self):
        request = mock_request()
        request.GET['url'] = 'https://example.com/#foobar'

        ctx = views.goto_url(request)

        data = json.loads(ctx['data'])
        assert data['viaUrl'] == 'https://via.hypothes.is/https://example.com/#annotations:query:'
        assert data['extensionUrl'] == 'https://example.com/#annotations:query:'


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


class TestHealthcheck(object):
    def test_ok(self):
        request = mock_request()
        request.es.cluster.health.return_value = {'status': 'green'}

        result = views.healthcheck(request)

        assert 'status' in result
        assert result['status'] == 'ok'

    def test_failed_es_request(self):
        request = mock_request()
        exc = es_exceptions.ConnectionTimeout()
        request.es.cluster.health.side_effect = exc

        with pytest.raises(views.FailedHealthcheck) as e:
            views.healthcheck(request)

        assert e.value.__cause__ == exc

    def test_wrong_cluster_status(self):
        request = mock_request()
        request.es.cluster.health.return_value = {'status': 'red'}

        with pytest.raises(views.FailedHealthcheck) as e:
            views.healthcheck(request)

        assert 'cluster status' in str(e.value)


@pytest.fixture
def parse_document(request):
    patcher = mock.patch("bouncer.views.util.parse_document")
    parse_document = patcher.start()
    request.addfinalizer(patcher.stop)
    parse_document.return_value = {
        "annotation_id": "AVLlVTs1f9G3pW-EYc6q",
        "document_uri": "http://www.example.com/example.html",
        "show_metadata": True,
        "quote": "Hypothesis annotation for www.example.com",
        "text": "test_text"
    }
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
        "_source": {
            "target": [{
                "source": "http://example.com/example.html",
                "selector": [],
            }],
            "uri": "http://www.example.com/example.html",
            "group": "__world__",
        }
    }
    request.raven = mock.Mock()
    return request
