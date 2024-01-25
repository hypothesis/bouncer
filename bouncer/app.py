import json
import os

import pyramid.config


def settings():  # pragma: nocover
    """
    Return the app's configuration settings as a dict.

    Settings are read from environment variables and fall back to hardcoded
    defaults if those variables aren't defined.

    """
    via_base_url = os.environ.get("VIA_BASE_URL", "https://via.hypothes.is")
    if via_base_url.endswith("/"):
        via_base_url = via_base_url[:-1]

    debug = "DEBUG" in os.environ

    extension_ids = os.environ.get(
        "CHROME_EXTENSION_ID", "bjfhmglciegochdpefhhlphglcehbmek"
    )
    if extension_ids.strip().startswith("{"):
        extension_ids = json.loads(extension_ids)
        if not extension_ids.get("default"):
            raise Exception('CHROME_EXTENSION_ID map must have a "default" key')
    else:
        extension_ids = {"default": extension_ids}

    result = {
        "chrome_extension_id": extension_ids,
        "debug": debug,
        "elasticsearch_index": os.environ.get("ELASTICSEARCH_INDEX", "hypothesis"),
        "hypothesis_authority": os.environ.get("HYPOTHESIS_AUTHORITY", "localhost"),
        "hypothesis_url": os.environ.get("HYPOTHESIS_URL", "https://hypothes.is"),
        "via_base_url": via_base_url,
    }

    if "ELASTICSEARCH_URL" in os.environ:
        result["elasticsearch_url"] = os.environ["ELASTICSEARCH_URL"]
    return result


def create_app(_=None, **_settings):  # pragma: nocover
    """Configure and return the WSGI app."""
    config = pyramid.config.Configurator(settings=settings())
    config.add_static_view(name="static", path="static")
    config.include("pyramid_jinja2")
    config.registry.settings["jinja2.filters"] = {
        "static_path": "pyramid_jinja2.filters:static_path_filter",
        "static_url": "pyramid_jinja2.filters:static_url_filter",
    }
    config.include("bouncer.search")
    config.include("bouncer.views")
    config.include("h_pyramid_sentry")
    return config.make_wsgi_app()
