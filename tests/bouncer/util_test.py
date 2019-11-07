import pytest

from bouncer import util


def test_parse_document_raises_if_annotated_deleted():
    # When an annotation is deleted in h it isn't immediately removed from the
    # search index. Its Elasticsearch document is temporarily updated to just
    # {'deleted': True}.
    with pytest.raises(util.DeletedAnnotationError):
        util.parse_document({"_id": "annotation_id", "_source": {"deleted": True}})


def test_parse_document_raises_if_no_uri(es_annotation_doc):
    del es_annotation_doc["_source"]["target"][0]["source"]

    with pytest.raises(util.InvalidAnnotationError) as exc:
        util.parse_document(es_annotation_doc)

    assert exc.value.reason == "annotation_has_no_uri"


def test_parse_document_raises_if_uri_not_a_string(es_annotation_doc):
    es_annotation_doc["_source"]["target"][0]["source"] = 52

    with pytest.raises(util.InvalidAnnotationError) as exc:
        util.parse_document(es_annotation_doc)

    assert exc.value.reason == "uri_not_a_string"


def test_parse_document_returns_annotation_id(es_annotation_doc):
    annotation_id = util.parse_document(es_annotation_doc)["annotation_id"]
    assert annotation_id == "annotation_id"


def test_parse_document_returns_document_uri(es_annotation_doc):
    document_uri = util.parse_document(es_annotation_doc)["document_uri"]
    assert document_uri == "http://example.com/example.html"


def test_parse_document_returns_quote(es_annotation_doc):
    es_annotation_doc["_source"]["target"][0]["selector"] = [
        {"type": "TextQuoteSelector", "exact": "test_quote"}
    ]
    quote = util.parse_document(es_annotation_doc)["quote"]
    assert quote == "test_quote"


@pytest.mark.parametrize(
    "selector",
    [
        # No selector (ie. a page note).
        None,
        # No quote selector. Allowed by the service even though a quote is required
        # to anchor the annotation.
        [{"type": "TextPositionSelector"}],
    ],
)
def test_parse_document_returns_boilerplate_quote_when_no_quote(
    es_annotation_doc, selector
):
    if selector:
        es_annotation_doc["_source"]["target"][0]["selector"] = selector
    quote = util.parse_document(es_annotation_doc)["quote"]
    assert quote == "Hypothesis annotation for example.com"


def test_parse_document_returns_text(es_annotation_doc):
    es_annotation_doc["_source"]["text"] = "test_text"
    text = util.parse_document(es_annotation_doc)["text"]
    assert text == "test_text"


def test_parse_document_returns_boilerplate_when_no_text(es_annotation_doc):
    text = util.parse_document(es_annotation_doc)["text"]
    assert text == util.ANNOTATION_BOILERPLATE_TEXT


def test_parse_document_returns_show_metadata_true_when_shared_and_world(
    es_annotation_doc,
):
    show_metadata = util.parse_document(es_annotation_doc)["show_metadata"]
    assert show_metadata is True


def test_parse_document_returns_document_uri_from_web_uri_when_pdf(es_annotation_doc):
    es_annotation_doc["_source"]["target"][0]["source"] = "urn:x-pdf:the-fingerprint"
    es_annotation_doc["_source"]["document"] = {"web_uri": "http://example.com/foo.pdf"}

    document_uri = util.parse_document(es_annotation_doc)["document_uri"]

    assert document_uri == "http://example.com/foo.pdf"


def test_parse_document_raises_when_uri_from_web_uri_not_string_for_pdfs(
    es_annotation_doc,
):
    es_annotation_doc["_source"]["target"][0]["source"] = "urn:x-pdf:the-fingerprint"
    es_annotation_doc["_source"]["document"] = {"web_uri": 52}

    with pytest.raises(util.InvalidAnnotationError) as exc:
        util.parse_document(es_annotation_doc)

    assert exc.value.reason == "uri_not_a_string"


def test_parse_document_returns_authority(es_annotation_doc):
    authority = util.parse_document(es_annotation_doc)["authority"]
    assert authority == "hypothes.is"


@pytest.fixture
def es_annotation_doc():
    """
    Minimal JSON document for an annotation as returned from Elasticsearch.

    This contains only fields which can be assumed to exist on all annotations.
    """
    return {
        "_id": "annotation_id",
        "_source": {
            "authority": "hypothes.is",
            "target": [{"source": "http://example.com/example.html"}],
            "group": "__world__",
            "shared": True,
        },
    }
