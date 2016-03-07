.. image:: https://travis-ci.org/hypothesis/bouncer.svg?branch=master
    :target: https://travis-ci.org/hypothesis/bouncer
    :alt: Build Status
.. image:: https://codecov.io/github/hypothesis/bouncer/coverage.svg?branch=master
    :target: https://codecov.io/github/hypothesis/bouncer?branch=master
    :alt: Test Coverage
.. image:: https://landscape.io/github/hypothesis/bouncer/master/landscape.svg?style=flat
   :target: https://landscape.io/github/hypothesis/bouncer/master
   :alt: Code Health


Hypothesis Direct-Link Bouncer Service
======================================

Configuration
-------------

You can set various environment variables to configure bouncer before running
it in production or development:

CHROME_EXTENSION_ID
  The ID of the Hypothesis Chrome extension that bouncer will communicate with
  (default: the ID of the `official Hypothesis Chrome extension <https://chrome.google.com/webstore/detail/hypothesis-web-pdf-annota/bjfhmglciegochdpefhhlphglcehbmek>`_)

ELASTICSEARCH_HOST
  The hostname of the Elasticsearch server that bouncer will read annotations
  from (default: localhost)

ELASTICSEARCH_INDEX
  The name of the Elasticsearch index that bouncer will read annotations
  from (default: annotator)

ELASTICSEARCH_PORT
  The port of the Elasticsearch server that bouncer will read annotations
  from (default: 9200)

HYPOTHESIS_URL
  The URL of the Hypothesis front page that requests to bouncer's front page
  will be redirected to (default: https://hypothes.is)

SENTRY_DSN
    The DSN (Data Source Name) that bouncer's server-side code will use to
    report crashes to `Sentry <https://getsentry.com/>`_

SENTRY_JAVASCRIPT_DSN
    The DSN (Data Source Name) that bouncer's client-side JavaScript code will
    use to report crashes to `Sentry <https://getsentry.com/>`_.
    This is different to SENTRY_DSN above - it doesn't include the secret key
    part of the DSN.

STATSD_HOST
  The host of the statsd server that bouncer will report stats to
  (default: localhost)

STATSD_PORT
  The port of the statsd server that bouncer will report stats to
  (default: 8125)

STATSD_PREFIX
  A string prefix that bouncer will prepend to all metric paths reported to
  statsd (default: none).
  We recommend ``export STATSD_PREFIX=bouncer`` so that all bouncer's metrics
  will start with ``bouncer``.

VIA_BASE_URL
  The base URL of the Via service that bouncer will redirect users to if they
  don't have the Hypothesis Chrome extension installed
  (default: https://via.hypothes.is)


Production Deployment
---------------------

Requirements:

* `Docker <https://www.docker.com/>`_
* `Git <https://git-scm.com/>`_
* `Make <https://www.gnu.org/software/make/>`_

Build the ``hypothesis/bouncer`` Docker image and run bouncer in a Docker
container:

.. code-block:: bash

   git clone https://github.com/hypothesis/bouncer.git
   cd bouncer
   make docker
   docker run --net host -p 8000:8000 hypothesis/bouncer


Development
-----------

Requirements:

* `Git <https://git-scm.com/>`_
* `Make <https://www.gnu.org/software/make/>`_
* `Python 3.5 <https://www.python.org/>`_
* `Virtualenv <https://virtualenv.readthedocs.org/>`_

Install:

.. code-block:: bash

   git clone https://github.com/hypothesis/bouncer.git
   cd bouncer
   virtualenv -p python3.5 .
   . bin/activate
   make deps

Run the tests:

.. code-block:: bash

   make test

To debug the JavaScript tests in a browser, run:

.. code-block:: bash

   ./node_modules/karma/bin/karma start --no-single-run

and open http://localhost:9876/ in your browser.

To run a dev instance on port 8000:

.. code-block:: bash

   export CHROME_EXTENSION_ID=<id_of_your_local_dev_build_of_the_hypothesis_chrome_extension>
   make dev
