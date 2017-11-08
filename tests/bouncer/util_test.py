import pytest

from bouncer import util


def test_parse_document_raises_if_annotated_deleted():
    # When an annotation is deleted in h it isn't immediately removed from the
    # search index. Its Elasticsearch document is temporarily updated to just
    # {'deleted': True}.
    with pytest.raises(util.DeletedAnnotationError) as exc:
        util.parse_document({
            "_id": "annotation_id",
            "_source": {
                "deleted": True,
            },
        })


def test_parse_document_raises_if_no_uri():
    with pytest.raises(util.InvalidAnnotationError) as exc:
        util.parse_document({
            "_id": "annotation_id",
            "_source": {
                "target": [{  # no uri
                            "selector": []
                            }],
                "group": "__world__",
                "shared": True
            }
        })
    assert exc.value.reason == "annotation_has_no_uri"


def test_parse_document_raises_if_uri_not_a_string():
    with pytest.raises(util.InvalidAnnotationError) as exc:
        util.parse_document({
            "_id": "annotation_id",
            "_source": {
                "target": [{
                            "source": 52,  # "uri" isn't a string.
                            "selector": []
                            }],
                "group": "__world__",
                "shared": True
            }
        })
    assert exc.value.reason == "uri_not_a_string"


def test_parse_document_returns_annotation_id():
    annotation_id = util.parse_document({
        "_id": "annotation_id",
        "_source": {
            "target": [{
                "source": "http://example.com/example.html",
                "selector": [],
            }],
            "group": "__world__",
            "shared": True
        }
    })["annotation_id"]

    assert annotation_id == "annotation_id"


def test_parse_document_returns_document_uri():
    document_uri = util.parse_document({
        "_id": "annotation_id",
        "_source": {
            "target": [{
                "source": "http://example.com/example.html",
                "selector": []
            }],
            "group": "__world__",
            "shared": True
        }
    })["document_uri"]

    assert document_uri == "http://example.com/example.html"


def test_parse_document_returns_quote():
    parsed_document = util.parse_document({
        "_id": "annotation_id",
        "_source": {
            "target": [{
                                "source": "http://example.com/example.html",
                                "selector": [{
                                    "type": "TextQuoteSelector",
                                    "exact": "test_quote"
                                }]
                                }],
            "group": "__world__",
            "shared": True
        }
    })
    quote = parsed_document["quote"]

    assert quote == "test_quote"


def test_parse_document_returns_boilerplate_quote_when_no_quote():
    parsed_document = util.parse_document({
        "_id": "annotation_id",
        "_source": {
            "target": [{
                                "source": "http://example.com/example.html",
                                }],
            "group": "__world__",
            "shared": True
        }
    })
    quote = parsed_document["quote"]

    assert quote == "Hypothesis annotation for example.com"


def test_parse_document_returns_text():
    text = util.parse_document({
        "_id": "annotation_id",
        "_source": {
            "target": [{
                "source": "http://example.com/example.html",
                "selector": [{}]
            }],
            "group": "__world__",
            "shared": True,
            "text": "test_text"
        }
    })["text"]

    assert text == "test_text"


def test_parse_document_returns_boilerplate_when_no_text():
    text = util.parse_document({
        "_id": "annotation_id",
        "_source": {
            "target": [{
                "source": "http://example.com/example.html",
                "selector": [{}]
            }],
            "group": "__world__",
            "shared": True,
            "text": ""
        }
    })["text"]

    assert text == util.ANNOTATION_BOILERPLATE_TEXT


def test_parse_document_returns_show_metadata_true_when_shared_and_world():
    show_metadata = util.parse_document({
        "_id": "annotation_id",
        "_source": {
            "target": [{
                "source": "http://example.com/example.html",
                "selector": [{}]
            }],
            "group": "__world__",
            "shared": True
        }
    })["show_metadata"]

    assert show_metadata is True


def test_parse_document_returns_document_uri_from_web_uri_when_pdf():
    document_uri = util.parse_document({
        "_id": "annotation_id",
        "_source": {
            "target": [{
                "source": "urn:x-pdf:the-fingerprint",
                "selector": []
            }],
            "group": "__world__",
            "shared": True,
            "document": {"web_uri": "http://example.com/foo.pdf"}
        }
    })["document_uri"]

    assert document_uri == "http://example.com/foo.pdf"


def test_parse_document_raises_when_uri_from_web_uri_not_string_for_pdfs():
    with pytest.raises(util.InvalidAnnotationError) as exc:
        util.parse_document({
            "_id": "annotation_id",
            "_source": {
                "target": [{
                            "source": "urn:x-pdf:the-fingerprint",
                            "selector": []
                            }],
                "group": "__world__",
                "shared": True,
                "document": {"web_uri": 52}
            }
        })
    assert exc.value.reason == "uri_not_a_string"
