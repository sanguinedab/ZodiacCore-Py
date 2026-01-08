.PHONY: lint test test-parallel test-serial clean

test: test-parallel test-serial

lint:
	uvx --with tox-uv tox -e lint

test-parallel:
	uvx --with tox-uv tox -p auto -- -m "not serial"

test-serial:
	uvx --with tox-uv tox -- -m serial

clean:
	rm -rf .tox
	rm -rf .pytest_cache
	rm -rf dist
	find . -type d -name "__pycache__" -exec rm -rf {} +
