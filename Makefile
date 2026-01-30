.PHONY: lint test test-parallel test-serial clean docs-serve docs-build

test: test-parallel test-serial

lint:
	uvx --with tox-uv tox -e lint

docs-serve:
	uv run --group docs mkdocs serve

docs-build:
	uv run --group docs mkdocs build

test-parallel:
	uvx --with tox-uv tox -p auto -- -m "not serial"

test-serial:
	uvx --with tox-uv tox -- -m serial

clean:
	rm -rf .tox
	rm -rf .pytest_cache
	rm -rf dist
	rm -rf site
	find . -type d -name "__pycache__" -exec rm -rf {} +
