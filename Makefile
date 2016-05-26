BUILD_ID := $(shell python -c 'f = open("bouncer/__about__.py"); exec(f.read()); print(__version__)')
DOCKER_TAG = dev

deps:
	pip install --upgrade pip
	pip install --upgrade wheel
	pip install -e .[dev]
	npm install

dev:
	PYRAMID_RELOAD_TEMPLATES=1 gunicorn --reload "bouncer:app()"

test:
	py.test --cov=bouncer bouncer
	./node_modules/karma/bin/karma start karma.config.js

.PHONY: dist
dist: dist/bouncer-$(BUILD_ID).tar.gz

dist/bouncer-$(BUILD_ID).tar.gz:
	python setup.py sdist

dist/bouncer-$(BUILD_ID): dist/bouncer-$(BUILD_ID).tar.gz
	tar -C dist -zxf $<

.PHONY: docker
docker: dist/bouncer-$(BUILD_ID)
	docker build -t hypothesis/bouncer:$(DOCKER_TAG) $<

.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -f node_modules/.uptodate bouncer.egg-info/.uptodate
	rm -rf dist
