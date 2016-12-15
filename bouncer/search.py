import certifi
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth


def get_client(settings):
    """Return a client for the Elasticsearch index."""
    host = {'host': settings['elasticsearch_host'],
            'port': settings['elasticsearch_port']}
    kwargs = {}

    have_aws_creds = ('elasticsearch_aws_access_key_id' in settings and
                      'elasticsearch_aws_secret_access_key' in settings and
                      'elasticsearch_aws_region' in settings)
    if have_aws_creds:
        auth = AWS4Auth(settings['elasticsearch_aws_access_key_id'],
                        settings['elasticsearch_aws_secret_access_key'],
                        settings['elasticsearch_aws_region'],
                        'es')

        kwargs['http_auth'] = auth
        kwargs['use_ssl'] = True
        kwargs['verify_certs'] = True
        kwargs['ca_certs'] = certifi.where()
        kwargs['connection_class'] = RequestsHttpConnection

    return Elasticsearch([host], **kwargs)


def includeme(config):
    settings = config.registry.settings
    settings.setdefault('elasticsearch_host', 'localhost')
    settings.setdefault('elasticsearch_port', 9200)

    config.registry['es.client'] = get_client(settings)
    config.add_request_method(lambda r: r.registry['es.client'],
                              name='es',
                              reify=True)
