from elasticsearch import Elasticsearch
from mock import ANY, MagicMock, patch

from bouncer.search import get_client, includeme


class TestGetClient(object):
    def test_returns_client(self):
        client = get_client({"elasticsearch_url": "foo:9200"})

        assert isinstance(client, Elasticsearch)

    @patch("bouncer.search.Elasticsearch")
    def test_configures_client(self, es_mock):
        get_client({"elasticsearch_url": "foo:9200"})

        es_mock.assert_called_once_with(["foo:9200"])


def test_includeme():
    configurator = MagicMock()
    configurator.registry.settings = {"elasticsearch_url": "foo:9200"}

    includeme(configurator)

    configurator.add_request_method.assert_called_once_with(ANY, name="es", reify=True)
