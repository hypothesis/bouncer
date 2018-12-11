from elasticsearch import Elasticsearch


def get_client(settings):
    """Return a client for the Elasticsearch index."""
    host = settings["elasticsearch_url"]
    kwargs = {}

    # nb. No AWS credentials here because we assume that if using AWS-managed
    # ES, the cluster lives inside a VPC.
    return Elasticsearch([host], **kwargs)


def includeme(config):
    settings = config.registry.settings
    settings.setdefault("elasticsearch_url", "http://localhost:9200")

    config.registry["es.client"] = get_client(settings)
    config.add_request_method(lambda r: r.registry["es.client"], name="es", reify=True)
