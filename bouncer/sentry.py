"""Report exceptions to Sentry/Raven."""
from pyramid import tweens
import raven

from bouncer import __about__


#: The Raven client object that's used to send reports to Sentry.
#: This object is created once per app and re-used across requests.
#:
#: This should be accessed via request.raven rather than directly, because
#: get_raven_client() below adds per-request context to the client.
raven_client = raven.Client(release=__about__.__version__)


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
    """Add per-request context to raven_client and return it."""
    # Add request-specific context to the Raven client.
    raven_client.http_context({
        "url": request.url,
        "method": request.method,
    })

    # Clear the request-specific context at the end of each request so that it
    # isn't carried over to the next request (the same raven_client object is
    # used across requests).
    request.add_finished_callback(
        lambda request: raven_client.context.clear())

    return raven_client


def includeme(config):
    config.add_request_method(
        get_raven_client,
        name="raven",
        reify=True)
    config.add_tween(
        "bouncer.sentry.raven_tween_factory",
        under=tweens.EXCVIEW)
