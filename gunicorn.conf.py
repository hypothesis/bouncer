import os

statsd_host = "{host}:{port}".format(
    host=os.environ.get("STATSD_HOST", "localhost"),
    port=os.environ.get("STATSD_PORT", "8125"))

statsd_prefix = os.environ.get("STATSD_PREFIX", "")
