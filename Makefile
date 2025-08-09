.PHONY: test run fmt lint hooks

## run tests
test:
	pytest -q

## sample agent run
run:
	python -m master_ai agent-run --goal 'fetch: url=https://httpbin.org/robots.txt; dest=dl/robots.txt'

## format code with black
fmt:
	black .

## lint with ruff
lint:
	ruff check .

## install/refresh pre-commit hooks
hooks:
	pre-commit install
	pre-commit autoupdate
