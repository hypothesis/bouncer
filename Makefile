# Run the development web server.
.PHONY: dev
dev: .pydeps node_modules/.uptodate
	PYRAMID_RELOAD_TEMPLATES=1 gunicorn --reload "bouncer.app:app()"

# Run all the tests (Python and JavaScript).
.PHONY: test
test: node_modules/.uptodate pytests
	./node_modules/.bin/eslint bouncer/scripts
	./node_modules/karma/bin/karma start karma.config.js

# Run the tests and then print out a coverage report.
# `make coverage` always re-runs the tests.
.PHONY: coverage
coverage: test tox
	tox -e coverage

# Send a coverage report to Codecov based on the existing .coverage file.
# The Python tests will be run to generate the .coverage file if it doesn't
# exist, but if the .coverage file is out of date (code has changed) the tests
# won't be re-run.
.PHONY: codecov
codecov: .coverage tox
	tox -e codecov

# Build the docker image.
.PHONY: docker
docker:
	git archive HEAD | docker build -t hypothesis/bouncer:dev -

.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	-rm -f .pydeps node_modules/.uptodate .coverage

.pydeps: requirements-dev.txt requirements.txt
	pip install --upgrade pip
	pip install --upgrade wheel
	pip install --use-wheel -r requirements-dev.txt
	touch .pydeps

node_modules/.uptodate: package.json
	npm install
	touch node_modules/.uptodate

.coverage:
	$(MAKE) tox
	tox

.PHONY: pytests
pytests: tox
	tox

.PHONY: tox
tox:
	pip install -q tox
