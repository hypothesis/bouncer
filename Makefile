.PHONY: default
default: help

.PHONY: help
help:
	@echo "make help              Show this help message"
	@echo "make dev               Run the app in the development server"
	@echo "make lint              Run the code linter(s) and print any warnings"
	@echo "make test              Run the unit tests"
	@echo "make coverage          Print the unit test coverage report"
	@echo "make codecov           Upload the coverage report to codecov.io"
	@echo "make docstrings        View all the docstrings locally as HTML"
	@echo "make checkdocstrings   Crash if building the docstrings fails"
	@echo "make docker            Make the app's Docker image"
	@echo "make clean             Delete development artefacts (cached files, "
	@echo "                       dependencies, etc)"

.PHONY: dev
dev: node_modules/.uptodate
	tox -qe py36-dev

.PHONY: lint
lint: node_modules/.uptodate
	tox -qe py36-lint
	./node_modules/.bin/eslint bouncer/scripts

.PHONY: test
test: node_modules/.uptodate
	tox -qe py36-tests
	./node_modules/karma/bin/karma start karma.config.js

.PHONY: coverage
coverage:
	tox -qe py36-coverage

.PHONY: codecov
codecov:
	tox -qe py36-codecov

.PHONY: docstrings
docstrings:
	tox -qe py36-docstrings

.PHONY: checkdocstrings
checkdocstrings:
	tox -qe py36-checkdocstrings

.PHONY: docker
docker:
	git archive --format=tar.gz HEAD | docker build -t hypothesis/bouncer:$(DOCKER_TAG) -

.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -f node_modules/.uptodate

DOCKER_TAG = dev

node_modules/.uptodate: package.json
	@echo installing javascript dependencies
	@node_modules/.bin/check-dependencies 2>/dev/null || npm install
	@touch $@
