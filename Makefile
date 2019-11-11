.PHONY: help
help:
	@echo "make help              Show this help message"
	@echo "make dev               Run the app in the development server"
	@echo "make lint              Run the code linter(s) and print any warnings"
	@echo "make format            Correctly format the code"
	@echo "make checkformatting   Crash if the code isn't correctly formatted"
	@echo "make test              Run the unit tests"
	@echo "make coverage          Print the unit test coverage report"
	@echo "make docstrings        View all the docstrings locally as HTML"
	@echo "make checkdocstrings   Crash if building the docstrings fails"
	@echo "make pip-compile       Compile requirements.in to requirements.txt"
	@echo "make upgrade-package   Upgrade the version of a package in requirements.txt."
	@echo '                       Usage: `make upgrade-package name=some-package`.'
	@echo "make docker            Make the app's Docker image"
	@echo "make clean             Delete development artefacts (cached files, "
	@echo "                       dependencies, etc)"

.PHONY: dev
dev: node_modules/.uptodate python
	tox -q -e py36-dev

.PHONY: lint
lint: node_modules/.uptodate python
	tox -q -e py36-lint
	./node_modules/.bin/eslint bouncer/scripts

.PHONY: format
format: python
	tox -e py36-format

.PHONY: checkformatting
checkformatting: python
	tox -e py36-checkformatting

.PHONY: test
test: node_modules/.uptodate python
	tox -q -e py36-tests
	./node_modules/karma/bin/karma start karma.config.js

.PHONY: coverage
coverage: python
	tox -q -e py36-coverage

.PHONY: docstrings
docstrings: python
	tox -q -e py36-docstrings

.PHONY: checkdocstrings
checkdocstrings: python
	tox -q -e py36-checkdocstrings

.PHONY: pip-compile
pip-compile: python
	tox -q -e py36-pip-compile

.PHONY: upgrade-package
upgrade-package: python
	@tox -qe py36-pip-compile -- --upgrade-package $(name)

.PHONY: docker
docker:
	git archive --format=tar.gz HEAD | docker build -t hypothesis/bouncer:$(DOCKER_TAG) -

.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -f node_modules/.uptodate

.PHONY: python
python:
	@./bin/install-python

DOCKER_TAG = dev

node_modules/.uptodate: package.json
	@echo installing javascript dependencies
	@node_modules/.bin/check-dependencies 2>/dev/null || npm install
	@touch $@
