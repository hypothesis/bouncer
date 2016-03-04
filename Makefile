deps:
	pip install --upgrade pip
	pip install --upgrade wheel
	pip install -e .[dev]
	npm install

dev:
	PYRAMID_RELOAD_TEMPLATES=1 gunicorn --reload "bouncer:app()"

docker:
	docker build -t hypothesis/bouncer:dev .

test:
	py.test --cov=bouncer bouncer
	./node_modules/karma/bin/karma start karma.config.js
