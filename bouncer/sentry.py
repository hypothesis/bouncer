"""Report exceptions to Sentry/Raven."""
from pyramid import tweens
import raven

from bouncer import __about__


def get_raven_client(request):
    """Return the Raven client for reporting crashes to Sentry."""
    client = request.registry["raven.client"]

    client.http_context({
        "url": request.url,
        "method": request.method,
    })

    request.add_finished_callback(
        lambda request: client.context.clear())

    return client


def includeme(config):
    config.registry["raven.client"] = raven.Client(
        release=__about__.__version__)

    config.add_request_method(
        get_raven_client,
        name="raven",
        reify=True)
