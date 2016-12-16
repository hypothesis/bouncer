from elasticsearch import Elasticsearch


def get_client(settings):
    """Return a client for the Elasticsearch index."""
    host = {'host': settings['elasticsearch_host'],
            'port': settings['elasticsearch_port']}

    return Elasticsearch([host])


def includeme(config):
    settings = config.registry.settings
    settings.setdefault('elasticsearch_host', 'localhost')
    settings.setdefault('elasticsearch_port', 9200)

    config.registry['es.client'] = get_client(settings)
    config.add_request_method(lambda r: r.registry['es.client'],
                              name='es',
                              reify=True)
