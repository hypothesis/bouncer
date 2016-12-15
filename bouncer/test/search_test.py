from mock import (
    ANY,
    MagicMock,
    patch,
)

import certifi
from elasticsearch import Elasticsearch, RequestsHttpConnection

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

    @patch('bouncer.search.AWS4Auth')
    @patch('bouncer.search.Elasticsearch')
    def test_configures_aws_auth(self, es_mock, awsauth_mock):
        get_client({'elasticsearch_host': 'foo',
                    'elasticsearch_port': 9200,
                    'elasticsearch_aws_access_key_id': 'foo',
                    'elasticsearch_aws_secret_access_key': 'bar',
                    'elasticsearch_aws_region': 'spain'})

        awsauth_mock.assert_called_once_with('foo', 'bar', 'spain', 'es')

    @patch('bouncer.search.AWS4Auth')
    @patch('bouncer.search.Elasticsearch')
    def test_configures_es_for_aws_auth(self, es_mock, awsauth_mock):
        auth_result = awsauth_mock.return_value
        get_client({'elasticsearch_host': 'foo',
                    'elasticsearch_port': 9200,
                    'elasticsearch_aws_access_key_id': 'foo',
                    'elasticsearch_aws_secret_access_key': 'bar',
                    'elasticsearch_aws_region': 'spain'})

        es_mock.assert_called_once_with([{'host': 'foo', 'port': 9200}],
                                        http_auth=auth_result,
                                        use_ssl=True,
                                        verify_certs=True,
                                        ca_certs=certifi.where(),
                                        connection_class=RequestsHttpConnection)


def test_includeme():
    configurator = MagicMock()

    includeme(configurator)

    configurator.add_request_method.assert_called_once_with(ANY,
                                                            name='es',
                                                            reify=True)

