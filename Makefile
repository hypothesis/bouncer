DOCKER_TAG = dev

deps:
	pip install --upgrade pip
	pip install --upgrade wheel
	pip install --use-wheel -r requirements-dev.txt
	npm install

dev:
	PYRAMID_RELOAD_TEMPLATES=1 gunicorn --reload "bouncer:app()"

.PHONY: test
test:
	@pip install -q tox
	tox
	./node_modules/karma/bin/karma start karma.config.js

.PHONY: docker
docker:
	git archive HEAD | docker build -t hypothesis/bouncer:$(DOCKER_TAG) -

.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -f node_modules/.uptodate
