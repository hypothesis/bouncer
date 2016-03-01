"""Report exceptions to Sentry/Raven."""
from pyramid import tweens
import raven

from bouncer import __about__


def raven_tween_factory(handler, _):
    """Return a tween that reports uncaught exceptions to Sentry."""
    def raven_tween(request):
        """Report uncaught exceptions to Sentry."""
        try:
            return handler(request)
        except:
            request.raven.captureException()
            raise

    return raven_tween


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

    config.add_tween(
        "bouncer.sentry.raven_tween_factory",
        under=tweens.EXCVIEW)
