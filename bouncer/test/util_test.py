import pytest

from bouncer import util


def test_parse_document_raises_if_no_uri():
    with pytest.raises(util.InvalidAnnotationError) as exc:
        util.parse_document({
            "_id": "annotation_id",
            "_source": {}  # No "uri".
        })
    assert exc.value.reason == "annotation_has_no_uri"


def test_parse_document_raises_if_uri_not_a_string():
    with pytest.raises(util.InvalidAnnotationError) as exc:
        util.parse_document({
            "_id": "annotation_id",
            "_source": {"target": [{"source": 52}]}  # "uri" isn't a string.
        })
    assert exc.value.reason == "uri_not_a_string"


def test_parse_document_returns_annotation_id():
    annotation_id = util.parse_document({
        "_id": "annotation_id",
        "_source": {"target": [{"source": "http://example.com/example.html"}]}
    })[0]

    assert annotation_id == "annotation_id"


def test_parse_document_returns_document_uri():
    document_uri = util.parse_document({
        "_id": "annotation_id",
        "_source": {"target": [{"source": "http://example.com/example.html"}]}
    })[1]

    assert document_uri == "http://example.com/example.html"


def test_parse_document_returns_document_uri_from_web_uri_when_pdf():
    document_uri = util.parse_document({
        "_id": "annotation_id",
        "_source": {
            "target": [{"source": "urn:x-pdf:the-fingerprint"}],
            "document": {"web_uri": "http://example.com/foo.pdf"}
        }
    })[1]

    assert document_uri == "http://example.com/foo.pdf"


def test_parse_document_raises_when_uri_from_web_uri_not_string_for_pdfs():
    with pytest.raises(util.InvalidAnnotationError) as exc:
        util.parse_document({
            "_id": "annotation_id",
            "_source": {
                "target": [{"source": "urn:x-pdf:the-fingerprint"}],
                "document": {"web_uri": 52}
            }
        })
    assert exc.value.reason == "uri_not_a_string"
