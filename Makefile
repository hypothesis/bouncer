.PHONY: help
help:
	@echo "make help              Show this help message"
	@echo "make dev               Run the app in the development server"
	@echo "make lint              Run the code linter(s) and print any warnings"
	@echo "make format            Correctly format the code"
	@echo "make checkformatting   Crash if the code isn't correctly formatted"
	@echo "make test              Run the unit tests"
	@echo "make coverage          Print the unit test coverage report"
	@echo "make sure              Make sure that the formatter, linter, tests, etc all pass"
	@echo "make pip-compile       Compile requirements.in to requirements.txt"
	@echo "make upgrade-package   Upgrade the version of a package in requirements.txt."
	@echo '                       Usage: `make upgrade-package name=some-package`.'
	@echo "make docker            Make the app's Docker image"
	@echo "make run-docker        Run the app's Docker image locally. "
	@echo "                       This command exists for conveniently testing the Docker image "
	@echo "                       locally in production mode. It assumes that h's Elasticsearch "
	@echo "                       service is being run using docker-compose in the 'h_default' "
	@echo "                       network."
	@echo "make clean             Delete development artefacts (cached files, "
	@echo "                       dependencies, etc)"

.PHONY: dev
dev: node_modules/.uptodate python
	@tox -qe dev

.PHONY: lint
lint: backend-lint frontend-lint

.PHONY: backend-lint
backend-lint: python
	@tox -qe lint

.PHONY: frontend-lint
frontend-lint: node_modules/.uptodate
	@./node_modules/.bin/eslint bouncer/scripts

.PHONY: format
format: python
	@tox -qe format

.PHONY: checkformatting
checkformatting: python
	@tox -qe checkformatting

.PHONY: test
test: backend-test frontend-test

.PHONY: backend-test
backend-test: python
	@tox -q

.PHONY: frontend-test
frontend-test: node_modules/.uptodate
	@./node_modules/karma/bin/karma start karma.config.js

.PHONY: coverage
coverage: python
	@tox -qe coverage

.PHONY: sure
sure: checkformatting lint test coverage

.PHONY: pip-compile
pip-compile: python
	@tox -qe pip-compile

.PHONY: upgrade-package
upgrade-package: python
	@tox -qe pip-compile -- --upgrade-package $(name)

.PHONY: docker
docker:
	@git archive --format=tar.gz HEAD | docker build -t hypothesis/bouncer:$(DOCKER_TAG) -

.PHONY: run-docker
run-docker:
	@docker run \
		--net h_default \
		-e "ELASTICSEARCH_URL=http://elasticsearch:9200" \
		-p 8000:8000 \
		hypothesis/bouncer:$(DOCKER_TAG)

.PHONY: clean
clean:
	@find . -type f -name "*.py[co]" -delete
	@find . -type d -name "__pycache__" -delete
	@rm -f node_modules/.uptodate

.PHONY: python
python:
	@./bin/install-python

DOCKER_TAG = dev

node_modules/.uptodate: package.json
	@echo installing javascript dependencies
	@node_modules/.bin/check-dependencies 2>/dev/null || npm install
	@touch $@
