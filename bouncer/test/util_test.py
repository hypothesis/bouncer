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
            "_source": {"uri": 52}  # "uri" isn't a string.
        })
    assert exc.value.reason == "uri_not_a_string"


def test_parse_document_returns_annotation_id():
    annotation_id = util.parse_document({
        "_id": "annotation_id",
        "_source": {"uri": "http://example.com/example.html"}
    })[0]

    assert annotation_id == "annotation_id"


def test_parse_document_returns_document_uri():
    document_uri = util.parse_document({
        "_id": "annotation_id",
        "_source": {"uri": "http://example.com/example.html"}
    })[1]

    assert document_uri == "http://example.com/example.html"
