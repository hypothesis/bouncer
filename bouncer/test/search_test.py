from mock import (
    ANY,
    MagicMock,
    patch,
)

from elasticsearch import Elasticsearch

from bouncer.search import get_client, includeme


class TestGetClient(object):
    def test_returns_client(self):
        client = get_client({'elasticsearch_host': 'foo',
                             'elasticsearch_port': 9200})

        assert isinstance(client, Elasticsearch)

    @patch('bouncer.search.Elasticsearch')
    def test_configures_client(self, es_mock):
        get_client({'elasticsearch_host': 'foo',
                    'elasticsearch_port': 9200})


        es_mock.assert_called_once_with([{'host': 'foo', 'port': 9200}])


def test_includeme():
    configurator = MagicMock()

    includeme(configurator)

    configurator.add_request_method.assert_called_once_with(ANY,
                                                            name='es',
                                                            reify=True)

