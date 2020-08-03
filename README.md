[![Build Status](https://github.com/hypothesis/bouncer/workflows/Continuous%20integration/badge.svg?branch=master)](https://github.com/hypothesis/bouncer/actions?query=branch%3Amaster)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

Hypothesis Direct-Link Bouncer Service
======================================

Installing bouncer in a development environment
-----------------------------------------------

### You will need

* [Git](https://git-scm.com/)

* [Node](https://nodejs.org/) and npm.
  On Linux you should follow
  [nodejs.org's instructions for installing node](https://nodejs.org/en/download/package-manager/)
  because the version of node in the standard Ubuntu package repositories is
  too old.
  On macOS you should use [Homebrew](https://brew.sh/) to install node.

* [pyenv](https://github.com/pyenv/pyenv)
  Follow the instructions in the pyenv README to install it.
  The Homebrew method works best on macOS.

### Clone the Git repo

    git clone https://github.com/hypothesis/bouncer.git

This will download the code into an `bouncer` directory in your current working
directory. You need to be in the `bouncer` directory from the remainder of the
installation process:

    cd bouncer

### Start the development server

    make dev

The first time you run `make dev` it might take a while to start because it'll
need to install the application dependencies and build the assets.

This will start the server on port 8000 (http://localhost:8000), reload the
application whenever changes are made to the source code, and restart it should
it crash for some reason.

**That's it!** You’ve finished setting up your bouncer development environment. Run
`make help` to see all the commands that're available for running the tests,
linting, code formatting, etc.

Configuration
-------------

You can set various environment variables to configure bouncer:

<dl>
<dt>CHROME_EXTENSION_ID</dt>
<dd>The ID of the Hypothesis Chrome extension that bouncer will communicate with
(default: the ID of the <a href="https://chrome.google.com/webstore/detail/hypothesis-web-pdf-annota/bjfhmglciegochdpefhhlphglcehbmek" rel="nofollow">official Hypothesis Chrome extension</a>)</dd>

<dt>DEBUG</dt>
<dd>If <code>DEBUG</code> is set (to any value) then tracebacks will be printed to the
terminal for any unexpected Python exceptions. If there is no <code>DEBUG</code>
variable set in the environment then unexpected Python exceptions will be
reported to Sentry and a generic error page shown to the user.</dd>

<dt>ELASTICSEARCH_URL</dt>
<dd>The url (host and port) of the Elasticsearch server that bouncer will read
annotations from (default: <a href="http://localhost:9200" rel="nofollow">http://localhost:9200</a>)</dd>

<dt>ELASTICSEARCH_INDEX</dt>
<dd>The name of the Elasticsearch index that bouncer will read annotations
from (default: hypothesis)</dd>

<dt>HYPOTHESIS_AUTHORITY</dt>
<dd>The domain name of the Hypothesis service's first party authority.
This is usually the same as the domain name of the Hypothesis service
(default: localhost).</dd>

<dt>HYPOTHESIS_URL</dt>
<dd>The URL of the Hypothesis front page that requests to bouncer's front page
will be redirected to (default: <a href="https://hypothes.is" rel="nofollow">https://hypothes.is</a>)</dd>

<dt>SENTRY_DSN</dt>
<dd>The DSN (Data Source Name) that bouncer will use to report crashes to
<a href="https://getsentry.com/" rel="nofollow">Sentry</a></dd>

<dt>VIA_BASE_URL</dt>
<dd>The base URL of the Via service that bouncer will redirect users to if they
don't have the Hypothesis Chrome extension installed
(default: <a href="https://via.hypothes.is" rel="nofollow">https://via.hypothes.is</a>)</dd>
</dl>

Route Syntax/API
----------------

### Share Annotations on Page/URL (`/go`)

Go to a specified URL and display annotations there. Optionally filter which
annotations are displayed.

Querystring parameters:

* `url` (required): URL of target page/document
* `group` (optional): group ID. Show annotations within a specified group.
* `q` (optional): Search query. Filter annotations at URL to those that match
  this search query.

### Share an Annotation (`/{id}` or `/{id}/{url}`)

Go to an individual annotation, where `id` is the annotation's unique ID.

Optional `url` path parameter: URL of the annotation's target document.
This is intended to enhance the readability of shared annotation URLs and
is functionally identical to the `/{id}` route.
