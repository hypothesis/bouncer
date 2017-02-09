import os

import pyramid.config

from bouncer._version import get_version

__all__ = ('__version__',)
__version__ = get_version()


def settings():
    """
    Return the app's configuration settings as a dict.

    Settings are read from environment variables and fall back to hardcoded
    defaults if those variables aren't defined.

    """
    via_base_url = os.environ.get("VIA_BASE_URL", "https://via.hypothes.is")
    if via_base_url.endswith("/"):
        via_base_url = via_base_url[:-1]

    if "DEBUG" in os.environ:
        debug = True
    else:
        debug = False

    result = {
        "chrome_extension_id": os.environ.get(
            "CHROME_EXTENSION_ID",
            "bjfhmglciegochdpefhhlphglcehbmek"),
        "debug": debug,
        "elasticsearch_index": os.environ.get("ELASTICSEARCH_INDEX",
                                              "hypothesis"),
        "hypothesis_url": os.environ.get("HYPOTHESIS_URL",
                                         "https://hypothes.is"),
        "via_base_url": via_base_url,
    }

    if 'ELASTICSEARCH_HOST' in os.environ:
        result['elasticsearch_host'] = os.environ['ELASTICSEARCH_HOST']
    if 'ELASTICSEARCH_PORT' in os.environ:
        result['elasticsearch_port'] = int(os.environ['ELASTICSEARCH_PORT'])
    if 'ELASTICSEARCH_AWS_ACCESS_KEY_ID' in os.environ:
        result['elasticsearch_aws_access_key_id'] = os.environ['ELASTICSEARCH_AWS_ACCESS_KEY_ID']
    if 'ELASTICSEARCH_AWS_SECRET_ACCESS_KEY' in os.environ:
        result['elasticsearch_aws_secret_access_key'] = os.environ['ELASTICSEARCH_AWS_SECRET_ACCESS_KEY']
    if 'ELASTICSEARCH_AWS_REGION' in os.environ:
        result['elasticsearch_aws_region'] = os.environ['ELASTICSEARCH_AWS_REGION']

    return result


def app():
    """Configure and return the WSGI app."""
    config = pyramid.config.Configurator(settings=settings())
    config.add_static_view(name="static", path="static")
    config.include("pyramid_jinja2")
    config.registry.settings["jinja2.filters"] = {
        "static_path": "pyramid_jinja2.filters:static_path_filter",
        "static_url": "pyramid_jinja2.filters:static_url_filter"
    }
    config.include("bouncer.search")
    config.include("bouncer.views")
    config.include("bouncer.sentry")
    return config.make_wsgi_app()
