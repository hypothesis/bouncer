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

   ./node_modules/karma/bin/karma start --no-single-rin

and open http://localhost:9876/ in your browser.

To run a dev instance on port 8000:

.. code-block:: bash

   export CHROME_EXTENSION_ID=<id_of_your_local_dev_build_of_the_hypothesis_chrome_extension>
   make dev

Other environment variables can be used to change other settings, see
`__init__.py <bouncer/__init__.py>`_.
